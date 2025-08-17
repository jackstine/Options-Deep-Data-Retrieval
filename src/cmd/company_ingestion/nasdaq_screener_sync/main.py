#!/usr/bin/env python3
"""NASDAQ Screener Company Ingestion

Ingests company data from NASDAQ screener files using the company pipeline.

Usage:
    python -m src.cmd.company_ingestion.nasdaq_screener_sync.main [screener_dir]
"""

from __future__ import annotations

import logging
from pathlib import Path
import sys

from src.data_sources.nasdaq.screener import NasdaqScreenerSource
from src.pipelines.companies.simple_pipeline import CompanyPipeline


def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def main() -> int:
    """Ingest NASDAQ screener company data."""
    # Use default screener directory or command line argument
    screener_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    # Verify screener directory exists if provided
    if screener_dir and not Path(screener_dir).exists():
        print(f"Error: Screener directory '{screener_dir}' does not exist")
        return 1

    setup_logging()

    try:
        # Create source and pipeline
        if screener_dir is None:
            print("Error: No screener directory provided")
            return 1
        source = NasdaqScreenerSource(screener_dir)
        pipeline = CompanyPipeline()

        print(f"Starting company ingestion from {source.name}")
        if screener_dir:
            print(f"Source directory: {screener_dir}")

        # Run ingestion
        results = pipeline.run_ingestion([source])

        # Display results
        print("\n" + "=" * 50)
        print("INGESTION COMPLETED")
        print("=" * 50)
        print(f"  Companies inserted: {results['inserted']:,}")
        print(f"  Companies updated: {results['updated']:,}")
        print(f"  Companies skipped: {results['skipped']:,}")
        print(f"  Tickers inserted: {results.get('tickers_inserted', 0):,}")
        print(
            f"  Ticker histories inserted: {results.get('ticker_histories_inserted', 0):,}"
        )
        print(f"  Errors: {results['errors']:,}")
        print("-" * 50)
        total_processed = results["inserted"] + results["updated"] + results["skipped"]
        print(f"  Total companies processed: {total_processed:,}")

        if results["errors"] > 0:
            print(f"\n⚠️  {results['errors']} errors occurred during ingestion")
            print("Check the logs for details")
            return 1
        else:
            print("\n✅ Ingestion successful!")
            return 0

    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
