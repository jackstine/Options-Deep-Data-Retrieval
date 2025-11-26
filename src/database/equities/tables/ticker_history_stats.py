"""SQLAlchemy TickerHistoryStats table for database operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database.equities.base import Base

# Import for relationship type hint
if TYPE_CHECKING:
    from src.database.equities.tables.ticker_history import TickerHistory

# Price multiplier constant: $1.00 = 1,000,000 (6 decimal places, penny = 10,000)
PRICE_MULTIPLIER = 1000000


class TickerHistoryStats(Base):
    """SQLAlchemy model for ticker history statistics.

    Stores computed statistics for a ticker history including price ranges and data coverage.
    Prices are stored as integers multiplied by 1,000,000 for precision.
    Example: $63.68 is stored as 63,680,000.
    Coverage is stored in basis points: 100% = 10,000, 50% = 5,000.
    """

    __tablename__ = "ticker_history_stats"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to ticker history (unique - one stats record per ticker history)
    ticker_history_id: Mapped[int] = mapped_column(
        ForeignKey("ticker_history.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Data coverage percentage (stored as basis points: 0-10000)
    data_coverage_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Price statistics (stored as BIGINT, multiply by 1,000,000)
    min_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    max_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    average_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    median_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Data quality flags
    has_insufficient_coverage: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", index=True
    )
    low_suspicious_price: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", index=True
    )
    high_suspicious_price: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", index=True
    )

    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    ticker_history: Mapped[TickerHistory] = relationship("TickerHistory")

    # Constraints
    __table_args__ = (
        UniqueConstraint("ticker_history_id", name="uq_ticker_history_stats"),
        {"comment": "Statistical data for ticker histories with prices stored as integers (×1,000,000)"},
    )

    def __repr__(self) -> str:
        """String representation of TickerHistoryStats."""
        return f"<TickerHistoryStats(id={self.id}, ticker_history_id={self.ticker_history_id})>"
