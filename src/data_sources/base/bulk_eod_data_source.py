"""Abstract base class for bulk end-of-day pricing data sources."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.misplaced_eod_pricing import MisplacedEndOfDayPricing


class BulkEodDataSource(ABC):
    """Abstract base class for bulk end-of-day pricing data sources.

    This interface defines methods for fetching bulk EOD data for entire
    exchanges or large sets of symbols in a single request.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the data source (e.g., 'EODHD Bulk', 'Alpha Vantage Bulk').

        Returns:
            String identifier for the data source
        """
        pass

    @abstractmethod
    def get_bulk_latest_eod(
        self,
        exchange: str = "US",
        filter_common_stock: bool = True,
    ) -> dict[str, MisplacedEndOfDayPricing]:
        """Get latest end-of-day data for all symbols in an exchange.

        Fetches bulk EOD pricing data for an entire exchange or market.
        Returns data as MisplacedEndOfDayPricing since ticker_history
        associations are determined by the caller.

        Args:
            exchange: Exchange code (e.g., "US", "NYSE", "NASDAQ")
            filter_common_stock: If True, filter for Common Stock only

        Returns:
            Dictionary mapping symbol (str) to MisplacedEndOfDayPricing instance

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
