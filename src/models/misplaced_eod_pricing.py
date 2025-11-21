"""Misplaced end-of-day pricing data model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from src.database.equities.enums import DataSourceEnum

if TYPE_CHECKING:
    from src.database.equities.tables.misplaced_eod_pricing import (
        MisplacedEodPricing as DBMisplacedEodPricing,
    )


@dataclass
class MisplacedEndOfDayPricing:
    """Misplaced end-of-day OHLCV price data model.

    Stores pricing data that does not currently have an association with
    ticker_history records. Used for staging data before matching to
    appropriate ticker records.
    """

    symbol: str
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adjusted_close: Decimal
    volume: int
    source: DataSourceEnum

    def to_dict(self) -> dict[str, Any]:
        """Convert pricing data to dictionary for serialization."""
        return {
            "symbol": self.symbol,
            "date": self.date.isoformat(),
            "open": float(self.open),
            "high": float(self.high),
            "low": float(self.low),
            "close": float(self.close),
            "adjusted_close": float(self.adjusted_close),
            "volume": self.volume,
            "source": str(self.source),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MisplacedEndOfDayPricing:
        """Create MisplacedEndOfDayPricing instance from dictionary.

        Args:
            data: Dictionary with pricing data

        Returns:
            MisplacedEndOfDayPricing instance
        """
        # Parse date from string if needed
        pricing_date = data["date"]
        if isinstance(pricing_date, str):
            pricing_date = date.fromisoformat(pricing_date)

        # Parse source from string if needed
        source = data["source"]
        if isinstance(source, str):
            source = DataSourceEnum(source)

        return cls(
            symbol=data["symbol"],
            date=pricing_date,
            open=Decimal(str(data["open"])),
            high=Decimal(str(data["high"])),
            low=Decimal(str(data["low"])),
            close=Decimal(str(data["close"])),
            adjusted_close=Decimal(str(data["adjusted_close"])),
            volume=int(data["volume"]),
            source=source,
        )

    def print(self) -> None:
        """Print pricing information."""
        print(f"\n{self.symbol} - {self.date}")
        print(f"  Open: ${self.open:.2f}")
        print(f"  High: ${self.high:.2f}")
        print(f"  Low: ${self.low:.2f}")
        print(f"  Close: ${self.close:.2f}")
        print(f"  Adjusted Close: ${self.adjusted_close:.2f}")
        print(f"  Volume: {self.volume:,}")

    def __str__(self) -> str:
        """String representation of pricing data."""
        return f"MisplacedEndOfDayPricing(symbol={self.symbol}, date={self.date}, close={self.close})"

    def __repr__(self) -> str:
        """Detailed string representation of pricing data."""
        return self.__str__()

    def to_db_model(self) -> DBMisplacedEodPricing:
        """Convert data model to SQLAlchemy database model.

        Returns:
            DBMisplacedEodPricing: SQLAlchemy model instance ready for database operations
        """
        from src.database.equities.tables.misplaced_eod_pricing import PRICE_MULTIPLIER
        from src.database.equities.tables.misplaced_eod_pricing import (
            MisplacedEodPricing as DBMisplacedEodPricing,
        )

        return DBMisplacedEodPricing(
            symbol=self.symbol,
            date=self.date,
            open=int(self.open * PRICE_MULTIPLIER),
            high=int(self.high * PRICE_MULTIPLIER),
            low=int(self.low * PRICE_MULTIPLIER),
            close=int(self.close * PRICE_MULTIPLIER),
            adjusted_close=int(self.adjusted_close * PRICE_MULTIPLIER),
            volume=self.volume,
            source=self.source,
        )

    @classmethod
    def from_db_model(cls, db_model: DBMisplacedEodPricing) -> MisplacedEndOfDayPricing:
        """Create data model from SQLAlchemy database model.

        Args:
            db_model: SQLAlchemy MisplacedEodPricing instance from database

        Returns:
            MisplacedEndOfDayPricing: Data model instance
        """
        from src.database.equities.tables.misplaced_eod_pricing import PRICE_MULTIPLIER

        return cls(
            symbol=db_model.symbol,
            date=db_model.date,
            open=Decimal(db_model.open) / PRICE_MULTIPLIER,
            high=Decimal(db_model.high) / PRICE_MULTIPLIER,
            low=Decimal(db_model.low) / PRICE_MULTIPLIER,
            close=Decimal(db_model.close) / PRICE_MULTIPLIER,
            adjusted_close=Decimal(db_model.adjusted_close) / PRICE_MULTIPLIER,
            volume=db_model.volume,
            source=db_model.source,
        )

    def update_db_model(self, db_model: DBMisplacedEodPricing) -> None:
        """Update existing SQLAlchemy database model with data from this model.

        Args:
            db_model: SQLAlchemy MisplacedEodPricing instance to update
        """
        from src.database.equities.tables.misplaced_eod_pricing import PRICE_MULTIPLIER

        db_model.symbol = self.symbol
        db_model.date = self.date
        db_model.open = int(self.open * PRICE_MULTIPLIER)
        db_model.high = int(self.high * PRICE_MULTIPLIER)
        db_model.low = int(self.low * PRICE_MULTIPLIER)
        db_model.close = int(self.close * PRICE_MULTIPLIER)
        db_model.adjusted_close = int(self.adjusted_close * PRICE_MULTIPLIER)
        db_model.volume = self.volume
        db_model.source = self.source
