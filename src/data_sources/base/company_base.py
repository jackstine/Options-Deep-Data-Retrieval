"""Abstract base class for company data sources."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from src.data_sources.models.company import Company


class CompanyDataSourceBase(ABC):
    """Abstract base class for all company data source providers."""
    
    @abstractmethod
    def fetch_companies(self) -> List[Company]:
        """
        Fetch all available companies.
        
        Returns:
            List of Company objects with normalized data
            
        Raises:
            DataSourceError: When data retrieval fails
            ValidationError: When data validation fails
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the data source.
        
        Returns:
            String identifier for the data source
        """
        pass