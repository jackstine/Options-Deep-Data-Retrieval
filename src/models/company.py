"""Company data model with comprehensive typing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from src.database.equities.enums import DataSourceEnum

if TYPE_CHECKING:
    from src.models.ticker import Ticker


@dataclass
class Company:
    """Generic company information model."""

    company_name: str | None = None
    exchange: str | None = None
    ticker: Ticker | None = None  # Primary ticker model
    id: int | None = None
    sector: str | None = None
    industry: str | None = None
    country: str | None = None
    market_cap: int | None = None
    description: str | None = None
    active: bool | None = None
    is_valid_data: bool | None = None
    source: DataSourceEnum | str | None = None
    currency: str | None = None  #not in the DB
    type: str | None = None  #not in the DB
    isin: str | None = None  #not in the DB

    def to_dict(self) -> dict[str, Any]:
        """Convert company to dictionary for serialization."""
        return {
            "id": self.id,
            "company_name": self.company_name,
            "exchange": self.exchange,
            "ticker": self.ticker.to_dict() if self.ticker else None,
            "sector": self.sector,
            "industry": self.industry,
            "country": self.country,
            "market_cap": self.market_cap,
            "description": self.description,
            "active": self.active,
            "is_valid_data": self.is_valid_data,
            "source": self.source.value if isinstance(self.source, DataSourceEnum) else self.source,
            "currency": self.currency,
            "type": self.type,
            "isin": self.isin,
        }

    def print(self) -> None:
        """Print company information."""
        print(f"\n{self.company_name}")
        if self.ticker:
            print(f"  Ticker: {self.ticker.symbol}")
        if self.id:
            print(f"  ID: {self.id}")
        print(f"  Exchange: {self.exchange}")
        if self.sector:
            print(f"  Sector: {self.sector}")
        if self.industry:
            print(f"  Industry: {self.industry}")
        if self.country:
            print(f"  Country: {self.country}")
        if self.currency:
            print(f"  Currency: {self.currency}")
        if self.type:
            print(f"  Type: {self.type}")
        if self.isin:
            print(f"  ISIN: {self.isin}")
        if self.market_cap:
            print(f"  Market Cap: ${self.market_cap:,}")
        print(f"  Active: {'Yes' if self.active else 'No'}")
        print(f"  Source: {self.source}")

    def __str__(self) -> str:
        """String representation of company."""
        return (
            f"Company(id={self.id}, name={self.company_name}, exchange={self.exchange})"
        )

    def __repr__(self) -> str:
        """Detailed string representation of company."""
        return self.__str__()
