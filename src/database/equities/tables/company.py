"""SQLAlchemy Company table for database operations."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from src.data_sources.models.company import Company as CompanyDataModel
from src.database.equities.base import Base

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

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

    def to_data_model(self) -> CompanyDataModel:
        """Convert SQLAlchemy model to data model.

        Returns:
            CompanyDataModel instance
        """
        return CompanyDataModel(
            id=self.id,
            company_name=self.company_name,
            exchange=self.exchange,
            sector=self.sector,
            industry=self.industry,
            country=self.country,
            market_cap=self.market_cap,
            description=self.description,
            active=self.active,
            source=self.source,
        )

    @classmethod
    def from_data_model(cls, company_data: CompanyDataModel) -> Company:
        """Create SQLAlchemy model from data model.

        Args:
            company_data: CompanyDataModel instance

        Returns:
            Company SQLAlchemy model instance
        """
        return cls(
            company_name=company_data.company_name,
            exchange=company_data.exchange,
            sector=company_data.sector,
            industry=company_data.industry,
            country=company_data.country,
            market_cap=company_data.market_cap,
            description=company_data.description,
            active=company_data.active,
            source=company_data.source,
        )

    def update_from_data_model(self, company_data: CompanyDataModel) -> None:
        """Update existing SQLAlchemy model from data model.

        Args:
            company_data: CompanyDataModel instance with updated data
        """
        self.company_name = company_data.company_name
        self.exchange = company_data.exchange
        self.sector = company_data.sector
        self.industry = company_data.industry
        self.country = company_data.country
        self.market_cap = company_data.market_cap
        self.description = company_data.description
        self.active = company_data.active
        self.source = company_data.source
