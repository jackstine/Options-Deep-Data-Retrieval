"""EODHD symbols data source for active and delisted US stocks."""

from __future__ import annotations

import logging
from typing import Any

import requests

import src.config.environment as en
from src.data_sources.models.company import Company

logger = logging.getLogger(__name__)


class EodhdSymbolsSource:
    """EODHD data source for retrieving US stock symbols (active and delisted)."""

    BASE_URL = "https://eodhd.com/api"

    def __init__(self, timeout: int = 30) -> None:
        """Initialize EODHD symbols data source.

        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.timeout = timeout
        self._api_key: str | None = None

    @property
    def name(self) -> str:
        """Name of the data source."""
        return "EODHD Symbols"

    @property
    def api_key(self) -> str:
        """Get and cache the EODHD API key."""
        if self._api_key is None:
            self._api_key = en.ENVIRONMENT_VARIABLES.get_eodhd_api_key()
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

    def get_delisted_symbols(self) -> list[Company]:
        """Get delisted US stock symbols from EODHD API.

        Uses the EODHD delisted symbols endpoint to retrieve all delisted
        companies. Filters for US-only symbols.

        Returns:
            List of Company instances with symbol information

        Raises:
            Exception: If API request fails or returns unexpected data
        """
        url = f"{self.BASE_URL}/delisted-symbols"
        params = {"api_token": self.api_key, "fmt": "json"}

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data: Any = response.json()
            if not isinstance(data, list):
                logger.error(f"Unexpected response format: {type(data)}")
                return []

            # Filter for US symbols only and convert to Company instances
            us_companies: list[Company] = []
            for symbol in data:
                if symbol.get("Exchange") in ["US", "NYSE", "NASDAQ", "AMEX"]:
                    symbol["source"] = "EODHD"
                    us_companies.append(Company.from_dict(symbol))

            logger.info(f"Retrieved {len(us_companies)} delisted US symbols")
            return us_companies

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch delisted symbols: {e}")
            raise

    def get_active_symbols(self, exchange: str = "US") -> list[Company]:
        """Get active US stock symbols from EODHD API.

        Uses the EODHD exchange symbols list endpoint to retrieve all
        currently trading symbols on the specified exchange.

        Args:
            exchange: Exchange code (default: "US" for all US exchanges)

        Returns:
            List of Company instances with symbol information

        Raises:
            Exception: If API request fails or returns unexpected data
        """
        url = f"{self.BASE_URL}/exchange-symbol-list/{exchange}"
        params = {"api_token": self.api_key, "fmt": "json"}

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data: Any = response.json()
            if not isinstance(data, list):
                logger.error(f"Unexpected response format: {type(data)}")
                return []

            # Convert to Company instances
            companies = []
            for symbol in data:
                symbol["source"] = "EODHD"
                companies.append(Company.from_dict(symbol))

            logger.info(f"Retrieved {len(companies)} active symbols from {exchange}")
            return companies

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch active symbols: {e}")
            raise

    def get_all_us_symbols(self) -> dict[str, list[Company]]:
        """Get all US symbols (both active and delisted).

        Convenience method that fetches both active and delisted symbols
        and returns them in a categorized dictionary.

        Returns:
            Dictionary with 'active' and 'delisted' keys, each containing
            a list of Company instances
        """
        return {
            "active": self.get_active_symbols(),
            "delisted": self.get_delisted_symbols(),
        }


if __name__ == "__main__":
    # Example usage
    source = EodhdSymbolsSource()
    if source.is_available():
        print(f"Using data source: {source.name}")

        # Get active symbols
        print("\nFetching active US symbols...")
        active = source.get_active_symbols()
        print(f"Retrieved {len(active)} active symbols")
        if active:
            print("\nFirst 3 active symbols:")
            for company in active[:3]:
                ticker = company.ticker.symbol if company.ticker else "N/A"
                print(f"  {ticker}: {company.company_name}")

        # Get delisted symbols
        print("\nFetching delisted US symbols...")
        delisted = source.get_delisted_symbols()
        print(f"Retrieved {len(delisted)} delisted symbols")
        if delisted:
            print("\nFirst 3 delisted symbols:")
            for company in delisted[:3]:
                ticker = company.ticker.symbol if company.ticker else "N/A"
                print(f"  {ticker}: {company.company_name}")
    else:
        print("EODHD API is not available. Please set EODHD_API_KEY.")
