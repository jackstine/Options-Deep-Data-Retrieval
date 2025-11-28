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
    """Historical end-of-day OHLCV price data model.

    Note: Uses ticker_history_id (not ticker_id) to support both active
    and delisted symbols. The ticker_history table tracks all symbols,
    while the ticker table only contains currently active symbols.
    """

    date: date | None = None
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    close: Decimal | None = None
    adjusted_close: Decimal | None = None
    volume: int | None = None
    ticker_history_id: int | None = None  # References ticker_history table
    symbol: str | None = None  # For display purposes only, not stored in DB

    def to_dict(self) -> dict[str, Any]:
        """Convert pricing data to dictionary for serialization."""
        return {
            "ticker_history_id": self.ticker_history_id,
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
            ticker_history_id=data.get("ticker_history_id"),
            symbol=data.get("symbol"),
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
            ValueError: If ticker_history_id is None
        """
        if self.ticker_history_id is None:
            raise ValueError(
                "ticker_history_id must be set before converting to database model"
            )

        from src.database.equities.tables.historical_eod_pricing import (
            PRICE_MULTIPLIER,
        )
        from src.database.equities.tables.historical_eod_pricing import (
            HistoricalEodPricing as DBHistoricalEodPricing,
        )

        return DBHistoricalEodPricing(
            ticker_history_id=self.ticker_history_id,
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
            ticker_history_id=db_model.ticker_history_id,
            symbol=None,  # Symbol not stored in DB, must be set separately if needed
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

        Note: Does not update ticker_history_id as it is a foreign key and should remain immutable.

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
