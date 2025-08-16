"""Abstract base class for data sources."""

from src.data_sources.models.stock_quote import StockQuote

from __future__ import annotations

from abc import ABC, abstractmethod


class DataSourceBase(ABC):
    """Abstract base class for all data source providers."""

    @abstractmethod
    def fetch_quotes(self, symbols: list[str]) -> list[StockQuote]:
        """Fetch stock quotes for given symbols.

        Args:
            symbols: List of stock symbols to fetch quotes for

        Returns:
            List of StockQuote objects with normalized data

        Raises:
            DataSourceError: When data retrieval fails
            ValidationError: When symbol validation fails
        """
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate connection to the data source.

        Returns:
            True if connection is valid, False otherwise
        """
        pass

    @abstractmethod
    def get_supported_symbols(self) -> list[str]:
        """Get list of supported stock symbols.

        Returns:
            List of supported stock symbols
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the data source.

        Returns:
            String identifier for the data source
        """
        pass
