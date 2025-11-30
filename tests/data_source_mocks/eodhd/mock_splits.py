"""Mock EODHD splits data source for testing."""

from __future__ import annotations

import csv
import logging
from datetime import date
from pathlib import Path

from src.data_sources.base.splits_data_source import SplitsDataSource
from src.models.split import Split

logger = logging.getLogger(__name__)


class MockEodhdSplitsDataSource(SplitsDataSource):
    """Mock EODHD splits data source that reads from fixture files instead of API."""

    def __init__(self) -> None:
        """Initialize mock EODHD splits data source."""
        self.fixtures_dir = Path(__file__).parent / "fixtures"

    @property
    def name(self) -> str:
        """Name of the data source."""
        return "Mock EODHD Splits Data"

    def is_available(self) -> bool:
        """Check if mock data source is available.

        Returns:
            Always returns True for mock data source
        """
        return True

    def get_splits(
        self,
        symbol: str,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[Split]:
        """Get stock split data for a symbol from fixture file.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL")
            from_date: Start date for split data (optional)
            to_date: End date for split data (optional)

        Returns:
            List of Split instances with historical split data.
            Note: ticker_history_id will be None and must be set by the caller.
        """
        fixture_file = self.fixtures_dir / "splits.csv"

        try:
            with open(fixture_file, newline='') as f:
                reader = csv.DictReader(f)

                splits = []
                for row in reader:
                    try:
                        split_date = date.fromisoformat(row["Date"])

                        # Apply date filters
                        if from_date and split_date < from_date:
                            continue
                        if to_date and split_date > to_date:
                            continue

                        split_ratio = row["Stock Splits"].strip()

                        split = Split(
                            date=split_date,
                            split_ratio=split_ratio,
                            symbol=symbol,
                            ticker_history_id=None,  # Must be set by caller
                        )
                        splits.append(split)

                    except (KeyError, ValueError) as e:
                        logger.warning(f"Failed to parse split row for {symbol}: {row}. Error: {e}")
                        continue

            logger.info(f"Loaded {len(splits)} split records for {symbol} from fixture")
            return splits

        except FileNotFoundError:
            logger.error(f"Fixture file not found: {fixture_file}")
            return []
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return []

    def get_current_date_splits(self, target_date: date) -> list[Split]:
        """Get all stock splits that occurred on a specific date from fixture file.

        Args:
            target_date: The date to get splits for

        Returns:
            List of Split instances for all stocks with splits on that date.
            Note: ticker_history_id will be None and must be resolved by the caller
            using the symbol field.
        """
        fixture_file = self.fixtures_dir / "bulk_splits.csv"

        try:
            with open(fixture_file, newline='') as f:
                reader = csv.DictReader(f)

                splits = []
                for row in reader:
                    try:
                        symbol = row["Code"].strip()
                        split_date = date.fromisoformat(row["Date"])

                        # Only return splits for the target date
                        if split_date != target_date:
                            continue

                        split_ratio = row["Split"].strip()

                        split = Split(
                            date=split_date,
                            split_ratio=split_ratio,
                            symbol=symbol,
                            ticker_history_id=None,  # Must be resolved by caller
                        )
                        splits.append(split)

                    except (KeyError, ValueError) as e:
                        logger.warning(f"Failed to parse bulk split row: {row}. Error: {e}")
                        continue

            logger.info(f"Loaded {len(splits)} split records for date {target_date} from fixture")
            return splits

        except FileNotFoundError:
            logger.error(f"Fixture file not found: {fixture_file}")
            return []
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return []
