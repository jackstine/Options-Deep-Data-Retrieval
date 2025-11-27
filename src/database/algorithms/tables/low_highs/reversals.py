"""SQLAlchemy Reversals table for completed low/high patterns."""

from __future__ import annotations

from datetime import date as date_type
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.algorithms.base import Base

# Import for relationship type hint
if TYPE_CHECKING:
    from src.database.equities.tables.ticker_history import TickerHistory

# Price multiplier constant: $1.00 = 1,000,000 (6 decimal places, penny = 10,000)
PRICE_MULTIPLIER = 1000000


class Reversal(Base):
    """SQLAlchemy model for completed reversal patterns in the low/high algorithm.

    This table stores completed price patterns where the price has successfully
    reversed back to the low_start price after rising by the threshold %.

    A pattern is considered complete when:
    1. Price rose by threshold % from low_start (creating high_threshold)
    2. Price declined by threshold % from highest (creating low_threshold)
    3. Price returned to or fell below low_start (creating reversal)

    Prices are stored as integers multiplied by 1,000,000 for precision.
    Example: $63.68 is stored as 63,680,000.

    Thresholds are stored as basis points (integer).
    Example: 20% threshold is stored as 2000.
    """

    __tablename__ = "reversals"

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

    # Low start - the trough price before the rise
    low_start_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    low_start_date: Mapped[date_type] = mapped_column(Date, nullable=False)

    # High threshold - first price at or above low_start * (1 + threshold)
    high_threshold_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    high_threshold_date: Mapped[date_type] = mapped_column(
        Date, nullable=False, index=True
    )

    # Highest - the actual highest point in the pattern
    highest_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    highest_date: Mapped[date_type] = mapped_column(Date, nullable=False)

    # Low threshold - decline point at highest / (1 + threshold)
    low_threshold_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    low_threshold_date: Mapped[date_type] = mapped_column(Date, nullable=False)

    # Reversal - price returned to low_start
    reversal_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reversal_date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)

    # Threshold crossing counter - tracks number of times low_threshold was crossed
    number_of_low_thresholds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Relationships
    ticker_history: Mapped[TickerHistory] = relationship(
        "TickerHistory", foreign_keys=[ticker_history_id]
    )

    def __repr__(self) -> str:
        """String representation of Reversal."""
        return (
            f"<Reversal(id={self.id}, ticker_history_id={self.ticker_history_id}, "
            f"threshold={self.threshold}, reversal_date={self.reversal_date})>"
        )
