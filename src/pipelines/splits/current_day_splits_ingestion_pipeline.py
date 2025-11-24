"""Pipeline for ingesting current day stock splits from bulk data sources."""

from __future__ import annotations

import logging
from datetime import date
from typing import TypedDict

from src.data_sources.base.splits_data_source import SplitsDataSource
from src.models.split import Split
from src.repos.equities.splits.splits_repository import SplitsRepository
from src.repos.equities.tickers.ticker_history_repository import (
    TickerHistoryRepository,
)


class CurrentDaySplitsIngestionResult(TypedDict):
    """Result of current day splits ingestion process."""

    target_date: str
    total_splits_fetched: int
    successful: int
    failed: int
    splits_inserted: int
    errors: list[str]


class CurrentDaySplitsIngestionPipeline:
    """Pipeline for ingesting current day stock splits from bulk sources.

    This pipeline:
    1. Fetches bulk splits data for a specific date (defaults to today)
    2. Looks up ticker_history_id for each split by symbol
    3. Groups splits by ticker_history_id
    4. Bulk upserts splits to the database
    """

    def __init__(
        self,
        splits_data_source: SplitsDataSource,
        splits_repo: SplitsRepository | None = None,
        ticker_history_repo: TickerHistoryRepository | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize current day splits ingestion pipeline.

        Args:
            splits_data_source: Data source for splits data (required)
            splits_repo: Repository for splits operations
            ticker_history_repo: Repository for ticker history operations
            logger: Logger instance for pipeline operations
        """
        self.splits_data_source = splits_data_source
        self.splits_repo = splits_repo or SplitsRepository()
        self.ticker_history_repo = ticker_history_repo or TickerHistoryRepository()
        self.logger = logger or logging.getLogger(__name__)

    def run(self, target_date: date | None = None) -> CurrentDaySplitsIngestionResult:
        """Run the current day splits ingestion process.

        Args:
            target_date: Date to fetch splits for (defaults to today)

        Returns:
            CurrentDaySplitsIngestionResult with counts of processed records
        """
        # Default to today if no date provided
        if target_date is None:
            target_date = date.today()

        self.logger.info(f"Starting current day splits ingestion for {target_date}")

        # Initialize result
        result: CurrentDaySplitsIngestionResult = {
            "target_date": target_date.isoformat(),
            "total_splits_fetched": 0,
            "successful": 0,
            "failed": 0,
            "splits_inserted": 0,
            "errors": [],
        }

        try:
            # Step 1: Fetch bulk splits data from data source
            self.logger.info(f"Fetching bulk splits data for {target_date}")
            splits = self.splits_data_source.get_current_date_splits(target_date)
            result["total_splits_fetched"] = len(splits)
            self.logger.info(f"Retrieved {len(splits)} splits from API")

            if not splits:
                self.logger.info("No splits found for this date")
                return result

            # Step 2: Group splits by ticker_history_id
            splits_by_ticker_history = self._resolve_ticker_histories(
                splits, target_date, result
            )

            # Step 3: Bulk upsert splits for each ticker_history_id
            total_inserted = self._bulk_upsert_splits(splits_by_ticker_history, result)
            result["splits_inserted"] = total_inserted

            self.logger.info(
                f"Current day splits ingestion completed. "
                f"Fetched: {result['total_splits_fetched']}, "
                f"Successful: {result['successful']}, "
                f"Failed: {result['failed']}, "
                f"Inserted: {result['splits_inserted']}"
            )

            return result

        except Exception as e:
            error_msg = f"Fatal error in current day splits ingestion: {e}"
            self.logger.exception(error_msg)
            result["errors"].append(error_msg)
            return result

    def _resolve_ticker_histories(
        self,
        splits: list[Split],
        target_date: date,
        result: CurrentDaySplitsIngestionResult,
    ) -> dict[int, list[Split]]:
        """Resolve ticker_history_id for each split and group by ticker_history_id.

        Args:
            splits: List of splits with symbols but no ticker_history_id
            target_date: Date to check validity against
            result: Result dict to update with errors

        Returns:
            Dictionary mapping ticker_history_id to list of splits
        """
        splits_by_ticker_history: dict[int, list[Split]] = {}

        for split in splits:
            try:
                # Look up ticker_history records for this symbol
                ticker_histories = self.ticker_history_repo.get_ticker_history_by_symbol(
                    split.symbol
                )

                if not ticker_histories:
                    error_msg = f"No ticker_history found for symbol: {split.symbol}"
                    self.logger.warning(error_msg)
                    result["errors"].append(error_msg)
                    result["failed"] += 1
                    continue

                # Find the ticker_history valid for the target date
                valid_ticker_history = None
                for th in ticker_histories:
                    # Check if target_date falls within valid_from and valid_to
                    if th.valid_from <= target_date and (
                        th.valid_to is None or th.valid_to >= target_date
                    ):
                        valid_ticker_history = th
                        break

                if not valid_ticker_history:
                    error_msg = (
                        f"No valid ticker_history found for symbol {split.symbol} "
                        f"on date {target_date}"
                    )
                    self.logger.warning(error_msg)
                    result["errors"].append(error_msg)
                    result["failed"] += 1
                    continue

                # Set ticker_history_id on the split
                split.ticker_history_id = valid_ticker_history.id

                # Group by ticker_history_id
                if valid_ticker_history.id not in splits_by_ticker_history:
                    splits_by_ticker_history[valid_ticker_history.id] = []
                splits_by_ticker_history[valid_ticker_history.id].append(split)

                result["successful"] += 1

            except Exception as e:
                error_msg = f"Error resolving ticker_history for {split.symbol}: {e}"
                self.logger.error(error_msg)
                result["errors"].append(error_msg)
                result["failed"] += 1

        self.logger.info(
            f"Resolved {len(splits_by_ticker_history)} ticker histories with splits"
        )
        return splits_by_ticker_history

    def _bulk_upsert_splits(
        self,
        splits_by_ticker_history: dict[int, list[Split]],
        result: CurrentDaySplitsIngestionResult,
    ) -> int:
        """Bulk upsert splits for each ticker_history_id.

        Args:
            splits_by_ticker_history: Dictionary mapping ticker_history_id to splits
            result: Result dict to update with errors

        Returns:
            Total number of splits inserted
        """
        total_inserted = 0

        for ticker_history_id, splits_list in splits_by_ticker_history.items():
            try:
                upsert_result = self.splits_repo.bulk_upsert_splits(
                    ticker_history_id=ticker_history_id,
                    splits_data=splits_list,
                )
                inserted = upsert_result.get("inserted", 0)
                total_inserted += inserted

                self.logger.debug(
                    f"Upserted {inserted} splits for ticker_history_id={ticker_history_id}"
                )

            except Exception as e:
                error_msg = (
                    f"Error bulk upserting splits for ticker_history_id "
                    f"{ticker_history_id}: {e}"
                )
                self.logger.error(error_msg)
                result["errors"].append(error_msg)

        self.logger.info(f"Total splits inserted: {total_inserted}")
        return total_inserted
