"""SQLAlchemy Splits table for database operations."""

from __future__ import annotations

from datetime import date as date_type
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.equities.base import Base

# Import for relationship type hint
if TYPE_CHECKING:
    from src.database.equities.tables.ticker_history import TickerHistory


class Split(Base):
    """SQLAlchemy model for stock split data.

    Split ratios are stored as strings in the format received from the API.
    Example: "2.000000/1.000000" represents a 2-for-1 split.

    Note: This table references ticker_history (not ticker) to support both
    active and delisted symbols. The ticker table only contains currently
    active trading symbols, while ticker_history tracks all historical symbols.
    """

    __tablename__ = "splits"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to ticker_history table (supports both active and delisted symbols)
    ticker_history_id: Mapped[int] = mapped_column(
        ForeignKey("ticker_history.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Split date
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)

    # Split ratio (e.g., "2.000000/1.000000")
    split_ratio: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    ticker_history: Mapped[TickerHistory] = relationship("TickerHistory")

    # Constraints
    __table_args__ = (
        UniqueConstraint("ticker_history_id", "date", name="uq_splits_ticker_history_date"),
        {"comment": "Stock split data with split ratios stored as strings (e.g., '2.000000/1.000000')"},
    )

    def __repr__(self) -> str:
        """String representation of Split."""
        return f"<Split(ticker_history_id={self.ticker_history_id}, date={self.date}, split_ratio={self.split_ratio})>"
