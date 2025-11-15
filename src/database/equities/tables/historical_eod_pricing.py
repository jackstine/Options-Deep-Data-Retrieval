"""SQLAlchemy Historical EOD Pricing table for database operations."""

from __future__ import annotations

from datetime import date as date_type
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.equities.base import Base

# Import for relationship type hint
if TYPE_CHECKING:
    from src.database.equities.tables.ticker_history import TickerHistory

# Price multiplier constant: $1.00 = 10,000 (4 decimal places)
PRICE_MULTIPLIER = 10000


class HistoricalEodPricing(Base):
    """SQLAlchemy model for historical end-of-day pricing data.

    Prices are stored as integers multiplied by 10,000 for precision.
    Example: $63.68 is stored as 636,800.
    """

    __tablename__ = "historical_eod_pricing"

    # Foreign key to ticker history
    ticker_id: Mapped[int] = mapped_column(
        ForeignKey("ticker_history.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Trading date
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)

    # OHLC prices (stored as BIGINT, multiply by 10,000)
    open: Mapped[int] = mapped_column(BigInteger, nullable=False)
    high: Mapped[int] = mapped_column(BigInteger, nullable=False)
    low: Mapped[int] = mapped_column(BigInteger, nullable=False)
    close: Mapped[int] = mapped_column(BigInteger, nullable=False)
    adjusted_close: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Volume
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relationships
    ticker_history: Mapped[TickerHistory] = relationship("TickerHistory")

    # Constraints
    __table_args__ = (
        PrimaryKeyConstraint("ticker_id", "date", name="pk_ticker_date"),
        {"comment": "Historical end-of-day pricing data with prices stored as integers (×10,000)"},
    )

    def __repr__(self) -> str:
        """String representation of HistoricalEodPricing."""
        return f"<HistoricalEodPricing(ticker_id={self.ticker_id}, date={self.date})>"
