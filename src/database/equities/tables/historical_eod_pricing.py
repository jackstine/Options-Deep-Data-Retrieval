"""SQLAlchemy Historical EOD Pricing table for database operations."""

from __future__ import annotations

from datetime import date as date_type
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data_sources.models.historical_eod_pricing import (
    HistoricalEndOfDayPricing as HistoricalEodPricingDataModel,
)
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

    def to_data_model(self) -> HistoricalEodPricingDataModel:
        """Convert SQLAlchemy model to data model.

        Returns:
            HistoricalEodPricingDataModel instance with prices as Decimals
        """
        return HistoricalEodPricingDataModel(
            id=self.id,
            date=self.date,
            open=Decimal(self.open) / PRICE_MULTIPLIER,
            high=Decimal(self.high) / PRICE_MULTIPLIER,
            low=Decimal(self.low) / PRICE_MULTIPLIER,
            close=Decimal(self.close) / PRICE_MULTIPLIER,
            adjusted_close=Decimal(self.adjusted_close) / PRICE_MULTIPLIER,
            volume=self.volume,
        )

    @classmethod
    def from_data_model(
        cls, pricing_data: HistoricalEodPricingDataModel, ticker_id: int
    ) -> HistoricalEodPricing:
        """Create SQLAlchemy model from data model.

        Args:
            pricing_data: HistoricalEodPricingDataModel instance
            ticker_id: ID of the ticker this pricing data belongs to

        Returns:
            HistoricalEodPricing SQLAlchemy model instance
        """
        return cls(
            ticker_id=ticker_id,
            date=pricing_data.date,
            open=int(pricing_data.open * PRICE_MULTIPLIER),
            high=int(pricing_data.high * PRICE_MULTIPLIER),
            low=int(pricing_data.low * PRICE_MULTIPLIER),
            close=int(pricing_data.close * PRICE_MULTIPLIER),
            adjusted_close=int(pricing_data.adjusted_close * PRICE_MULTIPLIER),
            volume=pricing_data.volume,
        )

    def update_from_data_model(
        self, pricing_data: HistoricalEodPricingDataModel
    ) -> None:
        """Update existing SQLAlchemy model from data model.

        Args:
            pricing_data: HistoricalEodPricingDataModel instance with updated data
        """
        self.date = pricing_data.date
        self.open = int(pricing_data.open * PRICE_MULTIPLIER)
        self.high = int(pricing_data.high * PRICE_MULTIPLIER)
        self.low = int(pricing_data.low * PRICE_MULTIPLIER)
        self.close = int(pricing_data.close * PRICE_MULTIPLIER)
        self.adjusted_close = int(pricing_data.adjusted_close * PRICE_MULTIPLIER)
        self.volume = pricing_data.volume
