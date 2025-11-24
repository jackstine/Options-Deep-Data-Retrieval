"""Pipeline for ingesting historical stock splits for all ticker histories."""

from __future__ import annotations

import logging
from typing import TypedDict

from src.data_sources.base.splits_data_source import SplitsDataSource
from src.repos.equities.splits.splits_repository import SplitsRepository
from src.repos.equities.tickers.ticker_history_repository import (
    TickerHistoryRepository,
)


class AllStocksSplitsIngestionResult(TypedDict):
    """Result of all stocks splits ingestion process."""

    total_ticker_histories: int
    processed: int
    successful: int
    failed: int
    total_splits_inserted: int
    errors: list[str]


class AllStocksSplitsIngestionPipeline:
    """Pipeline for ingesting historical splits for all ticker histories.

    This pipeline processes all ticker_history records in batches, fetching
    splits data from the data source and inserting them into the database.
    """

    BATCH_SIZE = 1000

    def __init__(
        self,
        splits_data_source: SplitsDataSource | None = None,
        splits_repo: SplitsRepository | None = None,
        ticker_history_repo: TickerHistoryRepository | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize pipeline with data sources and repositories.

        Args:
            splits_data_source: Source for splits data (required)
            splits_repo: Repository for splits operations
            ticker_history_repo: Repository for ticker history operations
            logger: Logger instance for pipeline operations
        """
        self.splits_data_source = splits_data_source
        self.splits_repo = splits_repo or SplitsRepository()
        self.ticker_history_repo = ticker_history_repo or TickerHistoryRepository()
        self.logger = logger or logging.getLogger(__name__)

    def run(self) -> AllStocksSplitsIngestionResult:
        """Run the splits ingestion pipeline for all ticker histories.

        Processes all ticker_history records in batches, fetching and inserting
        splits data for each one.

        Returns:
            AllStocksSplitsIngestionResult with statistics about the ingestion

        Raises:
            ValueError: If splits_data_source is not provided
        """
        if not self.splits_data_source:
            raise ValueError("splits_data_source is required")

        self.logger.info("Starting all stocks splits ingestion pipeline")

        # Initialize result
        result: AllStocksSplitsIngestionResult = {
            "total_ticker_histories": 0,
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "total_splits_inserted": 0,
            "errors": [],
        }

        # Get total count of ticker histories
        total_count = self.ticker_history_repo.count()
        result["total_ticker_histories"] = total_count
        self.logger.info(f"Found {total_count} ticker histories to process")

        if total_count == 0:
            self.logger.warning("No ticker histories found in database")
            return result

        # Process in batches
        offset = 0
        while offset < total_count:
            batch_num = (offset // self.BATCH_SIZE) + 1
            self.logger.info(
                f"Processing batch {batch_num} (offset={offset}, size={self.BATCH_SIZE})"
            )

            # Fetch batch of ticker histories
            ticker_histories = self.ticker_history_repo.get_limit_offset(
                limit=self.BATCH_SIZE,
                offset=offset,
            )

            if not ticker_histories:
                self.logger.info("No more ticker histories to process")
                break

            # Process each ticker history in the batch
            for ticker_history in ticker_histories:
                result["processed"] += 1

                try:
                    # Log progress every 100 records
                    if result["processed"] % 100 == 0:
                        self.logger.info(
                            f"Progress: {result['processed']}/{total_count} "
                            f"({result['processed'] * 100 // total_count}%) - "
                            f"Successful: {result['successful']}, "
                            f"Failed: {result['failed']}, "
                            f"Splits inserted: {result['total_splits_inserted']}"
                        )

                    # Fetch splits for this ticker history
                    splits = self.splits_data_source.get_splits(ticker_history.symbol)

                    if not splits:
                        self.logger.debug(
                            f"No splits found for {ticker_history.symbol} "
                            f"(ticker_history_id={ticker_history.id})"
                        )
                        result["successful"] += 1
                        continue

                    # Bulk upsert splits
                    upsert_result = self.splits_repo.bulk_upsert_splits(
                        ticker_history_id=ticker_history.id,  # type: ignore[arg-type]
                        splits_data=splits,
                    )

                    splits_inserted = upsert_result.get("inserted", 0)
                    result["total_splits_inserted"] += splits_inserted
                    result["successful"] += 1

                    self.logger.debug(
                        f"Inserted {splits_inserted} splits for {ticker_history.symbol} "
                        f"(ticker_history_id={ticker_history.id})"
                    )

                except Exception as e:
                    error_msg = (
                        f"Failed to process ticker_history_id={ticker_history.id} "
                        f"({ticker_history.symbol}): {e}"
                    )
                    self.logger.error(error_msg)
                    result["errors"].append(error_msg)
                    result["failed"] += 1

            # Move to next batch
            offset += self.BATCH_SIZE

        # Log final summary
        self.logger.info(
            f"Splits ingestion pipeline completed. "
            f"Processed: {result['processed']}/{result['total_ticker_histories']}, "
            f"Successful: {result['successful']}, "
            f"Failed: {result['failed']}, "
            f"Total splits inserted: {result['total_splits_inserted']}, "
            f"Errors: {len(result['errors'])}"
        )

        return result
