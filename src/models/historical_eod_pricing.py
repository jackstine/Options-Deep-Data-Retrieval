"""Historical end-of-day pricing data model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass
class HistoricalEndOfDayPricing:
    """Historical end-of-day OHLCV price data model.

    Note: Uses ticker_history_id (not ticker_id) to support both active
    and delisted symbols. The ticker_history table tracks all symbols,
    while the ticker table only contains currently active symbols.
    """

    date: date | None = None
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    close: Decimal | None = None
    adjusted_close: Decimal | None = None
    volume: int | None = None
    ticker_history_id: int | None = None  # References ticker_history table
    symbol: str | None = None  # For display purposes only, not stored in DB

    def to_dict(self) -> dict[str, Any]:
        """Convert pricing data to dictionary for serialization."""
        return {
            "ticker_history_id": self.ticker_history_id,
            "symbol": self.symbol,
            "date": self.date.isoformat(),
            "open": float(self.open),
            "high": float(self.high),
            "low": float(self.low),
            "close": float(self.close),
            "adjusted_close": float(self.adjusted_close),
            "volume": self.volume,
        }

    def print(self) -> None:
        """Print pricing information."""
        print(f"\n{self.symbol if self.symbol else 'Price Data'} - {self.date}")
        print(f"  Open: ${self.open:.2f}")
        print(f"  High: ${self.high:.2f}")
        print(f"  Low: ${self.low:.2f}")
        print(f"  Close: ${self.close:.2f}")
        print(f"  Adjusted Close: ${self.adjusted_close:.2f}")
        print(f"  Volume: {self.volume:,}")

    def __str__(self) -> str:
        """String representation of pricing data."""
        return f"HistoricalEndOfDayPricing(date={self.date}, close={self.close}, volume={self.volume})"

    def __repr__(self) -> str:
        """Detailed string representation of pricing data."""
        return self.__str__()
