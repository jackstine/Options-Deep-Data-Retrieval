"""TickerHistory data model with temporal tracking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass
class TickerHistory:
    """Historical ticker symbol model with temporal validity tracking."""

    symbol: str | None = None
    company_id: int | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert ticker history to dictionary for serialization."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "company_id": self.company_id,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TickerHistory:
        """Create TickerHistory instance from dictionary."""
        # Parse dates from ISO format strings
        valid_from = None  # Default
        if data.get("valid_from"):
            if isinstance(data["valid_from"], str):
                valid_from = date.fromisoformat(data["valid_from"])
            else:
                valid_from = data["valid_from"]

        valid_to = None
        if data.get("valid_to"):
            if isinstance(data["valid_to"], str):
                valid_to = date.fromisoformat(data["valid_to"])
            else:
                valid_to = data["valid_to"]

        return cls(
            id=data.get("id"),
            symbol=data["symbol"],
            company_id=data["company_id"],
            valid_from=valid_from,
            valid_to=valid_to,
        )

    def is_valid_on_date(self, check_date: date) -> bool:
        """Check if ticker was valid on a specific date.

        Args:
            check_date: Date to check validity for

        Returns:
            True if ticker was valid on the given date
        """
        # If valid_from is None, assume valid from beginning of time
        if self.valid_from is not None and check_date < self.valid_from:
            return False
        if self.valid_to is not None and check_date > self.valid_to:
            return False
        return True

    def is_currently_valid(self) -> bool:
        """Check if ticker is currently valid based on date range.

        Note: This only checks temporal validity. To check if the company
        is active, use the DB model's is_currently_valid() method.

        Returns:
            True if ticker is currently valid by date
        """
        today = date.today()
        return self.is_valid_on_date(today)

    def get_validity_period_str(self) -> str:
        """Get human-readable validity period string.

        Returns:
            String representation of validity period
        """
        start = self.valid_from.strftime("%Y-%m-%d") if self.valid_from else "unknown"
        if self.valid_to:
            end = self.valid_to.strftime("%Y-%m-%d")
            return f"{start} to {end}"
        else:
            return f"{start} to present"

    def print(self) -> None:
        """Print ticker history information."""
        print(f"\n{self.symbol} (Company ID: {self.company_id})")
        print(f"  Valid Period: {self.get_validity_period_str()}")
        if self.id:
            print(f"  ID: {self.id}")

    def __str__(self) -> str:
        """String representation of ticker history."""
        return f"TickerHistory(symbol={self.symbol}, company_id={self.company_id}, valid_from={self.valid_from}, valid_to={self.valid_to})"

    def __repr__(self) -> str:
        """Detailed string representation of ticker history."""
        return self.__str__()
