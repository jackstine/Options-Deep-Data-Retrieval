"""EODHD bulk end-of-day data source for fetching entire exchange data."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any

import requests

from src.config.configuration import CONFIG
from src.data_sources.base.bulk_eod_data_source import BulkEodDataSource
from src.data_sources.eodhd.symbols import EodhdSymbolsSource
from src.database.equities.enums import DataSourceEnum
from src.models.misplaced_eod_pricing import MisplacedEndOfDayPricing

logger = logging.getLogger(__name__)


class EodhdDailyBulkEodData(BulkEodDataSource):
    """EODHD data source for retrieving bulk end-of-day data for entire exchanges.

    Uses the /eod-bulk-last-day endpoint to efficiently fetch latest EOD data
    for all symbols in an exchange with a single API call.
    """

    BASE_URL = "https://eodhd.com/api/eod-bulk-last-day"

    def __init__(self, timeout: int = 60) -> None:
        """Initialize EODHD bulk EOD data source.

        Args:
            timeout: Request timeout in seconds (default: 60 for bulk requests)
        """
        self.timeout = timeout
        self._api_key: str | None = None

    @property
    def name(self) -> str:
        """Name of the data source."""
        return "EODHD Bulk EOD Data"

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

    def get_bulk_latest_eod(
        self,
        exchange: str = "US",
        filter_common_stock: bool = True,
    ) -> dict[str, MisplacedEndOfDayPricing]:
        """Get latest end-of-day data for all symbols in an exchange.

        Fetches bulk EOD pricing data using EODHD's bulk endpoint.
        Returns data as MisplacedEndOfDayPricing since ticker_history
        associations are determined by the caller.

        Args:
            exchange: Exchange code (default: "US" for all US exchanges)
            filter_common_stock: If True, only return Common Stock symbols

        Returns:
            Dictionary mapping symbol (str) to MisplacedEndOfDayPricing instance

        Raises:
            requests.exceptions.RequestException: If API request fails
        """
        url = f"{self.BASE_URL}/{exchange}"
        params = {
            "api_token": self.api_key,
            "fmt": "json",
        }

        try:
            logger.info(f"Fetching bulk EOD data for exchange: {exchange}")
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data: Any = response.json()
            if not isinstance(data, list):
                logger.error(f"Unexpected response format for {exchange}: {type(data)}")
                return {}

            # Convert each record to MisplacedEndOfDayPricing
            pricing_dict: dict[str, MisplacedEndOfDayPricing] = {}
            for record in data:
                try:
                    # Extract symbol (remove .US suffix if present)
                    code = record.get("code")
                    symbol = code.split(".")[0] if code and "." in code else code

                    if not symbol:
                        logger.warning(f"Skipping record with missing symbol: {record}")
                        continue

                    # Parse date
                    date_str = record.get("date")
                    if not date_str:
                        logger.warning(f"Skipping {symbol}: missing date")
                        continue
                    pricing_date = date.fromisoformat(date_str)

                    # Create MisplacedEndOfDayPricing instance
                    pricing = MisplacedEndOfDayPricing(
                        symbol=symbol,
                        date=pricing_date,
                        open=Decimal(str(record.get("open", 0))),
                        high=Decimal(str(record.get("high", 0))),
                        low=Decimal(str(record.get("low", 0))),
                        close=Decimal(str(record.get("close", 0))),
                        adjusted_close=Decimal(str(record.get("adjusted_close", 0))),
                        volume=int(record.get("volume", 0)),
                        source=DataSourceEnum.EODHD,
                    )

                    pricing_dict[symbol] = pricing

                except (ValueError, TypeError, KeyError) as e:
                    logger.warning(
                        f"Failed to parse record for symbol {record.get('code', 'unknown')}: {e}"
                    )
                    continue

            logger.info(
                f"Retrieved {len(pricing_dict)} EOD records for exchange {exchange}"
            )

            # Filter for Common Stock if requested
            if filter_common_stock:
                logger.info("Filtering for Common Stock symbols...")
                symbols_source = EodhdSymbolsSource()
                companies = symbols_source.get_active_symbols()

                # Create mapping of symbol to company
                symbol_info = {
                    company.ticker.symbol: company
                    for company in companies
                    if company.ticker and company.ticker.symbol
                }

                # Filter to keep only Common Stock symbols
                original_count = len(pricing_dict)
                pricing_dict = {
                    symbol: pricing
                    for symbol, pricing in pricing_dict.items()
                    if symbol in symbol_info and symbol_info[symbol].type == "Common Stock"
                }

                logger.info(
                    f"Filtered from {original_count} to {len(pricing_dict)} Common Stock symbols"
                )

            return pricing_dict

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch bulk EOD data for {exchange}: {e}")
            raise


if __name__ == "__main__":
    # Example usage
    source = EodhdDailyBulkEodData()
    if source.is_available():
        print(f"Using data source: {source.name}")

        # Get bulk EOD data for US exchanges
        print("\nFetching bulk EOD data for US exchanges...")
        data = source.get_bulk_latest_eod(exchange="US", filter_common_stock=True)

        print(f"Retrieved {len(data)} symbols")

        # Display first 5 symbols
        if data:
            print("\nSample of first 5 symbols:")
            for i, (symbol, pricing) in enumerate(list(data.items())[:5]):
                print(
                    f"  {symbol}: {pricing.date} - "
                    f"Close=${pricing.close:.2f}, Volume={pricing.volume:,}"
                )
    else:
        print("EODHD API is not available. Please set EODHD_API_KEY.")
