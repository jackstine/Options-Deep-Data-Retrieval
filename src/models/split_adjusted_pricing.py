"""Split-adjusted pricing container model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Generic, TypeVar

from src.models.date_price import DatePrice
from src.models.eod_split_adjusted_pricing import EODSplitAdjustedPricing

# Generic type variable for pricing data
T = TypeVar("T", DatePrice, EODSplitAdjustedPricing)


@dataclass
class SplitAdjustedPricing(Generic[T]):
    """Container for split-adjusted pricing data.

    Generic model that can hold either simple DatePrice data or full
    EODSplitAdjustedPricing OHLCV data. The type parameter T determines
    which pricing model is contained in the prices list.

    Attributes:
        prices: List of pricing data (either DatePrice or EODSplitAdjustedPricing)
        from_date: Start date of the pricing data range (inclusive)
        to_date: End date of the pricing data range (inclusive)
        symbol: Optional stock symbol (e.g., "AAPL")
        ticker_history_id: Optional ticker history ID reference
        company_id: Optional company ID reference
    """

    prices: list[T]
    from_date: date | None
    to_date: date | None
    symbol: str | None = None
    ticker_history_id: int | None = None
    company_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert split-adjusted pricing data to dictionary for serialization."""
        return {
            "symbol": self.symbol,
            "ticker_history_id": self.ticker_history_id,
            "company_id": self.company_id,
            "from_date": self.from_date.isoformat() if self.from_date else None,
            "to_date": self.to_date.isoformat() if self.to_date else None,
            "prices": [price.to_dict() for price in self.prices],
            "count": len(self.prices),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], price_type: type[T]) -> SplitAdjustedPricing[T]:
        """Create SplitAdjustedPricing instance from dictionary.

        Args:
            data: Dictionary with split-adjusted pricing data
            price_type: Type of price model (DatePrice or EODSplitAdjustedPricing)

        Returns:
            SplitAdjustedPricing instance
        """
        # Parse dates from strings if needed
        from_date = data.get("from_date")
        if from_date and isinstance(from_date, str):
            from_date = date.fromisoformat(from_date)

        to_date = data.get("to_date")
        if to_date and isinstance(to_date, str):
            to_date = date.fromisoformat(to_date)

        # Parse prices using the specified type
        prices = [price_type.from_dict(price_data) for price_data in data["prices"]]

        return cls(
            symbol=data.get("symbol"),
            ticker_history_id=data.get("ticker_history_id"),
            company_id=data.get("company_id"),
            from_date=from_date,
            to_date=to_date,
            prices=prices,
        )

    def __str__(self) -> str:
        """String representation of split-adjusted pricing data."""
        identifier = self.symbol or f"ticker_history_id={self.ticker_history_id}" or f"company_id={self.company_id}"
        return f"SplitAdjustedPricing({identifier}, {len(self.prices)} prices, {self.from_date} to {self.to_date})"

    def __repr__(self) -> str:
        """Detailed string representation of split-adjusted pricing data."""
        return self.__str__()
