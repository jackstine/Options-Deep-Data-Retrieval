"""SQLAlchemy Rebounds table for completed high/low patterns."""

from __future__ import annotations

from datetime import date as date_type

from sqlalchemy import BigInteger, Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.database.equities.base import Base

# Price multiplier constant: $1.00 = 1,000,000 (6 decimal places, penny = 10,000)
PRICE_MULTIPLIER = 1000000


class Rebound(Base):
    """SQLAlchemy model for completed rebound patterns in the high/low algorithm.

    This table stores completed price patterns where the price has successfully
    rebounded back to the high_start price after dropping by the threshold %.

    A pattern is considered complete when:
    1. Price dropped by threshold % from high_start (creating low_threshold)
    2. Price recovered by threshold % from lowest (creating high_threshold)
    3. Price returned to or exceeded high_start (creating rebound)

    Prices are stored as integers multiplied by 1,000,000 for precision.
    Example: $63.68 is stored as 63,680,000.

    Thresholds are stored as basis points (integer).
    Example: 20% threshold is stored as 2000.
    """

    __tablename__ = "rebounds"
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

    # High start - the peak price before the drop
    high_start_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    high_start_date: Mapped[date_type] = mapped_column(Date, nullable=False)

    # Low threshold - first price at or below high_start * (1 - threshold)
    low_threshold_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    low_threshold_date: Mapped[date_type] = mapped_column(
        Date, nullable=False, index=True
    )

    # Lowest - the actual lowest point in the pattern
    lowest_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    lowest_date: Mapped[date_type] = mapped_column(Date, nullable=False)

    # High threshold - recovery point at lowest * (1 + threshold)
    high_threshold_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    high_threshold_date: Mapped[date_type] = mapped_column(Date, nullable=False)

    # Rebound - price returned to high_start
    rebound_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rebound_date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)

    # Threshold crossing counter - tracks number of times high_threshold was crossed
    number_of_high_thresholds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Note: No SQLAlchemy relationship to TickerHistory - it's in a different database (equities)
    # Use ticker_history_id foreign key for joins at the application level

    def __repr__(self) -> str:
        """String representation of Rebound."""
        return (
            f"<Rebound(id={self.id}, ticker_history_id={self.ticker_history_id}, "
            f"threshold={self.threshold}, rebound_date={self.rebound_date})>"
        )
