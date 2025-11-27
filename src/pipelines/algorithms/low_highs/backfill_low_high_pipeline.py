"""Pipeline for backfilling low/high patterns from historical data."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import TypedDict

from src.algorithms.low_highs.models.high import High
from src.algorithms.low_highs.pattern_calculator import PatternCalculator
from src.algorithms.low_highs.processor import process_low_high_patterns
from src.models.date_price import DatePrice
from src.repos.algorithms.low_highs.highs_repository import HighsRepository
from src.repos.algorithms.low_highs.reversals_repository import ReversalsRepository
from src.repos.equities.pricing.historical_eod_pricing_repository import (
    HistoricalEodPricingRepository,
)
from src.repos.equities.tickers.ticker_repository import TickerRepository


class BackfillResult(TypedDict):
    """Result of backfill operation."""

    ticker_symbol: str
    ticker_history_id: int
    from_date: str
    to_date: str
    total_patterns_generated: int
    active_highs_inserted: int
    reversals_inserted: int
    errors: int


class BackfillLowHighPipeline:
    """Pipeline for backfilling low/high patterns from historical pricing data.

    This pipeline:
    1. Fetches all historical pricing data for a ticker
    2. For each threshold (15%, 20%, 25%, etc.)
    3. Initializes first pattern from first price
    4. Processes all prices chronologically using core algorithm
    5. Bulk inserts resulting highs and reversals into database

    This is a one-time operation for generating historical pattern data.
    After backfill, use DailyLowHighPipeline for incremental updates.
    """

    def __init__(
        self,
        highs_repo: HighsRepository | None = None,
        reversals_repo: ReversalsRepository | None = None,
        pricing_repo: HistoricalEodPricingRepository | None = None,
        ticker_repo: TickerRepository | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize backfill pipeline.

        Args:
            highs_repo: Repository for highs operations
            reversals_repo: Repository for reversals operations
            pricing_repo: Repository for pricing operations
            ticker_repo: Repository for ticker operations
            logger: Logger instance
        """
        self.highs_repo = highs_repo or HighsRepository()
        self.reversals_repo = reversals_repo or ReversalsRepository()
        self.pricing_repo = pricing_repo or HistoricalEodPricingRepository()
        self.ticker_repo = ticker_repo or TickerRepository()
        self.logger = logger or logging.getLogger(__name__)
        self.pattern_calc = PatternCalculator()

    def run(
        self,
        ticker_symbol: str,
        from_date: date | None = None,
        to_date: date | None = None,
        thresholds: list[Decimal] | None = None,
    ) -> BackfillResult:
        """Backfill low/high patterns for a ticker.

        Args:
            ticker_symbol: Ticker symbol to backfill
            from_date: Start date (default: all available history)
            to_date: End date (default: most recent date)
            thresholds: List of thresholds to process (default: standard thresholds)

        Returns:
            BackfillResult with processing statistics
        """
        self.logger.info(f"Starting backfill for {ticker_symbol}")

        result: BackfillResult = {
            "ticker_symbol": ticker_symbol,
            "ticker_history_id": 0,
            "from_date": "",
            "to_date": "",
            "total_patterns_generated": 0,
            "active_highs_inserted": 0,
            "reversals_inserted": 0,
            "errors": 0,
        }

        try:
            # Step 1: Get ticker from database
            ticker = self.ticker_repo.get_ticker_by_symbol(ticker_symbol)
            if not ticker or ticker.ticker_history_id is None:
                self.logger.error(f"Ticker not found: {ticker_symbol}")
                result["errors"] = 1
                return result

            result["ticker_history_id"] = ticker.ticker_history_id

            # Step 2: Get all historical pricing data
            self.logger.info(
                f"Fetching historical pricing for {ticker_symbol} "
                f"(ticker_history_id: {ticker.ticker_history_id})"
            )
            # TODO looks like we need to use the split adjusted pricing
            pricing_data = self.pricing_repo.get_pricing_by_ticker(
                ticker.ticker_history_id, from_date, to_date
            )

            if not pricing_data:
                self.logger.warning(f"No pricing data found for {ticker_symbol}")
                return result

            # Sort chronologically
            pricing_data = sorted(pricing_data, key=lambda p: p.date)
            result["from_date"] = str(pricing_data[0].date)
            result["to_date"] = str(pricing_data[-1].date)

            # Convert HistoricalEndOfDayPricing to DatePrice
            date_prices: list[DatePrice] = []
            for eod_price in pricing_data:
                if eod_price.close is not None:
                    date_prices.append(
                        DatePrice(date=eod_price.date, price=eod_price.close)
                    )

            if not date_prices:
                self.logger.warning(
                    f"No valid closing prices found for {ticker_symbol}"
                )
                return result

            self.logger.info(
                f"Processing {len(date_prices)} days of pricing data "
                f"from {result['from_date']} to {result['to_date']}"
            )

            # Step 3: Use default thresholds if not provided
            if thresholds is None:
                thresholds = self.pattern_calc.get_default_thresholds()

            # Step 4: Process each threshold
            all_active_highs = []
            all_reversals = []

            for threshold in thresholds:
                self.logger.info(
                    f"Processing threshold {float(threshold):.0%} for {ticker_symbol}"
                )

                try:
                    # Initialize first pattern from first price
                    first_price = date_prices[0]
                    initial_pattern = High(
                        ticker_history_id=ticker.ticker_history_id,
                        threshold=threshold,
                        low_start_price=first_price.price,
                        low_start_date=first_price.date,
                        last_updated=first_price.date,
                    )

                    # Process all prices for this threshold
                    processed = process_low_high_patterns(
                        current_patterns=[initial_pattern],
                        new_prices=date_prices,
                        threshold=threshold,
                    )

                    # Collect results
                    all_active_highs.extend(processed.active_highs)
                    all_reversals.extend(processed.completed_reversals)

                    self.logger.info(
                        f"Threshold {float(threshold):.0%}: "
                        f"{len(processed.active_highs)} active patterns, "
                        f"{len(processed.completed_reversals)} completed reversals"
                    )

                except Exception as e:
                    self.logger.error(
                        f"Error processing threshold {float(threshold):.0%}: {e}"
                    )
                    result["errors"] += 1

            # Step 5: Bulk insert into database
            if all_active_highs:
                self.logger.info(f"Inserting {len(all_active_highs)} active high patterns")
                upsert_result = self.highs_repo.bulk_upsert_highs(all_active_highs)
                result["active_highs_inserted"] = (
                    upsert_result["inserted"] + upsert_result["updated"]
                )

            if all_reversals:
                self.logger.info(f"Inserting {len(all_reversals)} completed reversals")
                reversals_inserted = self.reversals_repo.bulk_insert_reversals(
                    all_reversals
                )
                result["reversals_inserted"] = reversals_inserted

            result["total_patterns_generated"] = len(all_active_highs) + len(
                all_reversals
            )

            self.logger.info(f"Backfill complete for {ticker_symbol}: {result}")

        except Exception as e:
            self.logger.error(f"Error in backfill pipeline for {ticker_symbol}: {e}")
            result["errors"] += 1

        return result

    def run_bulk_backfill(
        self,
        ticker_symbols: list[str] | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        thresholds: list[Decimal] | None = None,
    ) -> list[BackfillResult]:
        """Backfill patterns for multiple tickers.

        Args:
            ticker_symbols: List of ticker symbols (default: all active tickers)
            from_date: Start date
            to_date: End date
            thresholds: List of thresholds to process

        Returns:
            List of BackfillResult for each ticker
        """
        # Get tickers
        if ticker_symbols is None:
            self.logger.info("Fetching all active tickers")
            all_tickers = self.ticker_repo.get_all_tickers()
            ticker_symbols = [t.symbol for t in all_tickers]

        self.logger.info(f"Starting bulk backfill for {len(ticker_symbols)} tickers")

        results = []
        for i, symbol in enumerate(ticker_symbols, 1):
            self.logger.info(f"Processing ticker {i}/{len(ticker_symbols)}: {symbol}")
            result = self.run(symbol, from_date, to_date, thresholds)
            results.append(result)

        # Summary
        total_patterns = sum(r["total_patterns_generated"] for r in results)
        total_errors = sum(r["errors"] for r in results)
        self.logger.info(
            f"Bulk backfill complete: {total_patterns} patterns generated, "
            f"{total_errors} errors across {len(results)} tickers"
        )

        return results
