"""Rebound pattern data model for high/low algorithm."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.database.algorithms.tables.rebounds import Rebound as DBRebound


@dataclass
class Rebound:
    """Data model for a completed rebound pattern in the high/low algorithm.

    A rebound represents a completed price pattern where a stock dropped by
    a threshold percentage and then recovered back to the original high.

    Complete pattern lifecycle:
    1. high_start: The peak price before a drop
    2. low_threshold: First price at or below high_start * (1 - threshold)
    3. lowest: The actual lowest point reached
    4. high_threshold: Recovery to lowest * (1 + threshold)
    5. rebound: Price returned to or exceeded high_start (PATTERN COMPLETE)

    Threshold is stored as a decimal (e.g., 0.20 for 20%)
    """

    ticker_history_id: int
    threshold: Decimal
    high_start_price: Decimal
    high_start_date: date
    low_threshold_price: Decimal
    low_threshold_date: date
    lowest_price: Decimal
    lowest_date: date
    high_threshold_price: Decimal
    high_threshold_date: date
    rebound_price: Decimal
    rebound_date: date
    id: int | None = None

    def days_from_low_to_rebound(self) -> int:
        """Calculate number of days from low threshold to rebound.

        Returns:
            int: Number of days between low_threshold_date and rebound_date
        """
        return (self.rebound_date - self.low_threshold_date).days

    def days_from_high_to_low(self) -> int:
        """Calculate number of days from high start to low threshold.

        Returns:
            int: Number of days between high_start_date and low_threshold_date
        """
        return (self.low_threshold_date - self.high_start_date).days

    def total_pattern_days(self) -> int:
        """Calculate total days for complete pattern.

        Returns:
            int: Number of days from high_start_date to rebound_date
        """
        return (self.rebound_date - self.high_start_date).days

    def drop_percentage(self) -> Decimal:
        """Calculate actual drop percentage from high to lowest.

        Returns:
            Decimal: Drop percentage (e.g., 0.25 for 25% drop)
        """
        if self.high_start_price == 0:
            return Decimal("0")
        return (self.high_start_price - self.lowest_price) / self.high_start_price

    def recovery_percentage(self) -> Decimal:
        """Calculate recovery percentage from lowest to rebound.

        Returns:
            Decimal: Recovery percentage (e.g., 0.30 for 30% recovery)
        """
        if self.lowest_price == 0:
            return Decimal("0")
        return (self.rebound_price - self.lowest_price) / self.lowest_price

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            dict: Dictionary representation of the rebound pattern
        """
        return {
            "id": self.id,
            "ticker_history_id": self.ticker_history_id,
            "threshold": float(self.threshold),
            "high_start_price": float(self.high_start_price),
            "high_start_date": self.high_start_date.isoformat(),
            "low_threshold_price": float(self.low_threshold_price),
            "low_threshold_date": self.low_threshold_date.isoformat(),
            "lowest_price": float(self.lowest_price),
            "lowest_date": self.lowest_date.isoformat(),
            "high_threshold_price": float(self.high_threshold_price),
            "high_threshold_date": self.high_threshold_date.isoformat(),
            "rebound_price": float(self.rebound_price),
            "rebound_date": self.rebound_date.isoformat(),
            "days_from_low_to_rebound": self.days_from_low_to_rebound(),
            "total_pattern_days": self.total_pattern_days(),
            "drop_percentage": float(self.drop_percentage()),
            "recovery_percentage": float(self.recovery_percentage()),
        }

    def __str__(self) -> str:
        """String representation of Rebound pattern."""
        return (
            f"Rebound(id={self.id}, ticker_history_id={self.ticker_history_id}, "
            f"threshold={self.threshold}, rebound_date={self.rebound_date})"
        )

    def __repr__(self) -> str:
        """Detailed string representation of Rebound pattern."""
        return self.__str__()

    def to_db_model(self) -> DBRebound:
        """Convert data model to SQLAlchemy database model.

        Returns:
            DBRebound: SQLAlchemy model instance ready for database operations
        """
        from src.database.algorithms.tables.rebounds import (
            PRICE_MULTIPLIER,
        )
        from src.database.algorithms.tables.rebounds import (
            Rebound as DBRebound,
        )

        # Convert threshold from decimal to basis points (0.20 -> 2000)
        threshold_bp = int(self.threshold * Decimal("10000"))

        db_model = DBRebound(
            ticker_history_id=self.ticker_history_id,
            threshold=threshold_bp,
            high_start_price=int(self.high_start_price * PRICE_MULTIPLIER),
            high_start_date=self.high_start_date,
            low_threshold_price=int(self.low_threshold_price * PRICE_MULTIPLIER),
            low_threshold_date=self.low_threshold_date,
            lowest_price=int(self.lowest_price * PRICE_MULTIPLIER),
            lowest_date=self.lowest_date,
            high_threshold_price=int(self.high_threshold_price * PRICE_MULTIPLIER),
            high_threshold_date=self.high_threshold_date,
            rebound_price=int(self.rebound_price * PRICE_MULTIPLIER),
            rebound_date=self.rebound_date,
        )

        if self.id is not None:
            db_model.id = self.id

        return db_model

    @classmethod
    def from_db_model(cls, db_model: DBRebound) -> Rebound:
        """Create data model from SQLAlchemy database model.

        Args:
            db_model: SQLAlchemy Rebound instance from database

        Returns:
            Rebound: Data model instance
        """
        from src.database.algorithms.tables.rebounds import PRICE_MULTIPLIER

        # Convert threshold from basis points to decimal (2000 -> 0.20)
        threshold = Decimal(db_model.threshold) / Decimal("10000")

        return cls(
            id=db_model.id,
            ticker_history_id=db_model.ticker_history_id,
            threshold=threshold,
            high_start_price=Decimal(db_model.high_start_price) / PRICE_MULTIPLIER,
            high_start_date=db_model.high_start_date,
            low_threshold_price=Decimal(db_model.low_threshold_price)
            / PRICE_MULTIPLIER,
            low_threshold_date=db_model.low_threshold_date,
            lowest_price=Decimal(db_model.lowest_price) / PRICE_MULTIPLIER,
            lowest_date=db_model.lowest_date,
            high_threshold_price=Decimal(db_model.high_threshold_price)
            / PRICE_MULTIPLIER,
            high_threshold_date=db_model.high_threshold_date,
            rebound_price=Decimal(db_model.rebound_price) / PRICE_MULTIPLIER,
            rebound_date=db_model.rebound_date,
        )

    def update_db_model(self, db_model: DBRebound) -> None:
        """Update existing SQLAlchemy database model with data from this model.

        Note: Does not update id or ticker_history_id as they are immutable.

        Args:
            db_model: SQLAlchemy Rebound instance to update
        """
        from src.database.algorithms.tables.rebounds import PRICE_MULTIPLIER

        # Convert threshold from decimal to basis points
        threshold_bp = int(self.threshold * Decimal("10000"))

        db_model.threshold = threshold_bp
        db_model.high_start_price = int(self.high_start_price * PRICE_MULTIPLIER)
        db_model.high_start_date = self.high_start_date
        db_model.low_threshold_price = int(
            self.low_threshold_price * PRICE_MULTIPLIER
        )
        db_model.low_threshold_date = self.low_threshold_date
        db_model.lowest_price = int(self.lowest_price * PRICE_MULTIPLIER)
        db_model.lowest_date = self.lowest_date
        db_model.high_threshold_price = int(
            self.high_threshold_price * PRICE_MULTIPLIER
        )
        db_model.high_threshold_date = self.high_threshold_date
        db_model.rebound_price = int(self.rebound_price * PRICE_MULTIPLIER)
        db_model.rebound_date = self.rebound_date
