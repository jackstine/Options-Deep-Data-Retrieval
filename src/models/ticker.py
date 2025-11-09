"""Ticker data model for currently active tickers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.database.equities.tables.ticker import Ticker as DBTicker


@dataclass
class Ticker:
    """Currently active ticker symbol model."""

    symbol: str
    company_id: int | None = (
        None  # not required because it can be retrieved from sources that have just the symbol
    )
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert ticker to dictionary for serialization."""
        return {"id": self.id, "symbol": self.symbol, "company_id": self.company_id}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Ticker:
        """Create Ticker instance from dictionary."""
        return cls(
            id=data.get("id"), symbol=data["symbol"], company_id=data["company_id"]
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

    def to_db_model(self) -> DBTicker:
        """Convert data model to SQLAlchemy database model.

        Returns:
            DBTicker: SQLAlchemy model instance ready for database operations
        """
        from src.database.equities.tables.ticker import Ticker as DBTicker

        return DBTicker(symbol=self.symbol, company_id=self.company_id)

    @classmethod
    def from_db_model(cls, db_model: DBTicker) -> Ticker:
        """Create data model from SQLAlchemy database model.

        Args:
            db_model: SQLAlchemy Ticker instance from database

        Returns:
            Ticker: Data model instance
        """
        return cls(id=db_model.id, symbol=db_model.symbol, company_id=db_model.company_id)

    def update_db_model(self, db_model: DBTicker) -> None:
        """Update existing SQLAlchemy database model with data from this model.

        Args:
            db_model: SQLAlchemy Ticker instance to update
        """
        db_model.symbol = self.symbol
        if self.company_id is not None:
            db_model.company_id = self.company_id
