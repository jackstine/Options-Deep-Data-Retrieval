"""Abstract base class for historical end-of-day pricing data sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from src.models.historical_eod_pricing import HistoricalEndOfDayPricing


class HistoricalDataSource(ABC):
    """Abstract base class for historical end-of-day pricing data sources."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the data source (e.g., 'EODHD', 'Alpha Vantage').

        Returns:
            String identifier for the data source
        """
        pass

    @abstractmethod
    def get_eod_data(
        self,
        symbol: str,
        from_date: date | None = None,
        to_date: date | None = None,
        period: str = "d",
    ) -> list[HistoricalEndOfDayPricing]:
        """Get end-of-day historical data for a stock symbol.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL")
            from_date: Start date for historical data (optional)
            to_date: End date for historical data (optional)
            period: Data period - 'd' (daily), 'w' (weekly), 'm' (monthly)

        Returns:
            List of HistoricalEndOfDayPricing instances with historical price data

        Raises:
            Exception: If data retrieval fails or returns unexpected data
        """
        pass

    @abstractmethod
    def get_latest_eod(self, symbol: str) -> HistoricalEndOfDayPricing | None:
        """Get the most recent end-of-day data for a symbol.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL")

        Returns:
            HistoricalEndOfDayPricing instance with latest price data, or None if unavailable
        """
        pass

    def is_available(self) -> bool:
        """Check if the data source is available and properly configured.

        Returns:
            True if data source is available, False otherwise
        """
        return True
