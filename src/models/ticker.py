"""Ticker data model for currently active tickers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Ticker:
    """Currently active ticker symbol model.

    Note: This model represents ONLY currently active/trading symbols.
    All tickers must have a corresponding ticker_history record referenced by ticker_history_id.
    """

    symbol: str | None = None
    company_id: int | None = (
        None  # not required because it can be retrieved from sources that have just the symbol
    )
    ticker_history_id: int | None = None  # Required for database, references ticker_history table
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert ticker to dictionary for serialization."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "company_id": self.company_id,
            "ticker_history_id": self.ticker_history_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Ticker:
        """Create Ticker instance from dictionary."""
        return cls(
            id=data.get("id"),
            symbol=data["symbol"],
            company_id=data["company_id"],
            ticker_history_id=data.get("ticker_history_id"),
        )

    def print(self) -> None:
        """Print ticker information."""
        print(f"\n{self.symbol} (Company ID: {self.company_id})")
        if self.id:
            print(f"  ID: {self.id}")

    def __str__(self) -> str:
        """String representation of ticker."""
        return f"Ticker(symbol={self.symbol}, company_id={self.company_id})"

    def __repr__(self) -> str:
        """Detailed string representation of ticker."""
        return self.__str__()
