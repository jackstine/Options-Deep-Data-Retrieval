"""SQLAlchemy Missing EOD Pricing table for database operations."""

from __future__ import annotations

from datetime import date as date_type
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.equities.base import Base

# Import for relationship type hints
if TYPE_CHECKING:
    from src.database.equities.tables.company import Company
    from src.database.equities.tables.ticker_history import TickerHistory


class MissingEodPricing(Base):
    """SQLAlchemy model for tracking missing end-of-day pricing data.

    This table records which dates are missing pricing data for specific
    tickers. Used to track and fill gaps in historical pricing data.

    Note: Foreign keys use RESTRICT to prevent deletion of company or
    ticker_history records that have missing pricing entries.
    """

    __tablename__ = "missing_eod_pricing"

    # Foreign key to companies table
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Foreign key to ticker_history table
    ticker_history_id: Mapped[int] = mapped_column(
        ForeignKey("ticker_history.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Missing trading date
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)

    # Relationships
    company: Mapped[Company] = relationship("Company")
    ticker_history: Mapped[TickerHistory] = relationship("TickerHistory")

    # Constraints
    __table_args__ = (
        PrimaryKeyConstraint(
            "company_id", "ticker_history_id", "date", name="pk_missing_pricing_composite"
        ),
        {"comment": "Tracks missing end-of-day pricing data for tickers"},
    )

    def __repr__(self) -> str:
        """String representation of MissingEodPricing."""
        return f"<MissingEodPricing(company_id={self.company_id}, ticker_history_id={self.ticker_history_id}, date={self.date})>"
