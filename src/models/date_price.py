"""Date and price data model for simple pricing data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass
class DatePrice:
    """Simple date and price data model.

    Used for split-adjusted pricing when only the closing price is needed,
    without the full OHLCV data.
    """

    date: date
    price: Decimal

    def to_dict(self) -> dict[str, Any]:
        """Convert date/price data to dictionary for serialization."""
        return {
            "date": self.date.isoformat(),
            "price": float(self.price),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DatePrice:
        """Create DatePrice instance from dictionary.

        Args:
            data: Dictionary with date and price data

        Returns:
            DatePrice instance
        """
        # Parse date from string if needed
        price_date = data["date"]
        if isinstance(price_date, str):
            price_date = date.fromisoformat(price_date)

        return cls(
            date=price_date,
            price=Decimal(str(data["price"])),
        )

    def __str__(self) -> str:
        """String representation of date/price data."""
        return f"DatePrice(date={self.date}, price={self.price})"

    def __repr__(self) -> str:
        """Detailed string representation of date/price data."""
        return self.__str__()
