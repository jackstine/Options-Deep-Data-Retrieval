#!/usr/bin/env python3
"""Ingest active company listings from EODHD with EOD data validation.

This script:
1. Fetches active companies from EODHD (filtered for Common Stock)
2. Retrieves EOD pricing data for each company
3. Calculates statistics and validates data quality
4. Inserts valid companies into the database
5. Writes failed companies to files and generates a report

Usage:
    python -m src.cmd.company_ingestion.eodhd.active_newcompany_ingestion
    python -m src.cmd.company_ingestion.eodhd.active_newcompany_ingestion --from-date 2024-01-01

Examples:
    # Ingest with default 1 year of data
    python -m src.cmd.company_ingestion.eodhd.active_newcompany_ingestion

    # Ingest with custom start date
    python -m src.cmd.company_ingestion.eodhd.active_newcompany_ingestion --from-date 2023-01-01
"""

import argparse
import logging
import sys
from datetime import date, timedelta

from src.data_sources.eodhd.eod_data import EodhdDataSource
from src.data_sources.eodhd.symbols import EodhdSymbolsSource
from src.pipelines.eod.active_new_listing_pipeline import ActiveNewListingPipeline


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
        description="Ingest active companies from EODHD with EOD data validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--from-date",
        type=str,
        help="Start date for EOD data in YYYY-MM-DD format (default: 1 year ago)",
        default=None,
    )

    return parser.parse_args()


def main() -> int:
    """Run the active company ingestion pipeline.

    Returns:
        0 for success, 1 for failure
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        args = parse_args()

        # Parse from_date if provided
        from_date = None
        if args.from_date:
            try:
                from_date = date.fromisoformat(args.from_date)
                logger.info(f"Using custom from_date: {from_date}")
            except ValueError:
                logger.error(f"Invalid date format: {args.from_date}")
                return 1
        else:
            from_date = date.today() - timedelta(days=365)
            logger.info(f"Using default from_date: {from_date} (1 year ago)")

        logger.info("=" * 80)
        logger.info("EODHD Active Company Ingestion")
        logger.info("=" * 80)

        # Initialize data sources
        logger.info("Initializing EODHD data sources...")
        company_source = EodhdSymbolsSource()
        historical_source = EodhdDataSource()

        # Check data source availability
        if not company_source.is_available():
            logger.error("Company data source is not available")
            return 1

        if not historical_source.is_available():
            logger.error("Historical data source is not available")
            return 1

        # Initialize pipeline
        logger.info("Initializing ingestion pipeline...")
        pipeline = ActiveNewListingPipeline(
            company_source=company_source,
            historical_source=historical_source,
        )

        # Run ingestion
        logger.info("Starting ingestion process...")
        result = pipeline.run_ingestion(from_date=from_date)

        # Display results
        logger.info("=" * 80)
        logger.info("INGESTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total companies retrieved: {result['total_companies']}")
        logger.info(f"Common stock companies: {result['common_stock_count']}")
        logger.info(f"Companies processed: {result['processed']}")
        logger.info("")
        logger.info(f"✓ Valid companies: {result['valid_companies']}")
        logger.info(f"✗ Invalid companies: {result['invalid_companies']}")
        logger.info("")
        logger.info(f"Companies inserted/updated: {result['companies_inserted']}")
        logger.info(f"Tickers inserted: {result['tickers_inserted']}")
        logger.info(f"Ticker histories inserted: {result['ticker_histories_inserted']}")
        logger.info(f"Pricing records inserted: {result['pricing_records_inserted']}")
        logger.info("")

        if result["failed_symbols"]:
            logger.info(f"Failed symbols ({len(result['failed_symbols'])}):")
            for symbol in result["failed_symbols"][:10]:  # Show first 10
                logger.info(f"  - {symbol}")
            if len(result["failed_symbols"]) > 10:
                logger.info(f"  ... and {len(result['failed_symbols']) - 10} more")
            logger.info("")
            logger.info("See reports/failed_active_eod_report.md for details")

        if result["errors"]:
            logger.warning(f"Errors encountered ({len(result['errors'])}):")
            for error in result["errors"][:5]:  # Show first 5
                logger.warning(f"  - {error}")
            if len(result["errors"]) > 5:
                logger.warning(f"  ... and {len(result['errors']) - 5} more")

        logger.info("=" * 80)

        if result["errors"]:
            logger.warning("Ingestion completed with errors")
            return 1

        logger.info("Ingestion completed successfully")
        return 0

    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        return 1
    except Exception as e:
        logger.exception(f"Fatal error during ingestion: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
