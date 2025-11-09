"""EOD pricing data ingestion pipeline."""

from __future__ import annotations

import logging
from datetime import date
from typing import TypedDict

from src.data_sources.eodhd.eod_data import EodhdDataSource
from src.data_sources.models.historical_eod_pricing import (
    HistoricalEndOfDayPricing as HistoricalEodPricingDataModel,
)
from src.repos.equities.pricing.historical_eod_pricing_repository import (
    HistoricalEodPricingRepository,
)
from src.repos.equities.tickers.ticker_repository import TickerRepository


class TickerPricingResult(TypedDict):
    """Result of ingesting pricing data for a single ticker."""

    ticker_id: int
    ticker_symbol: str
    upserted: int
    errors: int
    from_date: str | None
    to_date: str | None


class BulkPricingResult(TypedDict):
    """Result of ingesting pricing data for multiple tickers."""

    total_tickers: int
    successful_tickers: int
    failed_tickers: int
    total_upserted: int
    total_errors: int


class EodPricingPipeline:
    """EOD pricing data ingestion pipeline with bulk operations."""

    def __init__(
        self,
        pricing_repo: HistoricalEodPricingRepository | None = None,
        ticker_repo: TickerRepository | None = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize the pipeline with repositories and logger.

        Args:
            pricing_repo: Repository for historical EOD pricing data
            ticker_repo: Repository for ticker data
            logger: Logger instance
        """
        self.pricing_repo = pricing_repo or HistoricalEodPricingRepository()
        self.ticker_repo = ticker_repo or TickerRepository()
        self.logger = logger or logging.getLogger(__name__)

    def ingest_pricing_for_ticker(
        self,
        ticker_symbol: str,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> TickerPricingResult:
        """Ingest EOD pricing data for a single ticker.

        Args:
            ticker_symbol: Ticker symbol (e.g., "AAPL")
            from_date: Start date for pricing data (None = all available)
            to_date: End date for pricing data (None = up to present)

        Returns:
            TickerPricingResult with ingestion details
        """
        results: TickerPricingResult = {
            "ticker_id": 0,
            "ticker_symbol": ticker_symbol,
            "upserted": 0,
            "errors": 0,
            "from_date": None,
            "to_date": None,
        }

        try:
            # 1. Get ticker from database
            self.logger.info(f"Looking up ticker: {ticker_symbol}")
            ticker = self.ticker_repo.get_ticker_by_symbol(ticker_symbol)

            if not ticker or ticker.id is None:
                self.logger.error(f"Ticker not found in database: {ticker_symbol}")
                results["errors"] = 1
                return results

            results["ticker_id"] = ticker.id

            # 2. Fetch pricing data from EODHD
            self.logger.info(
                f"Fetching pricing data for {ticker_symbol} from EODHD..."
            )
            data_source = EodhdDataSource()

            if not data_source.is_available():
                self.logger.error("EODHD data source is not available")
                results["errors"] = 1
                return results

            pricing_data = data_source.get_eod_data(
                ticker_symbol, from_date, to_date
            )

            if not pricing_data:
                self.logger.warning(f"No pricing data found for {ticker_symbol}")
                return results

            self.logger.info(
                f"Retrieved {len(pricing_data)} pricing records for {ticker_symbol}"
            )

            # Track date range
            if pricing_data:
                dates = [p.date for p in pricing_data]
                results["from_date"] = str(min(dates))
                results["to_date"] = str(max(dates))

            # 3. Upsert pricing data to database
            self.logger.info(f"Upserting {len(pricing_data)} pricing records...")
            upsert_results = self.pricing_repo.bulk_upsert_pricing(
                ticker.id, pricing_data
            )

            results["upserted"] = upsert_results["inserted"] + upsert_results["updated"]

            self.logger.info(
                f"Successfully ingested {results['upserted']} pricing records for {ticker_symbol}"
            )

        except Exception as e:
            self.logger.error(f"Error ingesting pricing for {ticker_symbol}: {e}")
            results["errors"] = 1

        return results

    def ingest_pricing_for_multiple_tickers(
        self,
        ticker_symbols: list[str],
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> BulkPricingResult:
        """Ingest EOD pricing data for multiple tickers.

        Args:
            ticker_symbols: List of ticker symbols
            from_date: Start date for pricing data
            to_date: End date for pricing data

        Returns:
            BulkPricingResult with aggregate results
        """
        aggregate_results: BulkPricingResult = {
            "total_tickers": len(ticker_symbols),
            "successful_tickers": 0,
            "failed_tickers": 0,
            "total_upserted": 0,
            "total_errors": 0,
        }

        self.logger.info(
            f"Starting bulk ingestion for {len(ticker_symbols)} tickers..."
        )

        for ticker_symbol in ticker_symbols:
            try:
                self.logger.info(
                    f"Processing ticker {ticker_symbol} ({ticker_symbols.index(ticker_symbol) + 1}/{len(ticker_symbols)})..."
                )

                results = self.ingest_pricing_for_ticker(
                    ticker_symbol, from_date, to_date
                )

                if results["errors"] == 0:
                    aggregate_results["successful_tickers"] += 1
                    aggregate_results["total_upserted"] += results["upserted"]
                else:
                    aggregate_results["failed_tickers"] += 1
                    aggregate_results["total_errors"] += 1

            except Exception as e:
                self.logger.error(f"Unexpected error processing {ticker_symbol}: {e}")
                aggregate_results["failed_tickers"] += 1
                aggregate_results["total_errors"] += 1

        self.logger.info(
            f"Bulk ingestion complete. Successful: {aggregate_results['successful_tickers']}, "
            f"Failed: {aggregate_results['failed_tickers']}, "
            f"Total upserted: {aggregate_results['total_upserted']}"
        )

        return aggregate_results

    def update_latest_pricing_for_ticker(
        self, ticker_symbol: str, days_back: int = 30
    ) -> TickerPricingResult:
        """Update pricing data for a ticker for the most recent period.

        Useful for incremental updates rather than full historical loads.

        Args:
            ticker_symbol: Ticker symbol
            days_back: Number of days to look back from today

        Returns:
            TickerPricingResult with update details
        """
        from datetime import timedelta

        to_date = date.today()
        from_date = to_date - timedelta(days=days_back)

        self.logger.info(
            f"Updating latest {days_back} days of pricing for {ticker_symbol}"
        )

        return self.ingest_pricing_for_ticker(ticker_symbol, from_date, to_date)

    def backfill_pricing_for_ticker(
        self, ticker_symbol: str, target_date: date
    ) -> TickerPricingResult:
        """Backfill pricing data from a target date to the latest available date in DB.

        Args:
            ticker_symbol: Ticker symbol
            target_date: Date to start backfilling from

        Returns:
            TickerPricingResult with backfill details
        """
        results: TickerPricingResult = {
            "ticker_id": 0,
            "ticker_symbol": ticker_symbol,
            "upserted": 0,
            "errors": 0,
            "from_date": None,
            "to_date": None,
        }

        try:
            # Get ticker
            ticker = self.ticker_repo.get_ticker_by_symbol(ticker_symbol)
            if not ticker or ticker.id is None:
                self.logger.error(f"Ticker not found: {ticker_symbol}")
                results["errors"] = 1
                return results

            # Get latest pricing date from database
            latest_pricing = self.pricing_repo.get_latest_pricing(ticker.id)

            if latest_pricing:
                to_date = latest_pricing.date
                self.logger.info(
                    f"Backfilling from {target_date} to existing latest date {to_date}"
                )
            else:
                to_date = date.today()
                self.logger.info(
                    f"No existing pricing found. Backfilling from {target_date} to {to_date}"
                )

            # Ingest pricing data
            return self.ingest_pricing_for_ticker(ticker_symbol, target_date, to_date)

        except Exception as e:
            self.logger.error(f"Error backfilling pricing for {ticker_symbol}: {e}")
            results["errors"] = 1

        return results
