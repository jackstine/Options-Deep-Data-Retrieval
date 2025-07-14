"""Stock quote data models with comprehensive typing."""

# TODO_JAKE need to confirm this using the YFinance Data....

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal


@dataclass
class StockQuote:
    """Normalized stock quote data model."""
    
    symbol: str
    price: Decimal
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    volume: int = 0
    market_cap: Optional[Decimal] = None
    day_high: Optional[Decimal] = None
    day_low: Optional[Decimal] = None
    previous_close: Optional[Decimal] = None
    open_price: Optional[Decimal] = None
    fifty_two_week_high: Optional[Decimal] = None
    fifty_two_week_low: Optional[Decimal] = None
    pe_ratio: Optional[Decimal] = None
    dividend_yield: Optional[Decimal] = None
    timestamp: datetime = datetime.now()
    source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stock quote to dictionary for serialization."""
        return {
            'symbol': self.symbol,
            'price': float(self.price),
            'bid': float(self.bid) if self.bid is not None else None,
            'ask': float(self.ask) if self.ask is not None else None,
            'volume': self.volume,
            'market_cap': float(self.market_cap) if self.market_cap is not None else None,
            'day_high': float(self.day_high) if self.day_high is not None else None,
            'day_low': float(self.day_low) if self.day_low is not None else None,
            'previous_close': float(self.previous_close) if self.previous_close is not None else None,
            'open_price': float(self.open_price) if self.open_price is not None else None,
            'fifty_two_week_high': float(self.fifty_two_week_high) if self.fifty_two_week_high is not None else None,
            'fifty_two_week_low': float(self.fifty_two_week_low) if self.fifty_two_week_low is not None else None,
            'pe_ratio': float(self.pe_ratio) if self.pe_ratio is not None else None,
            'dividend_yield': float(self.dividend_yield) if self.dividend_yield is not None else None,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StockQuote:
        """Create StockQuote instance from dictionary."""
        return cls(
            symbol=data['symbol'],
            price=Decimal(str(data['price'])),
            bid=Decimal(str(data['bid'])) if data.get('bid') is not None else None,
            ask=Decimal(str(data['ask'])) if data.get('ask') is not None else None,
            volume=data.get('volume', 0),
            market_cap=Decimal(str(data['market_cap'])) if data.get('market_cap') is not None else None,
            day_high=Decimal(str(data['day_high'])) if data.get('day_high') is not None else None,
            day_low=Decimal(str(data['day_low'])) if data.get('day_low') is not None else None,
            previous_close=Decimal(str(data['previous_close'])) if data.get('previous_close') is not None else None,
            open_price=Decimal(str(data['open_price'])) if data.get('open_price') is not None else None,
            fifty_two_week_high=Decimal(str(data['fifty_two_week_high'])) if data.get('fifty_two_week_high') is not None else None,
            fifty_two_week_low=Decimal(str(data['fifty_two_week_low'])) if data.get('fifty_two_week_low') is not None else None,
            pe_ratio=Decimal(str(data['pe_ratio'])) if data.get('pe_ratio') is not None else None,
            dividend_yield=Decimal(str(data['dividend_yield'])) if data.get('dividend_yield') is not None else None,
            timestamp=datetime.fromisoformat(data['timestamp']) if isinstance(data['timestamp'], str) else data['timestamp'],
            source=data['source']
        )
    
    def __str__(self) -> str:
        """String representation of stock quote."""
        return f"StockQuote(symbol={self.symbol}, price={self.price}, volume={self.volume}, source={self.source})"
    
    def __repr__(self) -> str:
        """Detailed string representation of stock quote."""
        return self.__str__()