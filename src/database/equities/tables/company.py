"""SQLAlchemy Company table for database operations."""

from __future__ import annotations
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func

from src.database.equities.base import Base
from src.data_sources.models.company import Company as CompanyDataModel


class Company(Base):
    """SQLAlchemy model for company data."""
    
    __tablename__ = 'companies'
    
    # Primary key with auto-incrementing serial ID
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core company information
    ticker = Column(String(20), nullable=False, unique=True, index=True)
    company_name = Column(String(500), nullable=False)
    exchange = Column(String(20), nullable=False)
    
    # Optional company details
    sector = Column(String(100), nullable=True, index=True)
    industry = Column(String(200), nullable=True, index=True)
    country = Column(String(100), nullable=True)
    market_cap = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    
    # Trading status
    active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Data source tracking
    source = Column(String(50), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        """String representation of Company."""
        return f"<Company(id={self.id}, ticker='{self.ticker}', name='{self.company_name}')>"
    
    def to_data_model(self) -> CompanyDataModel:
        """
        Convert SQLAlchemy model to data model.
        
        Returns:
            CompanyDataModel instance
        """
        return CompanyDataModel(
            id=self.id, # type: ignore[arg-type]
            ticker=self.ticker, # type: ignore[arg-type]
            company_name=self.company_name, # type: ignore[arg-type]
            exchange=self.exchange, # type: ignore[arg-type]
            sector=self.sector, # type: ignore[arg-type]
            industry=self.industry, # type: ignore[arg-type]
            country=self.country, # type: ignore[arg-type]
            market_cap=self.market_cap, # type: ignore[arg-type]
            description=self.description, # type: ignore[arg-type]
            active=self.active, # type: ignore[arg-type]
            source=self.source # type: ignore[arg-type]
        )
    
    @classmethod
    def from_data_model(cls, company_data: CompanyDataModel) -> Company:
        """
        Create SQLAlchemy model from data model.
        
        Args:
            company_data: CompanyDataModel instance
            
        Returns:
            Company SQLAlchemy model instance
        """
        return cls(
            ticker=company_data.ticker,
            company_name=company_data.company_name,
            exchange=company_data.exchange,
            sector=company_data.sector,
            industry=company_data.industry,
            country=company_data.country,
            market_cap=company_data.market_cap,
            description=company_data.description,
            active=company_data.active,
            source=company_data.source
        )
    
    def update_from_data_model(self, company_data: CompanyDataModel) -> None:
        """
        Update existing SQLAlchemy model from data model.
        
        Args:
            company_data: CompanyDataModel instance with updated data
        """
        self.ticker = company_data.ticker
        self.company_name = company_data.company_name
        self.exchange = company_data.exchange
        self.sector = company_data.sector
        self.industry = company_data.industry
        self.country = company_data.country
        self.market_cap = company_data.market_cap
        self.description = company_data.description
        self.active = company_data.active
        self.source = company_data.source