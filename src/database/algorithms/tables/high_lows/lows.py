"""SQLAlchemy Lows table for high/low algorithm pattern tracking."""

from __future__ import annotations

from datetime import date as date_type
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.algorithms.base import Base

# Import for relationship type hint
if TYPE_CHECKING:
    from src.database.equities.tables.ticker_history import TickerHistory

# Price multiplier constant: $1.00 = 1,000,000 (6 decimal places, penny = 10,000)
PRICE_MULTIPLIER = 1000000


class Low(Base):
    """SQLAlchemy model for active low patterns in the high/low algorithm.

    This table tracks active price patterns that have not yet completed (rebounded).

    Pattern lifecycle:
    1. Starts when price drops by threshold % from high_start
    2. Tracks lowest point and recovery
    3. Moves to rebounds table when price returns to high_start
    4. Expires after 800 days if not completed

    Prices are stored as integers multiplied by 1,000,000 for precision.
    Example: $63.68 is stored as 63,680,000.

    Thresholds are stored as basis points (integer).
    Example: 20% threshold is stored as 2000.
    """

    __tablename__ = "lows"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Foreign key to ticker_history table
    ticker_history_id: Mapped[int] = mapped_column(
        ForeignKey("ticker_history.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Threshold as basis points (2000 = 20%, 1500 = 15%)
    threshold: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # High start - the peak price before the drop
    high_start_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    high_start_date: Mapped[date_type] = mapped_column(Date, nullable=False)

    # Low threshold - first price at or below high_start * (1 - threshold)
    low_threshold_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    low_threshold_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)

    # Lowest - the actual lowest point in the pattern
    lowest_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    lowest_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)

    # High threshold - recovery point at lowest * (1 + threshold)
    high_threshold_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    high_threshold_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)

    # Threshold crossing counter - tracks number of times high_threshold is crossed
    number_of_high_thresholds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Tracking fields
    last_updated: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    spawned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expired: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # Relationships
    ticker_history: Mapped[TickerHistory] = relationship(
        "TickerHistory", foreign_keys=[ticker_history_id]
    )

    def __repr__(self) -> str:
        """String representation of Low."""
        return (
            f"<Low(id={self.id}, ticker_history_id={self.ticker_history_id}, "
            f"threshold={self.threshold}, last_updated={self.last_updated})>"
        )
