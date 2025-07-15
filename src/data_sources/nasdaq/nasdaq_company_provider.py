"""NASDAQ company data source provider with abstraction wrapper."""

from __future__ import annotations
from typing import List
import logging

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