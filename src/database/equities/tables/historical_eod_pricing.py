"""SQLAlchemy Historical EOD Pricing table for database operations."""

from __future__ import annotations

from datetime import date as date_type
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.equities.base import Base

# Import for relationship type hint
if TYPE_CHECKING:
    from src.database.equities.tables.ticker import Ticker

# Price multiplier constant: $1.00 = 10,000 (4 decimal places)
PRICE_MULTIPLIER = 10000


class HistoricalEodPricing(Base):
    """SQLAlchemy model for historical end-of-day pricing data.

    Prices are stored as integers multiplied by 10,000 for precision.
    Example: $63.68 is stored as 636,800.
    """

    __tablename__ = "historical_eod_pricing"

    # Primary key with auto-incrementing serial ID
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to ticker
    ticker_id: Mapped[int] = mapped_column(
        ForeignKey("tickers.id", ondelete="CASCADE"), nullable=False, index=True
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
    ticker: Mapped[Ticker] = relationship("Ticker")

    # Constraints
    __table_args__ = (
        UniqueConstraint("ticker_id", "date", name="uq_ticker_date"),
        {"comment": "Historical end-of-day pricing data with prices stored as integers (×10,000)"},
    )

    def __repr__(self) -> str:
        """String representation of HistoricalEodPricing."""
        return f"<HistoricalEodPricing(id={self.id}, ticker_id={self.ticker_id}, date={self.date})>"
