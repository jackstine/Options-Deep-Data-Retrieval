#!/usr/bin/env python3
"""Command-line tool for daily high/low pattern calculation.

This script should be run daily after EOD pricing ingestion to update patterns.
It processes all active patterns with today's pricing data.

Usage:
    # Run for today
    python -m src.cmd.algorithms.daily_high_low_calculation

    # Run for specific date
    python -m src.cmd.algorithms.daily_high_low_calculation --date 2024-01-15

Examples:
    python -m src.cmd.algorithms.daily_high_low_calculation
    python -m src.cmd.algorithms.daily_high_low_calculation --date 2024-01-15
"""

from __future__ import annotations

import argparse
import logging
from datetime import date, datetime

from src.pipelines.algorithms.high_lows.daily_high_low_pipeline import (
    DailyHighLowPipeline,
)

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


def main() -> None:
    """Run daily high/low calculation."""
    parser = argparse.ArgumentParser(
        description="Calculate daily high/low patterns for all active patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Run for today:
    python -m src.cmd.algorithms.daily_high_low_calculation

  Run for specific date:
    python -m src.cmd.algorithms.daily_high_low_calculation --date 2024-01-15
        """,
    )

    parser.add_argument(
        "--date",
        "-d",
        type=parse_date,
        help="Calculation date in YYYY-MM-DD format (default: today)",
    )

    args = parser.parse_args()
    calc_date = args.date or date.today()

    # Initialize pipeline
    logger.info("Initializing daily high/low pipeline...")
    pipeline = DailyHighLowPipeline()

    # Run daily processing
    logger.info(f"Starting daily high/low calculation for {calc_date}")
    result = pipeline.run(calculation_date=calc_date)

    # Print result
    logger.info("=" * 60)
    logger.info("DAILY HIGH/LOW CALCULATION RESULT")
    logger.info("=" * 60)
    logger.info(f"Calculation Date: {calc_date}")
    logger.info(f"Total Tickers Processed: {result['total_tickers_processed']}")
    logger.info(f"Total Patterns Processed: {result['total_patterns_processed']}")
    logger.info(f"Patterns Completed: {result['patterns_completed']}")
    logger.info(f"Patterns Updated: {result['patterns_updated']}")
    logger.info(f"Patterns Spawned: {result['patterns_spawned']}")
    logger.info(f"Patterns Expired: {result['patterns_expired']}")
    logger.info(f"Errors: {result['errors']}")
    logger.info("=" * 60)

    if result["errors"] > 0:
        logger.warning(f"{result['errors']} errors occurred during processing")
        exit(1)

    logger.info("Daily calculation complete!")


if __name__ == "__main__":
    main()
