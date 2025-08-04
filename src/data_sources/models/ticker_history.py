"""TickerHistory data model with temporal tracking."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Dict, Any, Optional


@dataclass
class TickerHistory:
    """Historical ticker symbol model with temporal validity tracking."""
    
    symbol: str
    company_id: int
    valid_from: date = date(1900, 1, 1)
    valid_to: Optional[date] = None
    active: bool = True
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ticker history to dictionary for serialization."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'company_id': self.company_id,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_to': self.valid_to.isoformat() if self.valid_to else None,
            'active': self.active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TickerHistory:
        """Create TickerHistory instance from dictionary."""
        # Parse dates from ISO format strings
        valid_from = date(1900, 1, 1)  # Default
        if data.get('valid_from'):
            if isinstance(data['valid_from'], str):
                valid_from = date.fromisoformat(data['valid_from'])
            else:
                valid_from = data['valid_from']
        
        valid_to = None
        if data.get('valid_to'):
            if isinstance(data['valid_to'], str):
                valid_to = date.fromisoformat(data['valid_to'])
            else:
                valid_to = data['valid_to']
        
        return cls(
            id=data.get('id'),
            symbol=data['symbol'],
            company_id=data['company_id'],
            valid_from=valid_from,
            valid_to=valid_to,
            active=data.get('active', True)
        )
    
    def is_valid_on_date(self, check_date: date) -> bool:
        """
        Check if ticker was valid on a specific date.
        
        Args:
            check_date: Date to check validity for
            
        Returns:
            True if ticker was valid on the given date
        """
        if check_date < self.valid_from:
            return False
        if self.valid_to is not None and check_date > self.valid_to:
            return False
        return True
    
    def is_currently_valid(self) -> bool:
        """
        Check if ticker is currently valid.
        
        Returns:
            True if ticker is currently valid
        """
        today = date.today()
        return self.is_valid_on_date(today) and self.active
    
    def get_validity_period_str(self) -> str:
        """
        Get human-readable validity period string.
        
        Returns:
            String representation of validity period
        """
        start = self.valid_from.strftime("%Y-%m-%d")
        if self.valid_to:
            end = self.valid_to.strftime("%Y-%m-%d")
            return f"{start} to {end}"
        else:
            return f"{start} to present"
    
    def print(self) -> None:
        """Print ticker history information."""
        print(f"\n{self.symbol} (Company ID: {self.company_id})")
        print(f"  Valid Period: {self.get_validity_period_str()}")
        print(f"  Active: {'Yes' if self.active else 'No'}")
        if self.id:
            print(f"  ID: {self.id}")
    
    def __str__(self) -> str:
        """String representation of ticker history."""
        return f"TickerHistory(symbol={self.symbol}, company_id={self.company_id}, valid_from={self.valid_from}, valid_to={self.valid_to})"
    
    def __repr__(self) -> str:
        """Detailed string representation of ticker history."""
        return self.__str__()