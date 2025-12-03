"""Misplaced end-of-day pricing data model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from src.database.equities.enums import DataSourceEnum


@dataclass
class MisplacedEndOfDayPricing:
    """Misplaced end-of-day OHLCV price data model.

    Stores pricing data that does not currently have an association with
    ticker_history records. Used for staging data before matching to
    appropriate ticker records.
    """

    symbol: str
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adjusted_close: Decimal
    volume: int
    source: DataSourceEnum

    def to_dict(self) -> dict[str, Any]:
        """Convert pricing data to dictionary for serialization."""
        return {
            "symbol": self.symbol,
            "date": self.date.isoformat(),
            "open": float(self.open),
            "high": float(self.high),
            "low": float(self.low),
            "close": float(self.close),
            "adjusted_close": float(self.adjusted_close),
            "volume": self.volume,
            "source": str(self.source),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MisplacedEndOfDayPricing:
        """Create MisplacedEndOfDayPricing instance from dictionary.

        Args:
            data: Dictionary with pricing data

        Returns:
            MisplacedEndOfDayPricing instance
        """
        # Parse date from string if needed
        pricing_date = data["date"]
        if isinstance(pricing_date, str):
            pricing_date = date.fromisoformat(pricing_date)

        # Parse source from string if needed
        source = data["source"]
        if isinstance(source, str):
            source = DataSourceEnum(source)

        return cls(
            symbol=data["symbol"],
            date=pricing_date,
            open=Decimal(str(data["open"])),
            high=Decimal(str(data["high"])),
            low=Decimal(str(data["low"])),
            close=Decimal(str(data["close"])),
            adjusted_close=Decimal(str(data["adjusted_close"])),
            volume=int(data["volume"]),
            source=source,
        )

    def print(self) -> None:
        """Print pricing information."""
        print(f"\n{self.symbol} - {self.date}")
        print(f"  Open: ${self.open:.2f}")
        print(f"  High: ${self.high:.2f}")
        print(f"  Low: ${self.low:.2f}")
        print(f"  Close: ${self.close:.2f}")
        print(f"  Adjusted Close: ${self.adjusted_close:.2f}")
        print(f"  Volume: {self.volume:,}")

    def __str__(self) -> str:
        """String representation of pricing data."""
        return f"MisplacedEndOfDayPricing(symbol={self.symbol}, date={self.date}, close={self.close})"

    def __repr__(self) -> str:
        """Detailed string representation of pricing data."""
        return self.__str__()
