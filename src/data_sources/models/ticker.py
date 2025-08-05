"""Ticker data model for currently active tickers."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class Ticker:
    """Currently active ticker symbol model."""
    
    symbol: str
    company_id: Optional[int] = None # not required because it can be retrieved from sources that have just the symbol
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ticker to dictionary for serialization."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'company_id': self.company_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Ticker:
        """Create Ticker instance from dictionary."""
        return cls(
            id=data.get('id'),
            symbol=data['symbol'],
            company_id=data['company_id']
        )
    
    def print(self) -> None:
        """Print ticker information."""
        print(f"\n{self.symbol} (Company ID: {self.company_id})")
        if self.id:
            print(f"  ID: {self.id}")
    
    def __str__(self) -> str:
        """String representation of ticker."""
        return f"Ticker(symbol={self.symbol}, company_id={self.company_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of ticker."""
        return self.__str__()