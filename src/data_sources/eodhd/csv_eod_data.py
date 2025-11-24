#!/usr/bin/env python3
"""EODHD CSV historical EOD data loader.

This module provides functionality to load historical end-of-day pricing data
from EODHD CSV files stored locally, implementing the HistoricalDataSource interface.
"""

from __future__ import annotations

import csv
import logging
from datetime import date
from pathlib import Path

from src.data_sources.base.historical_data_source import HistoricalDataSource
from src.models.historical_eod_pricing import HistoricalEndOfDayPricing


class EodhdCsvEodHeaders:
    """Headers expected in EODHD EOD pricing CSV files."""

    DATE = "Date"
    OPEN = "Open"
    HIGH = "High"
    LOW = "Low"
    CLOSE = "Close"
    ADJUSTED_CLOSE = "Adjusted_close"
    VOLUME = "Volume"


class EodhdCsvHistoricalDataLoader:
    """EODHD CSV historical EOD data file loader and parser."""

    def __init__(self, eod_data_dir: str | Path) -> None:
        """Initialize the CSV historical data loader.

        Args:
            eod_data_dir: Directory containing EOD CSV files (one file per symbol)
        """
        self.eod_data_dir = Path(eod_data_dir)
        self.logger = logging.getLogger(__name__)

    def load_eod_file(
        self,
        symbol: str,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[HistoricalEndOfDayPricing]:
        """Load EOD pricing data for a symbol from CSV file.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            from_date: Optional start date filter
            to_date: Optional end date filter

        Returns:
            List of HistoricalEndOfDayPricing objects, sorted by date ascending

        Raises:
            FileNotFoundError: If the CSV file for the symbol doesn't exist
            ValueError: If file format is invalid
        """
        csv_file = self.eod_data_dir / f"{symbol}.csv"

        if not csv_file.exists():
            self.logger.debug(f"EOD file not found for symbol {symbol}: {csv_file}")
            return []

        self.logger.debug(f"Loading EOD data for {symbol} from {csv_file}")

        pricing_data = []

        try:
            with open(csv_file, encoding="utf-8") as f:
                csv_reader = csv.DictReader(f)
                if csv_reader.fieldnames is None:
                    raise ValueError(f"No data found in CSV: {csv_file}")

                # Validate required headers exist
                self._validate_headers(list(csv_reader.fieldnames), csv_file)

                for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header row
                    try:
                        pricing = self._convert_row_to_pricing(row, symbol)
                        if pricing:
                            # Apply date filters if provided
                            if from_date and pricing.date < from_date:
                                continue
                            if to_date and pricing.date > to_date:
                                continue

                            pricing_data.append(pricing)
                    except Exception as e:
                        self.logger.warning(
                            f"Error processing row {row_num} in {csv_file}: {e}"
                        )
                        continue

            # Sort by date ascending
            pricing_data.sort(key=lambda p: p.date)

            self.logger.debug(
                f"Successfully loaded {len(pricing_data)} EOD records for {symbol}"
            )
            return pricing_data

        except csv.Error as e:
            raise ValueError(f"Invalid CSV format in file {csv_file}: {e}")
        except Exception as e:
            self.logger.error(f"Error loading EOD file {csv_file}: {e}")
            raise

    def _validate_headers(self, fieldnames: list[str], file_path: Path) -> None:
        """Validate that required headers exist in the CSV file.

        Args:
            fieldnames: List of field names from CSV header
            file_path: Path to file for error reporting

        Raises:
            ValueError: If required headers are missing
        """
        required_headers = [
            EodhdCsvEodHeaders.DATE,
            EodhdCsvEodHeaders.OPEN,
            EodhdCsvEodHeaders.HIGH,
            EodhdCsvEodHeaders.LOW,
            EodhdCsvEodHeaders.CLOSE,
            EodhdCsvEodHeaders.ADJUSTED_CLOSE,
            EodhdCsvEodHeaders.VOLUME,
        ]

        missing_headers = [h for h in required_headers if h not in fieldnames]
        if missing_headers:
            raise ValueError(
                f"Missing required headers in {file_path}: {missing_headers}"
            )

    def _convert_row_to_pricing(
        self, row: dict, symbol: str
    ) -> HistoricalEndOfDayPricing | None:
        """Convert a CSV row to HistoricalEndOfDayPricing object.

        Args:
            row: Dictionary representing a CSV row
            symbol: Stock symbol for display purposes

        Returns:
            HistoricalEndOfDayPricing object or None if conversion fails
        """
        # Convert CSV headers (PascalCase/Mixed) to lowercase for from_dict()
        normalized_row = {
            "date": row.get(EodhdCsvEodHeaders.DATE, "").strip(),
            "open": row.get(EodhdCsvEodHeaders.OPEN, "").strip(),
            "high": row.get(EodhdCsvEodHeaders.HIGH, "").strip(),
            "low": row.get(EodhdCsvEodHeaders.LOW, "").strip(),
            "close": row.get(EodhdCsvEodHeaders.CLOSE, "").strip(),
            "adjusted_close": row.get(EodhdCsvEodHeaders.ADJUSTED_CLOSE, "").strip(),
            "volume": row.get(EodhdCsvEodHeaders.VOLUME, "").strip(),
            "symbol": symbol,
        }

        # Check for missing essential data
        if not all([
            normalized_row["date"],
            normalized_row["open"],
            normalized_row["high"],
            normalized_row["low"],
            normalized_row["close"],
            normalized_row["adjusted_close"],
            normalized_row["volume"],
        ]):
            return None

        try:
            # Use HistoricalEndOfDayPricing.from_dict() to parse and validate
            pricing = HistoricalEndOfDayPricing.from_dict(normalized_row)
            return pricing
        except Exception as e:
            self.logger.warning(
                f"Error converting row to HistoricalEndOfDayPricing for {symbol}: {e}"
            )
            return None


class EodhdCsvHistoricalDataSource(HistoricalDataSource):
    """EODHD CSV historical data source."""

    def __init__(self, eod_data_dir: str | Path | None = None):
        """Initialize EODHD CSV historical data source.

        Args:
            eod_data_dir: Directory containing EOD CSV files (one per symbol).
                         If None, uses default path relative to this module.
        """
        if eod_data_dir is None:
            # Default to data/eod/ relative to this module
            eod_data_dir = Path(__file__).parent / "data" / "eod"

        self.eod_data_dir = Path(eod_data_dir)
        self.loader = EodhdCsvHistoricalDataLoader(self.eod_data_dir)

    @property
    def name(self) -> str:
        """Name of the data source."""
        return "EODHD CSV Historical Data"

    def get_eod_data(
        self,
        symbol: str,
        from_date: date | None = None,
        to_date: date | None = None,
        period: str = "d",
    ) -> list[HistoricalEndOfDayPricing]:
        """Get end-of-day historical data for a stock symbol.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            from_date: Optional start date for filtering
            to_date: Optional end date for filtering
            period: Time period ('d' for daily) - ignored for CSV files

        Returns:
            List of HistoricalEndOfDayPricing objects, sorted by date ascending
        """
        return self.loader.load_eod_file(symbol, from_date, to_date)

    def get_latest_eod(self, symbol: str) -> HistoricalEndOfDayPricing | None:
        """Get the most recent end-of-day data for a symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Most recent HistoricalEndOfDayPricing or None if no data exists
        """
        data = self.get_eod_data(symbol)
        return data[-1] if data else None

    def is_available(self) -> bool:
        """Check if the EOD data directory exists and is available.

        Returns:
            True if directory exists, False otherwise
        """
        return self.eod_data_dir.exists() and self.eod_data_dir.is_dir()
