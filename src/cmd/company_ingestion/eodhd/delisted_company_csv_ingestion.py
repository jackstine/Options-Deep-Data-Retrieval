#!/usr/bin/env python3
"""Ingest delisted companies with historical EOD pricing data from EODHD CSV files.

This command reads delisted Common Stock symbols from EODHD CSV files and ingests them
into the database along with their historical EOD pricing data. It calculates
validation metrics and marks companies as valid/invalid based on:
- Exchange (NASDAQ, NYSE, NYSE_MKT, NYSE ARCA, AMEX are automatically valid)
- Data coverage (> 90% required for non-major exchanges)
- Max price (<= $1000 required for non-major exchanges)

Usage:
    python -m src.cmd.company_ingestion.eodhd.delisted_company_csv_ingestion

    or

    python src/cmd/company_ingestion/eodhd/delisted_company_csv_ingestion.py

Output:
    - Ingests companies into the company table
    - Creates ticker_history records with valid_to dates
    - Creates ticker_history_stats with coverage and price metrics
    - Inserts historical EOD pricing data
    - Generates failure report at /reports/failed_delisted_symbols_csv.md

Processing Details:
    - Only processes Common Stock type symbols
    - Reads from local CSV files (no API calls)
    - Continues on individual failures
    - Marks companies with errors as is_valid_data=False

Environment Variables:
    - OPTIONS_DEEP_TEST_LIMITS: Optional integer to limit number of symbols processed
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from src.config.configuration import CONFIG
from src.data_sources.eodhd.csv_eod_data import EodhdCsvHistoricalDataSource
from src.data_sources.eodhd.csv_symbols import EodhdCsvSymbolsSource
from src.pipelines.eod.delisted_pipeline import DelistedCompanyPipeline


def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("delisted_csv_ingestion.log"),
        ],
    )


def write_failure_report(failed_symbols: list[dict], report_path: Path) -> None:
    """Write failure report to markdown file.

    Args:
        failed_symbols: List of failed company dictionaries
        report_path: Path to the failure report file
    """
    report_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Failed Delisted Symbol CSV Ingestion Report\n\n")
        f.write(f"**Generated:** {timestamp}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Total Failed:** {len(failed_symbols)}\n\n")
        f.write("---\n\n")
        f.write("## Failed Symbols\n\n")

        if not failed_symbols:
            f.write("*No failures - all symbols processed successfully!*\n")
        else:
            for symbol_info in failed_symbols:
                f.write(f"### {symbol_info.get('code', 'N/A')} - {symbol_info.get('name', 'Unknown')}\n\n")
                f.write(f"- **Exchange:** {symbol_info.get('exchange', 'N/A')}\n")
                f.write(f"- **Error:** {symbol_info.get('error', 'Unknown error')}\n")
                f.write("- **Full Details:**\n\n")
                f.write("```json\n")
                f.write(json.dumps(symbol_info, indent=2, default=str))
                f.write("\n```\n\n")
                f.write("---\n\n")


def main() -> int:
    """Main function to run delisted company CSV ingestion.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting delisted company CSV ingestion...")

        # Check for test limits
        test_limit = CONFIG.get_test_limits()
        if test_limit:
            logger.info(f"Test limits active: processing max {test_limit} symbols")
            print(f"\n⚠️  Test mode active: Processing limited to {test_limit} symbols")
            print("Set OPTIONS_DEEP_TEST_LIMITS=0 or unset to process all symbols\n")

        # Initialize CSV data sources
        logger.info("Initializing CSV data sources...")
        company_source = EodhdCsvSymbolsSource()
        historical_source = EodhdCsvHistoricalDataSource()

        # Check availability
        if not company_source.is_available():
            logger.error("EODHD CSV symbols file is not available")
            print("ERROR: Delisted symbols CSV file not found.")
            print(f"Expected location: {company_source.csv_file_path}")
            return 1

        if not historical_source.is_available():
            logger.error("EODHD CSV historical data directory is not available")
            print("ERROR: EOD data directory not found.")
            print(f"Expected location: {historical_source.eod_data_dir}")
            return 1

        # Initialize pipeline
        logger.info("Initializing pipeline...")
        pipeline = DelistedCompanyPipeline()

        # Run ingestion
        logger.info("Running delisted company CSV ingestion...")
        print("\nIngesting delisted companies from EODHD CSV files...")
        print("This may take a while depending on the number of symbols...\n")

        results = pipeline.ingest_delisted_companies(company_source, historical_source)

        # Print results
        print("\n" + "=" * 70)
        print("DELISTED COMPANY CSV INGESTION COMPLETED")
        print("=" * 70)
        print("\nCompanies:")
        print(f"  Total processed:      {results['total_companies']:>6,}")
        print(f"  Inserted:             {results['companies_inserted']:>6,}")
        print(f"  Updated:              {results['companies_updated']:>6,}")
        print(f"  Failed:               {results['failed_companies']:>6,}")

        print("\nTicker Histories:")
        print(f"  Created:              {results['ticker_histories_created']:>6,}")

        print("\nTicker History Stats:")
        print(f"  Upserted:             {results['stats_upserted']:>6,}")

        print("\nHistorical EOD Pricing:")
        print(f"  Records inserted:     {results['pricing_records_inserted']:>6,}")
        print(f"  Records updated:      {results['pricing_records_updated']:>6,}")

        print("\n" + "=" * 70)

        # Print failed symbols
        if results["failed_companies"] > 0:
            print(f"\nFailed Symbols ({results['failed_companies']}):")
            print("-" * 70)
            for failed in results["failed_symbols"][:10]:  # Show first 10
                print(f"  {failed.get('code', 'N/A'):8} - {failed.get('error', 'Unknown error')}")

            if len(results["failed_symbols"]) > 10:
                print(f"  ... and {len(results['failed_symbols']) - 10} more")

            # Write failure report
            project_root = Path(__file__).parent.parent.parent.parent.parent
            report_path = project_root / "reports" / "failed_delisted_symbols_csv.md"

            logger.info(f"Writing failure report to {report_path}")
            write_failure_report(results["failed_symbols"], report_path)
            print(f"\nFailure report written to: {report_path}")

        # Summary
        print("\n" + "=" * 70)
        success_rate = (
            ((results["total_companies"] - results["failed_companies"]) / results["total_companies"] * 100)
            if results["total_companies"] > 0
            else 0
        )
        print(f"Success Rate: {success_rate:.1f}%")

        if results["failed_companies"] == 0:
            print("Status: All companies processed successfully!")
        elif results["failed_companies"] < results["total_companies"] * 0.1:
            print("Status: Ingestion completed with minor failures")
        else:
            print("Status: Ingestion completed with significant failures")

        print("=" * 70 + "\n")

        return 0 if results["failed_companies"] < results["total_companies"] * 0.5 else 1

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
