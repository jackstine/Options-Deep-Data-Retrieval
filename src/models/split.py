"""Stock split data model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass
class Split:
    """Stock split data model.

    Split ratios are stored as strings in the format "numerator/denominator".
    Example: "2.000000/1.000000" represents a 2-for-1 split.

    Note: Uses ticker_history_id (not ticker_id) to support both active
    and delisted symbols. The ticker_history table tracks all symbols,
    while the ticker table only contains currently active symbols.
    """

    date: date | None = None
    split_ratio: str | None = None
    ticker_history_id: int | None = None
    symbol: str | None = None  # For display purposes only, not stored in DB
    id: int | None = None

    def get_split_ratio(self) -> Decimal:
        """Parse and calculate the split ratio as a decimal.

        Example: "2.000000/1.000000" returns Decimal("2.0")
        Example: "1.000000/10.000000" returns Decimal("0.1")

        Returns:
            Decimal representation of the split ratio

        Raises:
            ValueError: If split_ratio format is invalid
        """
        try:
            parts = self.split_ratio.split("/")
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid split ratio format: {self.split_ratio}. Expected 'numerator/denominator'"
                )

            numerator = Decimal(parts[0].strip())
            denominator = Decimal(parts[1].strip())

            if denominator == 0:
                raise ValueError("Denominator cannot be zero in split ratio")

            return numerator / denominator

        except (ValueError, IndexError) as e:
            raise ValueError(f"Failed to parse split ratio '{self.split_ratio}': {e}") from e

    def to_dict(self) -> dict[str, Any]:
        """Convert split data to dictionary for serialization."""
        return {
            "id": self.id,
            "ticker_history_id": self.ticker_history_id,
            "symbol": self.symbol,
            "date": self.date.isoformat(),
            "split_ratio": self.split_ratio,
            "calculated_ratio": float(self.get_split_ratio()),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Split:
        """Create Split instance from dictionary.

        Args:
            data: Dictionary with split data

        Returns:
            Split instance
        """
        # Parse date from string if needed
        split_date = data["date"]
        if isinstance(split_date, str):
            split_date = date.fromisoformat(split_date)

        return cls(
            id=data.get("id"),
            ticker_history_id=data.get("ticker_history_id"),
            symbol=data.get("symbol"),
            date=split_date,
            split_ratio=str(data["split_ratio"]),
        )

    def __str__(self) -> str:
        """String representation of split data."""
        ratio = self.get_split_ratio()
        symbol_part = f"{self.symbol} " if self.symbol else ""
        return f"Split({symbol_part}{self.date}, ratio={self.split_ratio} [{ratio}])"

    def __repr__(self) -> str:
        """Detailed string representation of split data."""
        return self.__str__()
