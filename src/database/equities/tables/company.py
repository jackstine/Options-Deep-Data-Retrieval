"""SQLAlchemy Company table for database operations."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database.equities.base import Base

# Import for relationship type hint
if TYPE_CHECKING:
    from src.database.equities.tables.ticker import Ticker
    from src.database.equities.tables.ticker_history import TickerHistory


class Company(Base):
    """SQLAlchemy model for company data."""

    __tablename__ = "companies"

    # Primary key with auto-incrementing serial ID
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Core company information
    company_name: Mapped[str] = mapped_column(String(500), nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False)

    # Optional company details
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    industry: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    market_cap: Mapped[int | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Trading status
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )

    # Data source tracking
    source: Mapped[str] = mapped_column(String(50), nullable=False)

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
    tickers: Mapped[list[Ticker]] = relationship("Ticker", back_populates="company")
    ticker_history: Mapped[list[TickerHistory]] = relationship(
        "TickerHistory", back_populates="company"
    )

    def __repr__(self) -> str:
        """String representation of Company."""
        return f"<Company(id={self.id}, name='{self.company_name}')>"
