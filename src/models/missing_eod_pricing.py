"""Missing end-of-day pricing data model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass
class MissingEndOfDayPricing:
    """Missing end-of-day pricing data model.

    Tracks which dates are missing pricing data for specific tickers.
    Used to identify and fill gaps in historical pricing data.
    """

    company_id: int
    ticker_history_id: int
    date: date

    def to_dict(self) -> dict[str, Any]:
        """Convert missing pricing data to dictionary for serialization."""
        return {
            "company_id": self.company_id,
            "ticker_history_id": self.ticker_history_id,
            "date": self.date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MissingEndOfDayPricing:
        """Create MissingEndOfDayPricing instance from dictionary.

        Args:
            data: Dictionary with missing pricing data

        Returns:
            MissingEndOfDayPricing instance
        """
        # Parse date from string if needed
        pricing_date = data["date"]
        if isinstance(pricing_date, str):
            pricing_date = date.fromisoformat(pricing_date)

        return cls(
            company_id=int(data["company_id"]),
            ticker_history_id=int(data["ticker_history_id"]),
            date=pricing_date,
        )

    def print(self) -> None:
        """Print missing pricing information."""
        print(
            f"\nMissing pricing: Company ID {self.company_id}, Ticker History ID {self.ticker_history_id}, Date {self.date}"
        )

    def __str__(self) -> str:
        """String representation of missing pricing data."""
        return f"MissingEndOfDayPricing(company_id={self.company_id}, ticker_history_id={self.ticker_history_id}, date={self.date})"

    def __repr__(self) -> str:
        """Detailed string representation of missing pricing data."""
        return self.__str__()
