"""EODHD stock splits data source for US stocks."""

from __future__ import annotations

import csv
import logging
from datetime import date
from io import StringIO
from typing import Any

import requests

from src.config.configuration import CONFIG
from src.data_sources.base.splits_data_source import SplitsDataSource
from src.models.split import Split

logger = logging.getLogger(__name__)


class EodhdSplitsDataSource(SplitsDataSource):
    """EODHD data source for retrieving stock split data."""

    SPLITS_URL = "https://eodhd.com/api/splits"
    BULK_SPLITS_URL = "https://eodhd.com/api/eod-bulk-last-day"

    def __init__(self, timeout: int = 30) -> None:
        """Initialize EODHD splits data source.

        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.timeout = timeout
        self._api_key: str | None = None

    @property
    def name(self) -> str:
        """Name of the data source."""
        return "EODHD Splits Data"

    @property
    def api_key(self) -> str:
        """Get and cache the EODHD API key."""
        if self._api_key is None:
            self._api_key = CONFIG.get_eodhd_api_key()
        return self._api_key

    def is_available(self) -> bool:
        """Check if EODHD API is available.

        Returns:
            True if API key is configured, False otherwise
        """
        try:
            _ = self.api_key
            return True
        except Exception:
            return False

    def get_splits(
        self,
        symbol: str,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[Split]:
        """Get stock split data for a US stock symbol.

        Uses the EODHD splits endpoint to retrieve historical split data
        for a given symbol. Automatically appends .US suffix for US stocks.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL")
            from_date: Start date for split data (optional)
            to_date: End date for split data (optional)

        Returns:
            List of Split instances with historical split data.
            Note: ticker_history_id will be None and must be set by the caller.

        Raises:
            Exception: If API request fails or returns unexpected data
        """
        # Store original symbol for model
        original_symbol = symbol

        # Ensure symbol has .US suffix for API call
        if not symbol.endswith(".US"):
            symbol = f"{symbol}.US"

        url = f"{self.SPLITS_URL}/{symbol}"
        params: dict[str, Any] = {
            "api_token": self.api_key,
            "fmt": "csv",
        }

        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            # Parse CSV response
            csv_data = response.text
            splits_data = self._parse_individual_splits_csv(csv_data, original_symbol)

            logger.info(
                f"Retrieved {len(splits_data)} split records for {symbol}"
            )
            return splits_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch splits data for {symbol}: {e}")
            raise

    def get_current_date_splits(self, target_date: date) -> list[Split]:
        """Get all stock splits that occurred on a specific date.

        Uses the EODHD bulk endpoint to retrieve all splits for a given date
        across all US stocks.

        Args:
            target_date: The date to get splits for

        Returns:
            List of Split instances for all stocks with splits on that date.
            Note: ticker_history_id will be None and must be resolved by the caller
            using the symbol field.

        Raises:
            Exception: If API request fails or returns unexpected data
        """
        url = f"{self.BULK_SPLITS_URL}/US"
        params = {
            "api_token": self.api_key,
            "fmt": "csv",
            "type": "splits",
            "date": target_date.isoformat(),
        }

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            # Parse CSV response
            csv_data = response.text
            splits_data = self._parse_bulk_splits_csv(csv_data)

            logger.info(
                f"Retrieved {len(splits_data)} split records for date {target_date}"
            )
            return splits_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch bulk splits for {target_date}: {e}")
            raise

    def _parse_individual_splits_csv(
        self, csv_data: str, symbol: str
    ) -> list[Split]:
        """Parse CSV data from individual symbol splits endpoint.

        Expected format:
        Date,"Stock Splits"
        2014-11-03,1398.000000/1000.000000

        Args:
            csv_data: Raw CSV string from API
            symbol: Stock symbol for the data

        Returns:
            List of Split instances
        """
        splits = []
        reader = csv.DictReader(StringIO(csv_data))

        for row in reader:
            try:
                split_date = date.fromisoformat(row["Date"])
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

        return splits

    def _parse_bulk_splits_csv(self, csv_data: str) -> list[Split]:
        """Parse CSV data from bulk splits endpoint.

        Expected format:
        Code,Ex,Date,Split
        BLMZ,US,2025-11-21,1.000000/10.000000
        BUGLF,US,2025-11-21,1.000000/20.000000

        Args:
            csv_data: Raw CSV string from API

        Returns:
            List of Split instances
        """
        splits = []
        reader = csv.DictReader(StringIO(csv_data))

        for row in reader:
            try:
                symbol = row["Code"].strip()
                split_date = date.fromisoformat(row["Date"])
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

        return splits


if __name__ == "__main__":
    # Example usage
    source = EodhdSplitsDataSource()
    if source.is_available():
        print(f"Using data source: {source.name}")

        # Example 1: Get splits for a specific symbol
        symbol = "AAPL"
        print(f"\nFetching historical splits for {symbol}...")

        splits = source.get_splits(symbol)
        print(f"Retrieved {len(splits)} split records")

        if splits:
            print("\nAll splits:")
            for split in splits:
                ratio = split.get_split_ratio()
                print(f"  {split.date}: {split.split_ratio} (ratio={ratio})")

        # Example 2: Get splits for a specific date (bulk)
        print("\nFetching splits for a specific date...")
        from datetime import timedelta

        target_date = date.today() - timedelta(days=7)
        bulk_splits = source.get_current_date_splits(target_date)
        print(f"Retrieved {len(bulk_splits)} splits for {target_date}")

        if bulk_splits:
            print(f"\nSplits on {target_date}:")
            for split in bulk_splits[:10]:  # Show first 10
                ratio = split.get_split_ratio()
                print(f"  {split.symbol}: {split.split_ratio} (ratio={ratio})")

    else:
        print("EODHD API is not available. Please set EODHD_API_KEY.")
