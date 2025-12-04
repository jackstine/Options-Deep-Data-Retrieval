#!/usr/bin/env python3
"""Command-line tool for backfilling high/low patterns from historical data.

This script generates pattern data for ticker(s) from historical pricing data.
It should be run once to initialize pattern data before starting daily updates.

Usage:
    # Backfill single ticker
    python -m src.cmd.algorithms.backfill_high_low --ticker AAPL

    # Backfill single ticker with date range
    python -m src.cmd.algorithms.backfill_high_low --ticker AAPL --from-date 2020-01-01

    # Backfill all active tickers
    python -m src.cmd.algorithms.backfill_high_low --all

    # Backfill specific thresholds only
    python -m src.cmd.algorithms.backfill_high_low --ticker AAPL --thresholds 0.15,0.20,0.25

Examples:
    python -m src.cmd.algorithms.backfill_high_low --ticker AAPL
    python -m src.cmd.algorithms.backfill_high_low --all
"""

from __future__ import annotations

import argparse
import logging
from datetime import date, datetime
from decimal import Decimal

from src.algorithms.constants import DEFAULT_THRESHOLDS
from src.algorithms.high_lows.pattern_config import HighLowPatternConfig
from src.pipelines.algorithms.high_lows import BackfillHighLowPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_date(date_string: str) -> date:
    """Parse date string to date object.

    Args:
        date_string: Date in YYYY-MM-DD format

    Returns:
        date object
    """
    return datetime.strptime(date_string, "%Y-%m-%d").date()


def parse_thresholds(threshold_string: str) -> list[Decimal]:
    """Parse comma-separated thresholds.

    Args:
        threshold_string: Comma-separated thresholds (e.g., "0.15,0.20,0.25")

    Returns:
        List of Decimal thresholds
    """
    return [Decimal(t.strip()) for t in threshold_string.split(",")]


def main() -> None:
    """Run backfill high/low command."""
    parser = argparse.ArgumentParser(
        description="Backfill high/low patterns from historical pricing data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Backfill single ticker:
    python -m src.cmd.algorithms.backfill_high_low --ticker AAPL

  Backfill with date range:
    python -m src.cmd.algorithms.backfill_high_low --ticker AAPL --from-date 2020-01-01

  Backfill all active tickers:
    python -m src.cmd.algorithms.backfill_high_low --all

  Backfill specific thresholds:
    python -m src.cmd.algorithms.backfill_high_low --ticker AAPL --thresholds 0.15,0.20,0.25
        """,
    )

    # Ticker selection (mutually exclusive)
    ticker_group = parser.add_mutually_exclusive_group(required=True)
    ticker_group.add_argument(
        "--ticker",
        "-t",
        type=str,
        help="Single ticker symbol to backfill (e.g., AAPL)",
    )
    ticker_group.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Backfill all active tickers",
    )

    # Date range
    parser.add_argument(
        "--from-date",
        type=parse_date,
        help="Start date in YYYY-MM-DD format (default: all available history)",
    )
    parser.add_argument(
        "--to-date",
        type=parse_date,
        help="End date in YYYY-MM-DD format (default: most recent date)",
    )

    # Thresholds
    parser.add_argument(
        "--thresholds",
        type=parse_thresholds,
        help="Comma-separated thresholds (e.g., 0.15,0.20,0.25) (default: standard thresholds)",
    )

    args = parser.parse_args()

    # Create configs
    if args.thresholds:
        configs = [HighLowPatternConfig(threshold=t) for t in args.thresholds]
    else:
        configs = [HighLowPatternConfig(threshold=t) for t in DEFAULT_THRESHOLDS]

    # Initialize pipeline with configs
    logger.info("Initializing backfill pipeline...")
    pipeline = BackfillHighLowPipeline(configs=configs)

    # Run backfill
    if args.ticker:
        logger.info(f"Starting backfill for ticker: {args.ticker}")
        result = pipeline.run(
            ticker_symbol=args.ticker,
            from_date=args.from_date,
            to_date=args.to_date,
        )

        # Print result
        logger.info("=" * 60)
        logger.info("BACKFILL RESULT")
        logger.info("=" * 60)
        logger.info(f"Ticker: {result['ticker_symbol']}")
        logger.info(f"Ticker History ID: {result['ticker_history_id']}")
        logger.info(f"Date Range: {result['from_date']} to {result['to_date']}")
        logger.info(f"Total Patterns Generated: {result['total_patterns_generated']}")
        logger.info(f"Active Patterns Inserted: {result['active_patterns_inserted']}")
        logger.info(f"Completed Patterns Inserted: {result['completed_patterns_inserted']}")
        logger.info(f"Errors: {result['errors']}")
        logger.info("=" * 60)

        if result["errors"] > 0:
            exit(1)

    else:  # --all
        logger.info("Starting bulk backfill for all active tickers")
        results = pipeline.run(
            from_date=args.from_date,
            to_date=args.to_date,
        )

        # Print summary
        logger.info("=" * 60)
        logger.info("BULK BACKFILL SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tickers Processed: {len(results)}")
        total_patterns = sum(r["total_patterns_generated"] for r in results)
        total_active = sum(r["active_patterns_inserted"] for r in results)
        total_completed = sum(r["completed_patterns_inserted"] for r in results)
        total_errors = sum(r["errors"] for r in results)
        logger.info(f"Total Patterns Generated: {total_patterns}")
        logger.info(f"Total Active Patterns: {total_active}")
        logger.info(f"Total Completed Patterns: {total_completed}")
        logger.info(f"Total Errors: {total_errors}")
        logger.info("=" * 60)

        if total_errors > 0:
            logger.warning(f"{total_errors} tickers had errors during backfill")
            exit(1)

    logger.info("Backfill complete!")


if __name__ == "__main__":
    main()
