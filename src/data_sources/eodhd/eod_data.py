"""EODHD end-of-day historical data source for US stocks."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any

import requests

from src.config.configuration import CONFIG
from src.data_sources.base.historical_data_source import HistoricalDataSource
from src.models.historical_eod_pricing import HistoricalEndOfDayPricing

logger = logging.getLogger(__name__)


def transform_eodhd_eod_to_pricing(data: dict[str, Any]) -> HistoricalEndOfDayPricing:
    """Transform EODHD API EOD data to HistoricalEndOfDayPricing model.

    Handles EODHD API snake_case format for EOD pricing data.

    Args:
        data: Dictionary from EODHD API with EOD pricing fields

    Returns:
        HistoricalEndOfDayPricing: Pricing model instance
    """
    # Parse date from string if needed
    pricing_date = data["date"]
    if isinstance(pricing_date, str):
        pricing_date = date.fromisoformat(pricing_date)

    return HistoricalEndOfDayPricing(
        ticker_history_id=data.get("ticker_history_id"),
        symbol=data.get("symbol"),
        date=pricing_date,
        open=Decimal(str(data["open"])),
        high=Decimal(str(data["high"])),
        low=Decimal(str(data["low"])),
        close=Decimal(str(data["close"])),
        adjusted_close=Decimal(str(data["adjusted_close"])),
        volume=int(data["volume"]),
    )


class EodhdDataSource(HistoricalDataSource):
    """EODHD data source for retrieving end-of-day historical price data."""

    BASE_URL = "https://eodhd.com/api/eod"

    def __init__(self, timeout: int = 30) -> None:
        """Initialize EODHD EOD data source.

        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.timeout = timeout
        self._api_key: str | None = None

    @property
    def name(self) -> str:
        """Name of the data source."""
        return "EODHD EOD Data"

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

    def get_eod_data(
        self,
        symbol: str,
        from_date: date | None = None,
        to_date: date | None = None,
        period: str = "d",
    ) -> list[HistoricalEndOfDayPricing]:
        """Get end-of-day historical data for a US stock symbol.

        Uses the EODHD EOD endpoint to retrieve historical OHLCV data
        for a given symbol. Automatically appends .US suffix for US stocks.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL")
            from_date: Start date for historical data (optional)
            to_date: End date for historical data (optional)
            period: Data period - 'd' (daily), 'w' (weekly), 'm' (monthly)

        Returns:
            List of HistoricalEndOfDayPricing instances with historical price data

        Raises:
            Exception: If API request fails or returns unexpected data
        """
        # Store original symbol for model
        original_symbol = symbol

        # Ensure symbol has .US suffix for API call
        if not symbol.endswith(".US"):
            symbol = f"{symbol}.US"

        url = f"{self.BASE_URL}/{symbol}"
        params = {
            "api_token": self.api_key,
            "fmt": "json",
            "period": period,
        }

        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data: Any = response.json()
            if not isinstance(data, list):
                logger.error(f"Unexpected response format for {symbol}: {type(data)}")
                return []

            # Convert each dict to HistoricalEndOfDayPricing instance
            pricing_data = []
            for record in data:
                record["symbol"] = original_symbol
                pricing_data.append(transform_eodhd_eod_to_pricing(record))

            logger.info(
                f"Retrieved {len(pricing_data)} EOD records for {symbol}"
            )
            return pricing_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch EOD data for {symbol}: {e}")
            raise

    def get_latest_eod(self, symbol: str) -> HistoricalEndOfDayPricing | None:
        """Get the most recent end-of-day data for a symbol.

        Convenience method that fetches the latest EOD data point.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL")

        Returns:
            HistoricalEndOfDayPricing instance with latest price data, or None if unavailable
        """
        # Store original symbol for model
        original_symbol = symbol

        # Ensure symbol has .US suffix for API call
        if not symbol.endswith(".US"):
            symbol = f"{symbol}.US"

        url = f"{self.BASE_URL}/{symbol}"
        params = {
            "api_token": self.api_key,
            "fmt": "json",
            "filter": "last_close",
        }

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data: Any = response.json()
            if isinstance(data, list) and len(data) > 0:
                data[0]["symbol"] = original_symbol
                return transform_eodhd_eod_to_pricing(data[0])
            elif isinstance(data, dict):
                data["symbol"] = original_symbol
                return transform_eodhd_eod_to_pricing(data)
            else:
                logger.warning(f"No data available for {symbol}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch latest EOD for {symbol}: {e}")
            return None


if __name__ == "__main__":
    # Example usage
    source = EodhdDataSource()
    if source.is_available():
        print(f"Using data source: {source.name}")

        # Get recent EOD data for AAPL
        symbol = "AAPL"
        print(f"\nFetching recent EOD data for {symbol}...")

        # Get last 30 days
        from datetime import timedelta

        today = date.today()
        from_date = today - timedelta(days=30)

        data = source.get_eod_data(symbol, from_date=from_date, to_date=today)
        print(f"Retrieved {len(data)} days of data")

        if data:
            print("\nMost recent 3 days:")
            for record in data[-3:]:
                print(
                    f"  {record.date}: "
                    f"Open=${record.open:.2f}, "
                    f"Close=${record.close:.2f}, "
                    f"Volume={record.volume:,}"
                )

        # Get latest close
        print(f"\nFetching latest close for {symbol}...")
        latest = source.get_latest_eod(symbol)
        if latest:
            print(f"  Latest: {latest.date} - Close=${latest.close:.2f}")
    else:
        print("EODHD API is not available. Please set EODHD_API_KEY.")
