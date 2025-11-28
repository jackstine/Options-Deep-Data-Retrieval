"""Mock EODHD EOD data source for testing."""

from __future__ import annotations

import csv
import logging
from datetime import date
from pathlib import Path

from src.data_sources.base.historical_data_source import HistoricalDataSource
from src.data_sources.eodhd.eod_data import transform_eodhd_eod_to_pricing
from src.models.historical_eod_pricing import HistoricalEndOfDayPricing

logger = logging.getLogger(__name__)


class MockEodhdDataSource(HistoricalDataSource):
    """Mock EODHD EOD data source that reads from fixture files instead of API."""

    def __init__(self) -> None:
        """Initialize mock EODHD EOD data source."""
        self.fixtures_dir = Path(__file__).parent / "fixtures"

    @property
    def name(self) -> str:
        """Name of the data source."""
        return "Mock EODHD EOD Data"

    def is_available(self) -> bool:
        """Check if mock data source is available.

        Returns:
            Always returns True for mock data source
        """
        return True

    def get_eod_data(
        self,
        symbol: str,
        from_date: date | None = None,
        to_date: date | None = None,
        period: str = "d",
    ) -> list[HistoricalEndOfDayPricing]:
        """Get end-of-day historical data from fixture file.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL")
            from_date: Start date for historical data (optional)
            to_date: End date for historical data (optional)
            period: Data period - 'd' (daily), 'w' (weekly), 'm' (monthly) (ignored in mock)

        Returns:
            List of HistoricalEndOfDayPricing instances with historical price data
        """
        fixture_file = self.fixtures_dir / "eod_history.csv"

        try:
            with open(fixture_file, newline='') as f:
                reader = csv.DictReader(f)

                pricing_data = []
                for row in reader:
                    # Parse date
                    record_date = date.fromisoformat(row["Date"])

                    # Apply date filters
                    if from_date and record_date < from_date:
                        continue
                    if to_date and record_date > to_date:
                        continue

                    # Create HistoricalEndOfDayPricing instance
                    row["symbol"] = symbol
                    row["date"] = row.pop("Date")
                    row["open"] = row.pop("Open")
                    row["high"] = row.pop("High")
                    row["low"] = row.pop("Low")
                    row["close"] = row.pop("Close")
                    row["adjusted_close"] = row.pop("Adjusted_close")
                    row["volume"] = row.pop("Volume")

                    pricing_data.append(transform_eodhd_eod_to_pricing(row))

            logger.info(
                f"Loaded {len(pricing_data)} EOD records for {symbol} from fixture"
            )
            return pricing_data

        except FileNotFoundError:
            logger.error(f"Fixture file not found: {fixture_file}")
            return []
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return []

    def get_latest_eod(self, symbol: str) -> HistoricalEndOfDayPricing | None:
        """Get the most recent end-of-day data for a symbol.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL")

        Returns:
            HistoricalEndOfDayPricing instance with latest price data, or None if unavailable
        """
        all_data = self.get_eod_data(symbol)
        if all_data:
            return all_data[-1]  # Return the last record (most recent)
        return None
