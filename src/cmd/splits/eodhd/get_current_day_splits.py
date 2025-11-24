#!/usr/bin/env python3
"""Ingest current day stock splits from EODHD bulk endpoint.

This script fetches stock splits that occurred on the current day from EODHD's
bulk splits endpoint and inserts them into the database:

1. Fetches bulk splits data for today from EODHD
2. Resolves ticker_history_id for each split by symbol and date validity
3. Groups splits by ticker_history_id
4. Bulk upserts splits to the database

Usage:
    python -m src.cmd.splits.eodhd.get_current_day_splits

Examples:
    # Run current day splits ingestion
    python -m src.cmd.splits.eodhd.get_current_day_splits
"""

import logging
import sys

from src.data_sources.eodhd.splits import EodhdSplitsDataSource
from src.pipelines.splits.current_day_splits_ingestion_pipeline import (
    CurrentDaySplitsIngestionPipeline,
)


def setup_logging() -> None:
    """Configure logging for the ingestion process."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> int:
    """Run the current day splits ingestion pipeline.

    Returns:
        0 for success, 1 for failure
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("=" * 80)
        logger.info("CURRENT DAY SPLITS INGESTION - EODHD")
        logger.info("=" * 80)

        # Initialize data source
        logger.info("Initializing EODHD splits data source...")
        splits_data_source = EodhdSplitsDataSource()

        # Check data source availability
        if not splits_data_source.is_available():
            logger.error("EODHD splits data source is not available")
            logger.error("Please ensure EODHD_API_KEY is set in environment")
            return 1

        logger.info(f"Data source: {splits_data_source.name}")

        # Initialize pipeline
        logger.info("Initializing current day splits ingestion pipeline...")
        pipeline = CurrentDaySplitsIngestionPipeline(
            splits_data_source=splits_data_source,
            logger=logger,
        )

        # Run ingestion (defaults to today)
        logger.info("Starting current day splits ingestion process...")
        logger.info("-" * 80)

        result = pipeline.run()

        # Display results
        logger.info("=" * 80)
        logger.info("CURRENT DAY SPLITS INGESTION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Target Date: {result['target_date']}")
        logger.info(f"Splits Fetched: {result['total_splits_fetched']}")
        logger.info(f"Successful: {result['successful']}")
        logger.info(f"Failed: {result['failed']}")
        logger.info(f"Splits Inserted: {result['splits_inserted']}")
        logger.info(f"Errors: {len(result['errors'])}")

        if result["errors"]:
            logger.info("\nFirst 10 errors:")
            for error in result["errors"][:10]:
                logger.error(f"  - {error}")
            if len(result["errors"]) > 10:
                logger.info(f"  ... and {len(result['errors']) - 10} more errors")

        logger.info("=" * 80)

        # Return success if no failures
        return 0 if result["failed"] == 0 else 1

    except KeyboardInterrupt:
        logger.warning("\nIngestion interrupted by user")
        return 1

    except Exception as e:
        logger.exception(f"Fatal error during ingestion: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
