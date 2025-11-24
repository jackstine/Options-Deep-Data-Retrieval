"""End-of-day split-adjusted pricing data model with full OHLCV data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass
class EODSplitAdjustedPricing:
    """End-of-day split-adjusted OHLCV price data model.

    Contains full open, high, low, close, volume, and adjusted close data
    with split adjustments applied. Used when detailed OHLCV data is needed
    rather than just closing prices.
    """

    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    adjusted_close: Decimal

    def to_dict(self) -> dict[str, Any]:
        """Convert pricing data to dictionary for serialization."""
        return {
            "date": self.date.isoformat(),
            "open": float(self.open),
            "high": float(self.high),
            "low": float(self.low),
            "close": float(self.close),
            "volume": self.volume,
            "adjusted_close": float(self.adjusted_close),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EODSplitAdjustedPricing:
        """Create EODSplitAdjustedPricing instance from dictionary.

        Args:
            data: Dictionary with pricing data

        Returns:
            EODSplitAdjustedPricing instance
        """
        # Parse date from string if needed
        pricing_date = data["date"]
        if isinstance(pricing_date, str):
            pricing_date = date.fromisoformat(pricing_date)

        return cls(
            date=pricing_date,
            open=Decimal(str(data["open"])),
            high=Decimal(str(data["high"])),
            low=Decimal(str(data["low"])),
            close=Decimal(str(data["close"])),
            volume=int(data["volume"]),
            adjusted_close=Decimal(str(data["adjusted_close"])),
        )

    def __str__(self) -> str:
        """String representation of pricing data."""
        return f"EODSplitAdjustedPricing(date={self.date}, close={self.close}, volume={self.volume})"

    def __repr__(self) -> str:
        """Detailed string representation of pricing data."""
        return self.__str__()
