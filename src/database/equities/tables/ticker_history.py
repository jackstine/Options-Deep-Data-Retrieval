"""SQLAlchemy TickerHistory table for database operations."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database.equities.base import Base

# Import for relationship type hint
if TYPE_CHECKING:
    from src.database.equities.tables.company import Company


class TickerHistory(Base):
    """SQLAlchemy model for historical ticker symbol data with temporal tracking."""

    __tablename__ = "ticker_history"

    # Primary key with auto-incrementing serial ID
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Core ticker information
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"), nullable=False, index=True
    )

    # Temporal validity period
    valid_from: Mapped[date] = mapped_column(
        Date, nullable=False, default=date(1900, 1, 1), index=True
    )
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    # Trading status during this period
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped[Company] = relationship("Company", back_populates="ticker_history")

    def __repr__(self) -> str:
        """String representation of TickerHistory."""
        return f"<TickerHistory(id={self.id}, symbol='{self.symbol}', company_id={self.company_id}, valid_from='{self.valid_from}', valid_to='{self.valid_to}')>"

    def is_valid_on_date(self, check_date: date) -> bool:
        """Check if ticker was valid on a specific date.

        Args:
            check_date: Date to check validity for

        Returns:
            True if ticker was valid on the given date
        """
        if check_date < self.valid_from:
            return False
        if self.valid_to is not None and check_date > self.valid_to:
            return False
        return True

    def is_currently_valid(self) -> bool:
        """Check if ticker is currently valid.

        Returns:
            True if ticker is currently valid
        """
        today = date.today()
        return self.is_valid_on_date(today) and self.active

    def get_validity_period_str(self) -> str:
        """Get human-readable validity period string.

        Returns:
            String representation of validity period
        """
        start = self.valid_from.strftime("%Y-%m-%d")
        if self.valid_to:
            end = self.valid_to.strftime("%Y-%m-%d")
            return f"{start} to {end}"
        else:
            return f"{start} to present"
