"""Company data model with comprehensive typing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.data_sources.models.ticker import Ticker


@dataclass
class Company:
    """Generic company information model."""

    company_name: str
    exchange: str
    ticker: Ticker | None = None  # Primary ticker model
    id: int | None = None
    sector: str | None = None
    industry: str | None = None
    country: str | None = None
    market_cap: int | None = None
    description: str | None = None
    active: bool = True
    source: str = ""
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
            "source": self.source,
            "currency": self.currency,
            "type": self.type,
            "isin": self.isin,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Company:
        """Create Company instance from dictionary.

        Supports both snake_case and EODHD API PascalCase format.
        """
        from src.data_sources.models.ticker import Ticker

        # Handle ticker deserialization
        ticker = None
        ticker_data = data.get("ticker")

        # Handle EODHD API format (Code field)
        if not ticker_data and "Code" in data:
            ticker = Ticker(symbol=data["Code"], company_id=data.get("id", 0))
        elif ticker_data:
            if isinstance(ticker_data, dict):
                ticker = Ticker.from_dict(ticker_data)
            elif isinstance(ticker_data, str):
                # Handle legacy string ticker format
                ticker = Ticker(symbol=ticker_data, company_id=data.get("id", 0))

        # Support both snake_case and PascalCase for field names
        return cls(
            id=data.get("id"),
            company_name=data.get("company_name") or data.get("Name", ""),
            exchange=data.get("exchange") or data.get("Exchange", ""),
            ticker=ticker,
            sector=data.get("sector"),
            industry=data.get("industry"),
            country=data.get("country") or data.get("Country"),
            market_cap=data.get("market_cap"),
            description=data.get("description"),
            active=data.get("active", True),
            source=data.get("source", ""),
            currency=data.get("currency") or data.get("Currency"),
            type=data.get("type") or data.get("Type"),
            isin=data.get("isin") or data.get("Isin"),
        )

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
