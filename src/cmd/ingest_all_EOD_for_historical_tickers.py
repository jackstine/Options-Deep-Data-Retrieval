#!/usr/bin/env python3
"""Ingest All EOD Historical Pricing Data

Fetches and ingests complete historical end-of-day pricing data for all ticker
symbols found in the ticker_history table (includes active and delisted tickers).

Usage:
    python -m src.cmd.ingest_all_EOD_for_historical_tickers

    or

    python src/cmd/ingest_all_EOD_for_historical_tickers.py
"""

from __future__ import annotations

import logging
import sys

from src.pipelines.eod_pricing_pipeline import EodPricingPipeline
from src.repos.equities.tickers.ticker_history_repository import TickerHistoryRepository


def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def main() -> int:
    """Ingest EOD pricing data for all historical tickers."""
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Initialize repositories and pipeline
        ticker_history_repo = TickerHistoryRepository()
        pipeline = EodPricingPipeline()

        # Step 1: Get all ticker history records
        print("\n" + "=" * 70)
        print("EOD HISTORICAL PRICING DATA INGESTION")
        print("=" * 70)
        print("\nFetching all ticker symbols from ticker_history table...")

        all_ticker_histories = ticker_history_repo.get_all_ticker_histories()
        logger.info(f"Retrieved {len(all_ticker_histories)} ticker history records")

        # Extract unique symbols
        unique_symbols = sorted(set(th.symbol for th in all_ticker_histories))
        total_symbols = len(unique_symbols)

        print(f"Found {total_symbols:,} unique ticker symbols to process")
        print("This includes both active and delisted tickers\n")

        # Tracking variables
        successful_count = 0
        failed_count = 0
        total_records_inserted = 0
        failed_tickers: list[tuple[str, str]] = []

        # Step 2: Process each symbol
        for idx, symbol in enumerate(unique_symbols, start=1):
            print(f"\n[{idx}/{total_symbols}] Processing {symbol}...")

            try:
                # Fetch and insert pricing data (no date limits = full history)
                result = pipeline.ingest_pricing_for_ticker(symbol)

                if result["errors"] > 0:
                    logger.error(
                        f"Error ingesting data for {symbol}: "
                        f"ticker_id={result['ticker_id']}"
                    )
                    failed_count += 1
                    failed_tickers.append((symbol, "Ingestion error"))
                else:
                    successful_count += 1
                    total_records_inserted += result["upserted"]
                    logger.info(
                        f"✓ {symbol}: Inserted {result['upserted']:,} records "
                        f"({result['from_date']} to {result['to_date']})"
                    )

            except Exception as e:
                logger.error(f"Unexpected error processing {symbol}: {e}")
                failed_count += 1
                failed_tickers.append((symbol, str(e)))

        # Step 3: Print summary
        print("\n" + "=" * 70)
        print("INGESTION SUMMARY")
        print("=" * 70)
        print(f"  Total tickers processed: {total_symbols:,}")
        print(f"  Successful: {successful_count:,}")
        print(f"  Failed: {failed_count:,}")
        print(f"  Total pricing records inserted: {total_records_inserted:,}")
        print("-" * 70)

        if failed_tickers:
            print(f"\n⚠️  {failed_count} ticker(s) failed:")
            for symbol, error in failed_tickers[:10]:  # Show first 10
                print(f"    - {symbol}: {error}")
            if len(failed_tickers) > 10:
                print(f"    ... and {len(failed_tickers) - 10} more")

        if failed_count > 0:
            print("\n⚠️  Some tickers failed. Check the logs for details.")
            return 1
        else:
            print("\n✅ All tickers processed successfully!")
            return 0

    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        return 1

    except Exception as e:
        logger.exception(f"Fatal error during ingestion: {e}")
        print(f"\n❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
