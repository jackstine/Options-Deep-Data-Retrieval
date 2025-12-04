"""SQLAlchemy Highs table for low/high algorithm pattern tracking."""

from __future__ import annotations

from datetime import date as date_type

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.database.equities.base import Base

# Price multiplier constant: $1.00 = 1,000,000 (6 decimal places, penny = 10,000)
PRICE_MULTIPLIER = 1000000


class High(Base):
    """SQLAlchemy model for active high patterns in the low/high algorithm.

    This table tracks active price patterns that have not yet completed (reversed).

    Pattern lifecycle:
    1. Starts when price rises by threshold % from low_start
    2. Tracks highest point and decline
    3. Moves to reversals table when price returns to low_start
    4. Expires after 800 days if not completed

    Prices are stored as integers multiplied by 1,000,000 for precision.
    Example: $63.68 is stored as 63,680,000.

    Thresholds are stored as basis points (integer).
    Example: 20% threshold is stored as 2000.
    """

    __tablename__ = "highs"
    __table_args__ = {'schema': 'algorithm'}

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Reference to ticker_history table (in equities database - no FK constraint)
    ticker_history_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="References ticker_history.id in equities database (no FK constraint across databases)",
    )

    # Threshold as basis points (2000 = 20%, 1500 = 15%)
    threshold: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Low start - the trough price before the rise
    low_start_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    low_start_date: Mapped[date_type] = mapped_column(Date, nullable=False)

    # High threshold - first price at or above low_start * (1 + threshold)
    high_threshold_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    high_threshold_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)

    # Highest - the actual highest point in the pattern
    highest_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    highest_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)

    # Low threshold - decline point at highest / (1 + threshold)
    low_threshold_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    low_threshold_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)

    # Threshold crossing counter - tracks number of times low_threshold is crossed
    number_of_low_thresholds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Tracking fields
    last_updated: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    spawned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expired: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # Note: No SQLAlchemy relationship to TickerHistory - it's in a different database (equities)
    # Use ticker_history_id foreign key for joins at the application level

    def __repr__(self) -> str:
        """String representation of High."""
        return (
            f"<High(id={self.id}, ticker_history_id={self.ticker_history_id}, "
            f"threshold={self.threshold}, last_updated={self.last_updated})>"
        )
