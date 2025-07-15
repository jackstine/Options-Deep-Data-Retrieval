"""Company data model with comprehensive typing."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class Company:
    """Generic company information model."""
    
    ticker: str
    company_name: str
    exchange: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    market_cap: Optional[int] = None
    employees: Optional[int] = None
    website: Optional[str] = None
    description: Optional[str] = None
    source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert company to dictionary for serialization."""
        return {
            'ticker': self.ticker,
            'company_name': self.company_name,
            'exchange': self.exchange,
            'sector': self.sector,
            'industry': self.industry,
            'country': self.country,
            'currency': self.currency,
            'market_cap': self.market_cap,
            'employees': self.employees,
            'website': self.website,
            'description': self.description,
            'source': self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Company:
        """Create Company instance from dictionary."""
        return cls(
            ticker=data['ticker'],
            company_name=data['company_name'],
            exchange=data['exchange'],
            sector=data.get('sector'),
            industry=data.get('industry'),
            country=data.get('country'),
            currency=data.get('currency'),
            market_cap=data.get('market_cap'),
            employees=data.get('employees'),
            website=data.get('website'),
            description=data.get('description'),
            source=data.get('source', '')
        )
    
    def print(self) -> None:
        """Print company information."""
        print(f"\n{self.ticker} - {self.company_name}")
        print(f"  Exchange: {self.exchange}")
        if self.sector:
            print(f"  Sector: {self.sector}")
        if self.industry:
            print(f"  Industry: {self.industry}")
        if self.country:
            print(f"  Country: {self.country}")
        if self.market_cap:
            print(f"  Market Cap: ${self.market_cap:,}")
        if self.employees:
            print(f"  Employees: {self.employees:,}")
        if self.website:
            print(f"  Website: {self.website}")
        print(f"  Source: {self.source}")
    
    def __str__(self) -> str:
        """String representation of company."""
        return f"Company(ticker={self.ticker}, name={self.company_name}, exchange={self.exchange})"
    
    def __repr__(self) -> str:
        """Detailed string representation of company."""
        return self.__str__()