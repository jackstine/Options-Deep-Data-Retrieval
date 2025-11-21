"""Pipeline for daily EOD pricing ingestion from bulk data sources."""

from __future__ import annotations

import logging
from datetime import date
from typing import TypedDict

from src.data_sources.base.bulk_eod_data_source import BulkEodDataSource
from src.models.historical_eod_pricing import HistoricalEndOfDayPricing
from src.models.misplaced_eod_pricing import MisplacedEndOfDayPricing
from src.models.missing_eod_pricing import MissingEndOfDayPricing
from src.repos.equities.pricing.historical_eod_pricing_repository import (
    HistoricalEodPricingRepository,
)
from src.repos.equities.pricing.misplaced_eod_pricing_repository import (
    MisplacedEodPricingRepository,
)
from src.repos.equities.pricing.missing_eod_pricing_repository import (
    MissingEodPricingRepository,
)
from src.repos.equities.tickers.ticker_repository import TickerRepository


class DailyEodIngestionResult(TypedDict):
    """Result of daily EOD ingestion process."""

    total_symbols_from_api: int
    tickers_in_db: int
    historical_pricing_inserted: int
    misplaced_pricing_inserted: int
    missing_dates_tracked: int
    errors: int


class DailyEodIngestionPipeline:
    """Pipeline for ingesting daily EOD pricing data from bulk sources.

    This pipeline:
    1. Fetches bulk EOD data for an entire exchange
    2. Partitions symbols into matched (in DB) and unmatched (not in DB)
    3. Inserts matched pricing to historical_eod_pricing table
    4. Inserts unmatched pricing to misplaced_eod_pricing table
    5. Tracks missing dates for tickers with no data in missing_eod_pricing table
    """

    def __init__(
        self,
        bulk_eod_source: BulkEodDataSource,
        ticker_repo: TickerRepository | None = None,
        historical_pricing_repo: HistoricalEodPricingRepository | None = None,
        misplaced_pricing_repo: MisplacedEodPricingRepository | None = None,
        missing_pricing_repo: MissingEodPricingRepository | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize daily EOD ingestion pipeline.

        Args:
            bulk_eod_source: Data source for bulk EOD data
            ticker_repo: Repository for ticker operations
            historical_pricing_repo: Repository for historical pricing operations
            misplaced_pricing_repo: Repository for misplaced pricing operations
            missing_pricing_repo: Repository for missing pricing operations
            logger: Logger instance for pipeline operations
        """
        self.bulk_eod_source = bulk_eod_source
        self.ticker_repo = ticker_repo or TickerRepository()
        self.historical_pricing_repo = (
            historical_pricing_repo or HistoricalEodPricingRepository()
        )
        self.misplaced_pricing_repo = (
            misplaced_pricing_repo or MisplacedEodPricingRepository()
        )
        self.missing_pricing_repo = (
            missing_pricing_repo or MissingEodPricingRepository()
        )
        self.logger = logger or logging.getLogger(__name__)

    def run(
        self,
        exchange: str = "US",
        filter_common_stock: bool = True,
        test_limit: int | None = None,
    ) -> DailyEodIngestionResult:
        """Run the daily EOD ingestion process.

        Args:
            exchange: Exchange code to fetch data for (default: "US")
            filter_common_stock: Filter for Common Stock only (default: True)
            test_limit: Optional limit on number of symbols to process (for testing)

        Returns:
            DailyEodIngestionResult with counts of processed records
        """
        error_count = 0

        try:
            # Step 1: Fetch bulk EOD data from data source
            self.logger.info(f"Fetching bulk EOD data for exchange: {exchange}")
            eod_data = self.bulk_eod_source.get_bulk_latest_eod(
                exchange=exchange,
                filter_common_stock=filter_common_stock,
            )
            self.logger.info(f"Retrieved {len(eod_data)} symbols from API")

            # Apply test limit if provided
            if test_limit is not None and test_limit > 0:
                original_count = len(eod_data)
                # Limit to first N symbols in dictionary
                limited_symbols = list(eod_data.keys())[:test_limit]
                eod_data = {symbol: eod_data[symbol] for symbol in limited_symbols}
                self.logger.info(
                    f"TEST LIMIT APPLIED: Processing only {len(eod_data)} "
                    f"symbols (limited from {original_count})"
                )

            # Step 2: Get all ticker symbols from database
            self.logger.info("Fetching ticker symbols from database")
            db_symbols = self.ticker_repo.get_active_ticker_symbols()
            self.logger.info(f"Found {len(db_symbols)} tickers in database")

            # Step 3: Partition symbols into matched and unmatched
            api_symbols = set(eod_data.keys())
            matched_symbols = api_symbols & db_symbols
            unmatched_symbols = api_symbols - db_symbols

            self.logger.info(
                f"Partitioned symbols: {len(matched_symbols)} matched, "
                f"{len(unmatched_symbols)} unmatched"
            )

            # Step 4: Process matched symbols (insert to historical_eod_pricing)
            historical_count = self._process_matched_symbols(
                matched_symbols, eod_data
            )

            # Step 5: Process unmatched symbols (insert to misplaced_eod_pricing)
            misplaced_count = self._process_unmatched_symbols(
                unmatched_symbols, eod_data
            )

            # Step 6: Track missing dates (tickers in DB with no EOD data)
            missing_count = self._track_missing_dates(db_symbols, api_symbols)

            return DailyEodIngestionResult(
                total_symbols_from_api=len(eod_data),
                tickers_in_db=len(db_symbols),
                historical_pricing_inserted=historical_count,
                misplaced_pricing_inserted=misplaced_count,
                missing_dates_tracked=missing_count,
                errors=error_count,
            )

        except Exception as e:
            self.logger.exception(f"Fatal error in daily EOD ingestion: {e}")
            error_count += 1
            return DailyEodIngestionResult(
                total_symbols_from_api=0,
                tickers_in_db=0,
                historical_pricing_inserted=0,
                misplaced_pricing_inserted=0,
                missing_dates_tracked=0,
                errors=error_count,
            )

    def _process_matched_symbols(
        self,
        matched_symbols: set[str],
        eod_data: dict[str, MisplacedEndOfDayPricing],
    ) -> int:
        """Process symbols that exist in the database.

        Converts MisplacedEndOfDayPricing to HistoricalEndOfDayPricing with
        ticker_history_id and bulk inserts to historical_eod_pricing table.

        Args:
            matched_symbols: Set of symbols that exist in DB
            eod_data: Dictionary of all EOD data from API

        Returns:
            Number of records inserted
        """
        if not matched_symbols:
            self.logger.info("No matched symbols to process")
            return 0

        self.logger.info(f"Processing {len(matched_symbols)} matched symbols")

        # Group pricing by ticker_history_id for bulk operations
        pricing_by_ticker_history: dict[int, list[HistoricalEndOfDayPricing]] = {}
        error_count = 0

        for symbol in matched_symbols:
            try:
                # Get ticker to obtain ticker_history_id
                ticker = self.ticker_repo.get_ticker_by_symbol(symbol)
                if not ticker or ticker.ticker_history_id is None:
                    self.logger.warning(
                        f"Skipping {symbol}: ticker not found or missing ticker_history_id"
                    )
                    error_count += 1
                    continue

                # Get pricing data
                misplaced_pricing = eod_data[symbol]

                # Convert to HistoricalEndOfDayPricing
                historical_pricing = HistoricalEndOfDayPricing(
                    date=misplaced_pricing.date,
                    open=misplaced_pricing.open,
                    high=misplaced_pricing.high,
                    low=misplaced_pricing.low,
                    close=misplaced_pricing.close,
                    adjusted_close=misplaced_pricing.adjusted_close,
                    volume=misplaced_pricing.volume,
                    source=misplaced_pricing.source,
                )

                # Group by ticker_history_id
                if ticker.ticker_history_id not in pricing_by_ticker_history:
                    pricing_by_ticker_history[ticker.ticker_history_id] = []
                pricing_by_ticker_history[ticker.ticker_history_id].append(
                    historical_pricing
                )

            except Exception as e:
                self.logger.error(f"Error processing matched symbol {symbol}: {e}")
                error_count += 1
                continue

        # Bulk upsert to historical_eod_pricing table
        total_inserted = 0
        for ticker_history_id, pricing_list in pricing_by_ticker_history.items():
            try:
                result = self.historical_pricing_repo.bulk_upsert_pricing(
                    ticker_history_id, pricing_list
                )
                total_inserted += result["inserted"]
            except Exception as e:
                self.logger.error(
                    f"Error bulk upserting for ticker_history_id {ticker_history_id}: {e}"
                )
                error_count += 1

        self.logger.info(
            f"Inserted {total_inserted} historical pricing records ({error_count} errors)"
        )
        return total_inserted

    def _process_unmatched_symbols(
        self,
        unmatched_symbols: set[str],
        eod_data: dict[str, MisplacedEndOfDayPricing],
    ) -> int:
        """Process symbols that do not exist in the database.

        Bulk inserts to misplaced_eod_pricing table for later processing.

        Args:
            unmatched_symbols: Set of symbols that don't exist in DB
            eod_data: Dictionary of all EOD data from API

        Returns:
            Number of records inserted
        """
        if not unmatched_symbols:
            self.logger.info("No unmatched symbols to process")
            return 0

        self.logger.info(f"Processing {len(unmatched_symbols)} unmatched symbols")

        # Collect pricing data for unmatched symbols
        misplaced_pricing_list = [eod_data[symbol] for symbol in unmatched_symbols]

        try:
            # Bulk upsert to misplaced_eod_pricing table
            result = self.misplaced_pricing_repo.bulk_upsert_pricing(
                misplaced_pricing_list
            )
            inserted = result["inserted"]
            self.logger.info(f"Inserted {inserted} misplaced pricing records")
            return inserted

        except Exception as e:
            self.logger.error(f"Error bulk upserting misplaced pricing: {e}")
            return 0

    def _track_missing_dates(
        self, db_symbols: set[str], api_symbols: set[str]
    ) -> int:
        """Track missing dates for tickers with no EOD data from API.

        Creates MissingEndOfDayPricing records for tickers that exist in the
        database but did not have data in the API response.

        Args:
            db_symbols: Set of symbols in database
            api_symbols: Set of symbols from API

        Returns:
            Number of missing date records inserted
        """
        # Find symbols in DB but not in API response
        missing_symbols = db_symbols - api_symbols

        if not missing_symbols:
            self.logger.info("No missing symbols to track")
            return 0

        self.logger.info(f"Tracking {len(missing_symbols)} missing symbols")

        # Get current date for missing records
        today = date.today()
        missing_records: list[MissingEndOfDayPricing] = []
        error_count = 0

        for symbol in missing_symbols:
            try:
                # Get ticker to obtain company_id and ticker_history_id
                ticker = self.ticker_repo.get_ticker_by_symbol(symbol)
                if not ticker or ticker.company_id is None or ticker.ticker_history_id is None:
                    self.logger.warning(
                        f"Skipping {symbol}: ticker not found or missing IDs"
                    )
                    error_count += 1
                    continue

                # Create missing date record
                missing_record = MissingEndOfDayPricing(
                    company_id=ticker.company_id,
                    ticker_history_id=ticker.ticker_history_id,
                    date=today,
                )
                missing_records.append(missing_record)

            except Exception as e:
                self.logger.error(f"Error creating missing record for {symbol}: {e}")
                error_count += 1
                continue

        # Bulk insert to missing_eod_pricing table
        if missing_records:
            try:
                result = self.missing_pricing_repo.bulk_insert_missing_dates(
                    missing_records
                )
                inserted = result["inserted"]
                self.logger.info(
                    f"Inserted {inserted} missing date records ({error_count} errors)"
                )
                return inserted
            except Exception as e:
                self.logger.error(f"Error bulk inserting missing dates: {e}")
                return 0
        else:
            self.logger.info("No missing date records to insert")
            return 0
