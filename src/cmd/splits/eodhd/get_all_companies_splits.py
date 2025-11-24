#!/usr/bin/env python3
"""Ingest historical stock splits for all companies from EODHD.

This script:
1. Fetches all ticker_history records from the database
2. Retrieves historical splits data for each ticker from EODHD
3. Inserts splits into the database
4. Processes in batches of 1000 for efficient memory usage

Usage:
    python -m src.cmd.splits.eodhd.get_all_companies_splits

Examples:
    # Ingest all historical splits
    python -m src.cmd.splits.eodhd.get_all_companies_splits
"""

import argparse
import logging
import sys

from src.data_sources.eodhd.splits import EodhdSplitsDataSource
from src.pipelines.splits.all_stocks_splits_ingestion_pipeline import (
    AllStocksSplitsIngestionPipeline,
)


def setup_logging() -> None:
    """Configure logging for the ingestion process."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Ingest historical stock splits for all companies from EODHD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    return parser.parse_args()


def main() -> int:
    """Run the stock splits ingestion pipeline.

    Returns:
        0 for success, 1 for failure
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        parse_args()

        logger.info("=" * 80)
        logger.info("EODHD Stock Splits Ingestion - All Companies")
        logger.info("=" * 80)

        # Initialize data source
        logger.info("Initializing EODHD splits data source...")
        splits_data_source = EodhdSplitsDataSource()

        if not splits_data_source.is_available():
            logger.error("EODHD splits data source is not available")
            logger.error("Please check that EODHD_API_KEY is set in environment")
            return 1

        logger.info(f"Data source: {splits_data_source.name}")

        # Initialize pipeline
        logger.info("Initializing splits ingestion pipeline...")
        pipeline = AllStocksSplitsIngestionPipeline(
            splits_data_source=splits_data_source,
            logger=logger,
        )

        # Run pipeline
        logger.info("Starting splits ingestion for all ticker histories...")
        logger.info("-" * 80)

        result = pipeline.run()

        # Display results
        logger.info("=" * 80)
        logger.info("INGESTION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total ticker histories: {result['total_ticker_histories']}")
        logger.info(f"Processed: {result['processed']}")
        logger.info(f"Successful: {result['successful']}")
        logger.info(f"Failed: {result['failed']}")
        logger.info(f"Total splits inserted: {result['total_splits_inserted']}")
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
