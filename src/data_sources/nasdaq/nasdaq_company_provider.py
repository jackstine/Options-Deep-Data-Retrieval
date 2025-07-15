"""NASDAQ company data source provider with abstraction wrapper."""

from __future__ import annotations
from typing import List, Optional
import logging
import json
from pathlib import Path

from src.data_sources.base.company_base import CompanyDataSourceBase
from src.data_sources.models.company import Company
from src.data_sources.nasdaq.company import get_companies


logger = logging.getLogger(__name__)


class NasdaqCompanyProvider(CompanyDataSourceBase):
    """NASDAQ company data source provider with abstraction wrapper."""
    
    def __init__(self) -> None:
        """Initialize NASDAQ company provider."""
        self._name = "NASDAQ"
        self._companies_cache: List[Company] = []
        self._cache_loaded = False
    
    @property
    def name(self) -> str:
        """Get the name of the data source."""
        return self._name
    
    def fetch_companies(self) -> List[Company]:
        """
        Fetch all available companies from NASDAQ.
        
        Returns:
            List of Company objects with normalized data
            
        Raises:
            Exception: When data retrieval fails
        """
        try:
            logger.info("Fetching companies from NASDAQ API")
            companies = get_companies()
            self._companies_cache = companies
            self._cache_loaded = True
            logger.info(f"Successfully fetched {len(companies)} companies from NASDAQ")
            return companies
            
        except Exception as e:
            logger.error(f"Error fetching companies from NASDAQ: {str(e)}")
            raise
    
    def get_companies_by_exchange(self, exchange: str) -> List[Company]:
        """
        Get companies filtered by exchange.
        
        Args:
            exchange: Exchange name to filter by
            
        Returns:
            List of companies from the specified exchange
        """
        if not self._cache_loaded:
            self.fetch_companies()
        
        return [company for company in self._companies_cache if company.exchange.upper() == exchange.upper()]
    
    def search_companies(self, search_term: str) -> List[Company]:
        """
        Search companies by ticker or company name.
        
        Args:
            search_term: Term to search for in ticker or company name
            
        Returns:
            List of companies matching the search term
        """
        if not self._cache_loaded:
            self.fetch_companies()
        
        search_term_lower = search_term.lower()
        return [
            company for company in self._companies_cache
            if search_term_lower in company.ticker.lower() or search_term_lower in company.company_name.lower()
        ]
    
    def get_company_by_ticker(self, ticker: str) -> Company | None:
        """
        Get a specific company by ticker symbol.
        
        Args:
            ticker: Ticker symbol to search for
            
        Returns:
            Company object if found, None otherwise
        """
        if not self._cache_loaded:
            self.fetch_companies()
        
        for company in self._companies_cache:
            if company.ticker.upper() == ticker.upper():
                return company
        
        return None
    
    def clear_cache(self) -> None:
        """Clear the internal company cache."""
        self._companies_cache = []
        self._cache_loaded = False
        logger.info("Company cache cleared")
    
    def save_to_file(self, file_path: str, companies: Optional[List[Company]] = None) -> bool:
        """
        Save company data to a JSON file.
        
        Args:
            file_path: Path where to save the company data
            companies: Optional list of companies to save. If None, saves all cached companies.
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Use cached companies if none provided
            if companies is None:
                if not self._cache_loaded:
                    self.fetch_companies()
                companies = self._companies_cache
            
            # Convert companies to dictionaries for JSON serialization
            companies_data = [company.to_dict() for company in companies]
            
            # Create directory if it doesn't exist
            file_path_obj = Path(file_path)
            file_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'source': self.name,
                    'company_count': len(companies_data),
                    'companies': companies_data
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved {len(companies_data)} companies to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving companies to file {file_path}: {str(e)}")
            return False
    
    def load_from_file(self, file_path: str) -> List[Company]:
        """
        Load company data from a JSON file.
        
        Args:
            file_path: Path to the file containing company data
            
        Returns:
            List of Company objects loaded from file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"Company data file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate file format
            if 'companies' not in data:
                raise ValueError("Invalid file format: missing 'companies' key")
            
            # Convert dictionaries back to Company objects
            companies = [Company.from_dict(company_data) for company_data in data['companies']]
            
            # Update cache with loaded data
            self._companies_cache = companies
            self._cache_loaded = True
            
            logger.info(f"Successfully loaded {len(companies)} companies from {file_path}")
            return companies
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in file {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading companies from file {file_path}: {str(e)}")
            raise