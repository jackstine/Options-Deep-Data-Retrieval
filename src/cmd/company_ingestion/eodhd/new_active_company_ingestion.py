#!/usr/bin/env python3
"""Ingest new active companies from EODHD.

This command fetches active company symbols from EODHD and ingests only the
new companies (those not already in the database) into the following tables:
- companies
- ticker
- ticker_history

The pipeline automatically identifies which companies are new by checking
ticker symbols against the database and only inserts companies that don't
already exist.

Usage:
    python -m src.cmd.company_ingestion.eodhd.new_active_company_ingestion

    or

    python src/cmd/company_ingestion/eodhd/new_active_company_ingestion.py

Output:
    - Inserts new companies into the company table
    - Creates ticker records for new companies
    - Creates ticker_history records with valid_from=today and valid_to=NULL
    - Updates market_cap for existing companies

Processing Details:
    - Fetches all active companies from EODHD
    - No validation filters applied (processes all active companies)
    - Deduplicates by ticker symbol (keeps first occurrence)
    - Skips companies without ticker symbols
    - Only new companies are inserted
"""

from __future__ import annotations

import logging
import sys

from src.data_sources.eodhd.symbols import EodhdSymbolsSource
from src.pipelines.companies.new_company_pipeline import CompanyPipeline


def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("new_active_company_ingestion.log"),
        ],
    )


def main() -> int:
    """Main function to run new active company ingestion.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting new active company ingestion...")

        # Initialize data source
        logger.info("Initializing EODHD data source...")
        company_source = EodhdSymbolsSource()

        # Check availability
        if not company_source.is_available():
            logger.error("EODHD company data source is not available")
            print("ERROR: EODHD API key not configured. Please set EODHD_API_KEY environment variable.")
            return 1

        # Initialize pipeline
        logger.info("Initializing company pipeline...")
        pipeline = CompanyPipeline()

        # Run ingestion
        logger.info("Running new active company ingestion...")
        print("\nIngesting new active companies from EODHD...")
        print("This may take a while depending on the number of symbols...\n")

        results = pipeline.run_ingestion([company_source])

        # Print results
        print("\n" + "=" * 70)
        print("NEW ACTIVE COMPANY INGESTION COMPLETED")
        print("=" * 70)
        print("\nCompanies:")
        print(f"  New companies inserted:   {results['inserted']:>6,}")
        print(f"  Existing updated:         {results['updated']:>6,}")
        print(f"  Skipped:                  {results['skipped']:>6,}")
        print(f"  Errors:                   {results['errors']:>6,}")

        print("\nTickers:")
        print(f"  New tickers created:      {results['tickers_inserted']:>6,}")

        print("\nTicker Histories:")
        print(f"  New histories created:    {results['ticker_histories_inserted']:>6,}")

        print("\n" + "=" * 70)

        # Summary
        total_processed = results["inserted"] + results["updated"] + results["skipped"] + results["errors"]
        print(f"\nTotal companies processed: {total_processed:,}")

        if results["errors"] == 0:
            print("Status: All companies processed successfully!")
        elif results["errors"] < total_processed * 0.1:
            print("Status: Ingestion completed with minor errors")
        else:
            print("Status: Ingestion completed with significant errors")

        print("=" * 70 + "\n")

        return 0 if results["errors"] < total_processed * 0.5 else 1

    except KeyboardInterrupt:
        logger.warning("Ingestion interrupted by user")
        print("\n\nIngestion interrupted by user (Ctrl+C)")
        return 1

    except Exception as e:
        logger.exception("Fatal error during ingestion")
        print(f"\nFATAL ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
