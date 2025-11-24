"""SQLAlchemy Misplaced EOD Pricing table for database operations."""

from __future__ import annotations

from datetime import date as date_type

from sqlalchemy import BigInteger, Date, Enum, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.equities.base import Base
from src.database.equities.enums import DataSourceEnum

# Price multiplier constant: $1.00 = 1,000,000 (6 decimal places, penny = 10,000)
PRICE_MULTIPLIER = 1000000


class MisplacedEodPricing(Base):
    """SQLAlchemy model for misplaced end-of-day pricing data.

    This table stores pricing data that does not currently have an association
    with ticker_history records. Prices are stored as integers multiplied by
    1,000,000 for precision. Example: $63.68 is stored as 63,680,000.

    Note: This table has no foreign keys as it stores data before matching
    to ticker_history records.
    """

    __tablename__ = "misplaced_eod_pricing"

    # Stock symbol (no foreign key - data not yet associated)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Trading date
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)

    # OHLC prices (stored as BIGINT, multiply by 1,000,000)
    open: Mapped[int] = mapped_column(BigInteger, nullable=False)
    high: Mapped[int] = mapped_column(BigInteger, nullable=False)
    low: Mapped[int] = mapped_column(BigInteger, nullable=False)
    close: Mapped[int] = mapped_column(BigInteger, nullable=False)
    adjusted_close: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Volume
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Data source tracking
    source: Mapped[DataSourceEnum] = mapped_column(
        Enum(DataSourceEnum, native_enum=True, name="data_source_enum"),
        nullable=False,
    )

    # Constraints
    __table_args__ = (
        PrimaryKeyConstraint("symbol", "date", name="pk_misplaced_symbol_date"),
        {
            "comment": "Misplaced EOD pricing data without ticker_history associations (prices stored as integers ×1,000,000)"
        },
    )

    def __repr__(self) -> str:
        """String representation of MisplacedEodPricing."""
        return f"<MisplacedEodPricing(symbol='{self.symbol}', date={self.date})>"
