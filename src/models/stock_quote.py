"""Stock quote data models with comprehensive typing."""

# TODO_JAKE need to confirm this using the YFinance Data....

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class StockQuote:
    """Normalized stock quote data model."""

    symbol: str | None = None
    price: Decimal | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None
    volume: int | None = None
    market_cap: Decimal | None = None
    day_high: Decimal | None = None
    day_low: Decimal | None = None
    previous_close: Decimal | None = None
    open_price: Decimal | None = None
    fifty_two_week_high: Decimal | None = None
    fifty_two_week_low: Decimal | None = None
    pe_ratio: Decimal | None = None
    dividend_yield: Decimal | None = None
    timestamp: datetime | None = None
    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert stock quote to dictionary for serialization."""
        return {
            "symbol": self.symbol,
            "price": float(self.price),
            "bid": float(self.bid) if self.bid is not None else None,
            "ask": float(self.ask) if self.ask is not None else None,
            "volume": self.volume,
            "market_cap": float(self.market_cap)
            if self.market_cap is not None
            else None,
            "day_high": float(self.day_high) if self.day_high is not None else None,
            "day_low": float(self.day_low) if self.day_low is not None else None,
            "previous_close": float(self.previous_close)
            if self.previous_close is not None
            else None,
            "open_price": float(self.open_price)
            if self.open_price is not None
            else None,
            "fifty_two_week_high": float(self.fifty_two_week_high)
            if self.fifty_two_week_high is not None
            else None,
            "fifty_two_week_low": float(self.fifty_two_week_low)
            if self.fifty_two_week_low is not None
            else None,
            "pe_ratio": float(self.pe_ratio) if self.pe_ratio is not None else None,
            "dividend_yield": float(self.dividend_yield)
            if self.dividend_yield is not None
            else None,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StockQuote:
        """Create StockQuote instance from dictionary."""
        return cls(
            symbol=data["symbol"],
            price=Decimal(str(data["price"])),
            bid=Decimal(str(data["bid"])) if data.get("bid") is not None else None,
            ask=Decimal(str(data["ask"])) if data.get("ask") is not None else None,
            volume=data.get("volume", 0),
            market_cap=Decimal(str(data["market_cap"]))
            if data.get("market_cap") is not None
            else None,
            day_high=Decimal(str(data["day_high"]))
            if data.get("day_high") is not None
            else None,
            day_low=Decimal(str(data["day_low"]))
            if data.get("day_low") is not None
            else None,
            previous_close=Decimal(str(data["previous_close"]))
            if data.get("previous_close") is not None
            else None,
            open_price=Decimal(str(data["open_price"]))
            if data.get("open_price") is not None
            else None,
            fifty_two_week_high=Decimal(str(data["fifty_two_week_high"]))
            if data.get("fifty_two_week_high") is not None
            else None,
            fifty_two_week_low=Decimal(str(data["fifty_two_week_low"]))
            if data.get("fifty_two_week_low") is not None
            else None,
            pe_ratio=Decimal(str(data["pe_ratio"]))
            if data.get("pe_ratio") is not None
            else None,
            dividend_yield=Decimal(str(data["dividend_yield"]))
            if data.get("dividend_yield") is not None
            else None,
            timestamp=datetime.fromisoformat(data["timestamp"])
            if isinstance(data["timestamp"], str)
            else data["timestamp"],
            source=data["source"],
        )

    def print(self) -> None:
        """This will print out the stock quote information"""
        # TODO does not print out all the stock quote informaiton.
        print(f"\n{self.symbol}:")
        print(f"  Price: ${self.price}")
        print(f"  Volume: {self.volume:,}")
        print(f"  Day High: ${self.day_high}")
        print(f"  Day Low: ${self.day_low}")
        print(f"  Market Cap: ${self.market_cap}")
        print(f"  Source: {self.source}")
        print(f"  Timestamp: {self.timestamp}")
        print(f"  Price: ${self.price}")
        print(f"  P/E Ratio: {self.pe_ratio}")
        print(f"  52-Week High: ${self.fifty_two_week_high}")
        print(f"  52-Week Low: ${self.fifty_two_week_low}")

    def __str__(self) -> str:
        """String representation of stock quote."""
        return f"StockQuote(symbol={self.symbol}, price={self.price}, volume={self.volume}, source={self.source})"

    def __repr__(self) -> str:
        """Detailed string representation of stock quote."""
        return self.__str__()
