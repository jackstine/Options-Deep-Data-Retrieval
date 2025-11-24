"""Abstract base class for stock splits data sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from src.models.split import Split


class SplitsDataSource(ABC):
    """Abstract base class for stock splits data sources."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the data source (e.g., 'EODHD', 'Alpha Vantage').

        Returns:
            String identifier for the data source
        """
        pass

    @abstractmethod
    def get_splits(
        self,
        symbol: str,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[Split]:
        """Get stock split data for a symbol.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL")
            from_date: Start date for split data (optional)
            to_date: End date for split data (optional)

        Returns:
            List of Split instances with historical split data.
            Note: ticker_history_id will be None and must be set by the caller.

        Raises:
            Exception: If data retrieval fails or returns unexpected data
        """
        pass

    @abstractmethod
    def get_current_date_splits(self, target_date: date) -> list[Split]:
        """Get all stock splits that occurred on a specific date.

        This method fetches bulk split data for all stocks on a given date.
        Useful for daily update pipelines.

        Args:
            target_date: The date to get splits for

        Returns:
            List of Split instances for all stocks with splits on that date.
            Note: ticker_history_id will be None and must be resolved by the caller
            using the symbol field.

        Raises:
            Exception: If data retrieval fails or returns unexpected data
        """
        pass

    def is_available(self) -> bool:
        """Check if the data source is available and properly configured.

        Returns:
            True if data source is available, False otherwise
        """
        return True
