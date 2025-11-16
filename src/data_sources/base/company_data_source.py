"""Simple interface for company data sources."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.company import Company


class CompanyDataSource(ABC):
    """Simple interface that all company data sources must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the data source (e.g., 'NASDAQ', 'Yahoo Finance')."""
        pass

    @abstractmethod
    def get_companies(self) -> list[Company]:
        """Get active companies from this data source.

        Returns:
            List of Company objects for active/currently trading companies
        """
        pass

    @abstractmethod
    def get_delisted_symbols(self) -> list[Company]:
        """Get delisted/inactive companies from this data source.

        Returns:
            List of Company objects for delisted/inactive companies
        """
        pass

    def is_available(self) -> bool:
        """Check if the data source is working. Override if needed."""
        return True
