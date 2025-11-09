"""Historical end-of-day pricing data model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.database.equities.tables.historical_eod_pricing import (
        HistoricalEodPricing as DBHistoricalEodPricing,
    )


@dataclass
class HistoricalEndOfDayPricing:
    """Historical end-of-day OHLCV price data model."""

    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adjusted_close: Decimal
    volume: int
    id: int | None = None
    ticker_id: int | None = None
    symbol: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert pricing data to dictionary for serialization."""
        return {
            "id": self.id,
            "ticker_id": self.ticker_id,
            "symbol": self.symbol,
            "date": self.date.isoformat(),
            "open": float(self.open),
            "high": float(self.high),
            "low": float(self.low),
            "close": float(self.close),
            "adjusted_close": float(self.adjusted_close),
            "volume": self.volume,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HistoricalEndOfDayPricing:
        """Create HistoricalEndOfDayPricing instance from dictionary.

        Args:
            data: Dictionary with pricing data

        Returns:
            HistoricalEndOfDayPricing instance
        """
        # Parse date from string if needed
        pricing_date = data["date"]
        if isinstance(pricing_date, str):
            pricing_date = date.fromisoformat(pricing_date)

        return cls(
            id=data.get("id"),
            ticker_id=data.get("ticker_id"),
            symbol=data.get("symbol", ""),
            date=pricing_date,
            open=Decimal(str(data["open"])),
            high=Decimal(str(data["high"])),
            low=Decimal(str(data["low"])),
            close=Decimal(str(data["close"])),
            adjusted_close=Decimal(str(data["adjusted_close"])),
            volume=int(data["volume"]),
        )

    def print(self) -> None:
        """Print pricing information."""
        print(f"\n{self.symbol if self.symbol else 'Price Data'} - {self.date}")
        print(f"  Open: ${self.open:.2f}")
        print(f"  High: ${self.high:.2f}")
        print(f"  Low: ${self.low:.2f}")
        print(f"  Close: ${self.close:.2f}")
        print(f"  Adjusted Close: ${self.adjusted_close:.2f}")
        print(f"  Volume: {self.volume:,}")

    def __str__(self) -> str:
        """String representation of pricing data."""
        return f"HistoricalEndOfDayPricing(date={self.date}, close={self.close}, volume={self.volume})"

    def __repr__(self) -> str:
        """Detailed string representation of pricing data."""
        return self.__str__()

    def to_db_model(self) -> DBHistoricalEodPricing:
        """Convert data model to SQLAlchemy database model.

        Returns:
            DBHistoricalEodPricing: SQLAlchemy model instance ready for database operations

        Raises:
            ValueError: If ticker_id is None
        """
        if self.ticker_id is None:
            raise ValueError("ticker_id must be set before converting to database model")

        from src.database.equities.tables.historical_eod_pricing import (
            PRICE_MULTIPLIER,
            HistoricalEodPricing as DBHistoricalEodPricing,
        )

        return DBHistoricalEodPricing(
            ticker_id=self.ticker_id,
            date=self.date,
            open=int(self.open * PRICE_MULTIPLIER),
            high=int(self.high * PRICE_MULTIPLIER),
            low=int(self.low * PRICE_MULTIPLIER),
            close=int(self.close * PRICE_MULTIPLIER),
            adjusted_close=int(self.adjusted_close * PRICE_MULTIPLIER),
            volume=self.volume,
        )

    @classmethod
    def from_db_model(cls, db_model: DBHistoricalEodPricing) -> HistoricalEndOfDayPricing:
        """Create data model from SQLAlchemy database model.

        Args:
            db_model: SQLAlchemy HistoricalEodPricing instance from database

        Returns:
            HistoricalEndOfDayPricing: Data model instance
        """
        from src.database.equities.tables.historical_eod_pricing import PRICE_MULTIPLIER

        return cls(
            id=db_model.id,
            ticker_id=db_model.ticker_id,
            symbol="",  # Symbol not stored in DB, must be set separately if needed
            date=db_model.date,
            open=Decimal(db_model.open) / PRICE_MULTIPLIER,
            high=Decimal(db_model.high) / PRICE_MULTIPLIER,
            low=Decimal(db_model.low) / PRICE_MULTIPLIER,
            close=Decimal(db_model.close) / PRICE_MULTIPLIER,
            adjusted_close=Decimal(db_model.adjusted_close) / PRICE_MULTIPLIER,
            volume=db_model.volume,
        )

    def update_db_model(self, db_model: DBHistoricalEodPricing) -> None:
        """Update existing SQLAlchemy database model with data from this model.

        Note: Does not update ticker_id as it is a foreign key and should remain immutable.

        Args:
            db_model: SQLAlchemy HistoricalEodPricing instance to update
        """
        from src.database.equities.tables.historical_eod_pricing import PRICE_MULTIPLIER

        db_model.date = self.date
        db_model.open = int(self.open * PRICE_MULTIPLIER)
        db_model.high = int(self.high * PRICE_MULTIPLIER)
        db_model.low = int(self.low * PRICE_MULTIPLIER)
        db_model.close = int(self.close * PRICE_MULTIPLIER)
        db_model.adjusted_close = int(self.adjusted_close * PRICE_MULTIPLIER)
        db_model.volume = self.volume
