"""Abstract base class for company data sources."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path
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
    
    @abstractmethod
    def save_to_file(self, file_path: str, companies: Optional[List[Company]] = None) -> bool:
        """
        Save company data to a file.
        
        Args:
            file_path: Path where to save the company data
            companies: Optional list of companies to save. If None, saves all cached companies.
            
        Returns:
            True if save was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def load_from_file(self, file_path: str) -> List[Company]:
        """
        Load company data from a file.
        
        Args:
            file_path: Path to the file containing company data
            
        Returns:
            List of Company objects loaded from file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
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