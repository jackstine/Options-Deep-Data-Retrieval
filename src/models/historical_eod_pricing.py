"""Historical end-of-day pricing data model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass
class HistoricalEndOfDayPricing:
    """Historical end-of-day OHLCV price data model."""

    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adjusted_close: Decimal
    volume: int
    id: int | None = None
    symbol: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert pricing data to dictionary for serialization."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "date": self.date.isoformat(),
            "open": float(self.open),
            "high": float(self.high),
            "low": float(self.low),
            "close": float(self.close),
            "adjusted_close": float(self.adjusted_close),
            "volume": self.volume,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HistoricalEndOfDayPricing:
        """Create HistoricalEndOfDayPricing instance from dictionary.

        Args:
            data: Dictionary with pricing data

        Returns:
            HistoricalEndOfDayPricing instance
        """
        # Parse date from string if needed
        pricing_date = data["date"]
        if isinstance(pricing_date, str):
            pricing_date = date.fromisoformat(pricing_date)

        return cls(
            id=data.get("id"),
            symbol=data.get("symbol", ""),
            date=pricing_date,
            open=Decimal(str(data["open"])),
            high=Decimal(str(data["high"])),
            low=Decimal(str(data["low"])),
            close=Decimal(str(data["close"])),
            adjusted_close=Decimal(str(data["adjusted_close"])),
            volume=int(data["volume"]),
        )

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
