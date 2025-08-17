"""Yahoo Finance data source provider using yfinance library."""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

import yfinance as yf  # type: ignore

from src.data_sources.base.base import DataSourceBase
from src.data_sources.models.stock_quote import StockQuote

logger = logging.getLogger(__name__)


class YahooFinanceProvider(DataSourceBase):
    """Yahoo Finance data source provider using yfinance library."""

    def __init__(self, timeout: int = 30) -> None:
        """Initialize Yahoo Finance provider.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self._name = "Yahoo Finance"

    @property
    def name(self) -> str:
        """Get the name of the data source."""
        return self._name

    def fetch_quotes(self, symbols: list[str]) -> list[StockQuote]:
        """Fetch stock quotes for given symbols using yfinance.

        Args:
            symbols: List of stock symbols to fetch quotes for

        Returns:
            List of StockQuote objects with normalized data
        """
        quotes: list[StockQuote] = []

        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info

                # Get current quote data
                # TODO_JAKE need to confirm all the data that we can get from yfinance
                # print(json.dumps(info, indent=2))

                quote = self._generate_stock_quote(symbol, info)
                if quote:
                    quotes.append(quote)
                else:
                    # TODO_JAKE we might get an error such as a 429.
                    # we need to see what the rate limit is on the yFinance.... if we are going to use it.
                    logger.warning(f"No data available for symbol: {symbol}")

            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {str(e)}")
                continue

        return quotes

    def _generate_stock_quote(
        self, symbol: str, info: dict[str, Any]
    ) -> StockQuote | None:
        """Generate a Yahoo Finance data to StockQuote format.

        Args:
            symbol: Stock symbol
            info: Raw data from yfinance

        Returns:
            Normalized StockQuote object or None if data is invalid
        """
        try:
            # Extract current price - try multiple fields
            current_price = self._get_current_price(info)
            if current_price is None:
                logger.warning(f"No valid price found for {symbol}")
                return None

            # Create StockQuote with available data
            quote = StockQuote(
                symbol=symbol.upper(),
                price=Decimal(str(current_price)),
                bid=self._safe_decimal(info.get("bid")),
                ask=self._safe_decimal(info.get("ask")),
                volume=int(info.get("volume", 0))
                if info.get("volume") is not None
                else 0,
                market_cap=self._safe_decimal(info.get("marketCap")),
                day_high=self._safe_decimal(info.get("dayHigh")),
                day_low=self._safe_decimal(info.get("dayLow")),
                previous_close=self._safe_decimal(info.get("previousClose")),
                open_price=self._safe_decimal(info.get("open")),
                fifty_two_week_high=self._safe_decimal(info.get("fiftyTwoWeekHigh")),
                fifty_two_week_low=self._safe_decimal(info.get("fiftyTwoWeekLow")),
                pe_ratio=self._safe_decimal(info.get("trailingPE")),
                dividend_yield=self._safe_decimal(info.get("dividendYield")),
                timestamp=datetime.now(),
                source=self.name,
            )

            return quote

        except Exception as e:
            logger.error(f"Error normalizing data for {symbol}: {str(e)}")
            return None

    def _get_current_price(self, info: dict[str, Any]) -> float | None:
        """Extract current price from various possible fields.

        Args:
            info: Raw data from yfinance

        Returns:
            Current price as float or None if not found
        """
        # Try different price fields in order of preference
        price_fields = [
            "currentPrice",
            "regularMarketPrice",
            "price",
            "previousClose",
            "ask",
            "bid",
        ]

        for field in price_fields:
            price = info.get(field)
            if price is not None and price > 0:
                return float(price)

        return None

    def _safe_decimal(self, value: Any) -> Decimal | None:
        """Safely convert value to Decimal.

        Args:
            value: Value to convert

        Returns:
            Decimal value or None if conversion fails
        """
        if value is None:
            return None

        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None

    def validate_connection(self) -> bool:
        """Validate connection to Yahoo Finance by testing with a known symbol.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Test with a well-known symbol
            ticker = yf.Ticker("AAPL")
            info = ticker.info

            # Check if we got valid data back
            return info is not None and len(info) > 0 and "symbol" in info

        except Exception as e:
            logger.error(f"Connection validation failed: {str(e)}")
            return False

    def get_supported_symbols(self) -> list[str]:
        """Get list of supported stock symbols.

        Note: Yahoo Finance supports a vast number of symbols.
        This method returns a sample of common symbols for demonstration.
        In practice, you might want to implement symbol search functionality.

        Returns:
            List of sample supported stock symbols
        """
        # Return a sample of well-known symbols
        # In a real implementation, you might fetch this from Yahoo Finance
        # or maintain a more comprehensive list
        return [
            "AAPL",
            "GOOGL",
            "MSFT",
            "AMZN",
            "TSLA",
            "META",
            "NVDA",
            "AMD",
            "NFLX",
            "UBER",
            "LYFT",
            "ZOOM",
            "SHOP",
            "SQ",
            "PYPL",
            "CRM",
            "ORCL",
            "IBM",
            "INTC",
            "CSCO",
            "BA",
            "JPM",
            "BAC",
            "WFC",
            "V",
            "MA",
            "JNJ",
            "PFE",
            "KO",
            "PEP",
            "WMT",
            "TGT",
        ]
