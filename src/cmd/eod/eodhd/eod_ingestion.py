#!/usr/bin/env python3
"""Daily EOD ingestion from EODHD bulk endpoint.

This script fetches the latest end-of-day pricing data for all US Common Stock
symbols from EODHD's bulk endpoint and distributes the data to appropriate tables:

1. Fetches bulk EOD data for all US Common Stock symbols from EODHD
2. For symbols that exist in the database:
   - Inserts pricing data into historical_eod_pricing table
3. For symbols that don't exist in the database:
   - Inserts pricing data into misplaced_eod_pricing table for later processing
4. For tickers in the database with no EOD data from the API:
   - Tracks missing dates in missing_eod_pricing table for backfilling

Usage:
    python -m src.cmd.eod.eodhd.eod_ingestion

Examples:
    # Run daily EOD ingestion
    python -m src.cmd.eod.eodhd.eod_ingestion
"""

import logging
import sys

from src.data_sources.eodhd.daily_bulk_eod_data import EodhdDailyBulkEodData
from src.pipelines.eod.current_day_eod_pricings import DailyEodIngestionPipeline


def setup_logging() -> None:
    """Configure logging for the ingestion process."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> int:
    """Run the daily EOD ingestion pipeline.

    Returns:
        0 for success, 1 for failure
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("=" * 80)
        logger.info("DAILY EOD INGESTION - EODHD")
        logger.info("=" * 80)

        # Initialize data source
        logger.info("Initializing EODHD bulk data source...")
        bulk_source = EodhdDailyBulkEodData()

        # Check data source availability
        if not bulk_source.is_available():
            logger.error("EODHD bulk data source is not available")
            logger.error("Please ensure EODHD_API_KEY is set in environment")
            return 1

        # Initialize pipeline
        logger.info("Initializing daily EOD ingestion pipeline...")
        pipeline = DailyEodIngestionPipeline(
            bulk_eod_source=bulk_source,
        )

        # Run ingestion
        logger.info("Starting daily EOD ingestion process...")
        result = pipeline.run(
            exchange="US", filter_common_stock=True, test_limit=None
        )

        # Display results
        print("\n" + "=" * 80)
        print("DAILY EOD INGESTION SUMMARY")
        print("=" * 80)
        print(f"API Symbols Retrieved: {result['total_symbols_from_api']:,}")
        print(f"Database Tickers: {result['tickers_in_db']:,}")
        print("\nPRICING INSERTED:")
        print(f"  ✓ Historical Pricing: {result['historical_pricing_inserted']:,} records")
        print(f"  ✓ Misplaced Pricing: {result['misplaced_pricing_inserted']:,} records")
        print("\nMISSING DATA TRACKED:")
        print(f"  ✓ Missing Dates: {result['missing_dates_tracked']:,} records")

        if result['errors'] > 0:
            print(f"\n✗ Errors: {result['errors']}")
        else:
            print("\n✓ No errors")

        print("=" * 80)

        logger.info("Daily EOD ingestion completed successfully")
        return 0

    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        return 1
    except Exception as e:
        logger.exception(f"Fatal error during daily EOD ingestion: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
