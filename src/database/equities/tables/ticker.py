"""SQLAlchemy Ticker table for database operations."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database.equities.base import Base

# Import for relationship type hint
if TYPE_CHECKING:
    from src.database.equities.tables.company import Company


class Ticker(Base):
    """SQLAlchemy model for currently active ticker symbols."""

    __tablename__ = "tickers"

    # Primary key with auto-incrementing serial ID
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Core ticker information
    symbol: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"), nullable=False, index=True
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
    company: Mapped[Company] = relationship("Company", back_populates="tickers")

    def __repr__(self) -> str:
        """String representation of Ticker."""
        return f"<Ticker(id={self.id}, symbol='{self.symbol}', company_id={self.company_id})>"
