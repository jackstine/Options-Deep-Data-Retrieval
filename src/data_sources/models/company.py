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
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Company:
        """Create Company instance from dictionary."""
        # Handle ticker deserialization
        ticker = None
        ticker_data = data.get("ticker")
        if ticker_data:
            from src.data_sources.models.ticker import Ticker

            if isinstance(ticker_data, dict):
                ticker = Ticker.from_dict(ticker_data)
            elif isinstance(ticker_data, str):
                # Handle legacy string ticker format
                ticker = Ticker(symbol=ticker_data, company_id=data.get("id", 0))

        return cls(
            id=data.get("id"),
            company_name=data["company_name"],
            exchange=data["exchange"],
            ticker=ticker,
            sector=data.get("sector"),
            industry=data.get("industry"),
            country=data.get("country"),
            market_cap=data.get("market_cap"),
            description=data.get("description"),
            active=data.get("active", True),
            source=data.get("source", ""),
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
