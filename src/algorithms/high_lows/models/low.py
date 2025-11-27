"""Low pattern data model for high/low algorithm."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.database.algorithms.tables.lows import Low as DBLow

# Days until a pattern expires (from old_repo: EXPIRED_DAYS_OUT = 800)
EXPIRATION_DAYS = 800


@dataclass
class Low:
    """Data model for an active low pattern in the high/low algorithm.

    A low pattern tracks a stock's price movement from a peak (high_start)
    through a drop (low_threshold), to the lowest point, and potential recovery.

    Pattern lifecycle:
    1. high_start: The peak price before a drop
    2. low_threshold: First price at or below high_start * (1 - threshold)
    3. lowest: The actual lowest point reached
    4. high_threshold: Recovery to lowest * (1 + threshold)
    5. Pattern spawns a new low when hitting high_threshold
    6. Pattern completes (becomes rebound) when price returns to high_start

    Threshold is stored as a decimal (e.g., 0.20 for 20%)
    """

    ticker_history_id: int
    threshold: Decimal
    high_start_price: Decimal
    high_start_date: date
    last_updated: date
    low_threshold_price: Decimal | None = None
    low_threshold_date: date | None = None
    lowest_price: Decimal | None = None
    lowest_date: date | None = None
    high_threshold_price: Decimal | None = None
    high_threshold_date: date | None = None
    number_of_high_thresholds: int = 0
    spawned: bool = False
    expired: bool = False
    id: int | None = None

    def is_complete(self) -> bool:
        """Check if pattern is complete (ready to become a rebound).

        A pattern is complete when it has a rebound price (price returned to high_start).
        This is determined externally - this model only tracks up to high_threshold.

        Returns:
            bool: Always False for Low patterns (completeness is checked in processor)
        """
        return False

    def is_expired(self) -> bool:
        """Check if pattern has expired (800 days from low_threshold_date).

        Returns:
            bool: True if pattern has exceeded expiration period
        """
        if not self.low_threshold_date:
            return False

        days_since_low = (date.today() - self.low_threshold_date).days
        return days_since_low > EXPIRATION_DAYS

    def has_low_threshold(self) -> bool:
        """Check if low threshold has been set.

        Returns:
            bool: True if low_threshold_price and low_threshold_date are set
        """
        return (
            self.low_threshold_price is not None
            and self.low_threshold_date is not None
        )

    def has_high_threshold(self) -> bool:
        """Check if high threshold has been set.

        Returns:
            bool: True if high_threshold_price and high_threshold_date are set
        """
        return (
            self.high_threshold_price is not None
            and self.high_threshold_date is not None
        )

    def should_spawn(self) -> bool:
        """Check if pattern should spawn a new low.

        Pattern spawns when it hits high_threshold but hasn't spawned yet.

        Returns:
            bool: True if should spawn a new pattern
        """
        return self.has_high_threshold() and not self.spawned

    def days_since_low_threshold(self) -> int | None:
        """Calculate days since low threshold was reached.

        Returns:
            int | None: Number of days, or None if low_threshold_date not set
        """
        if not self.low_threshold_date:
            return None
        return (date.today() - self.low_threshold_date).days

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            dict: Dictionary representation of the low pattern
        """
        return {
            "id": self.id,
            "ticker_history_id": self.ticker_history_id,
            "threshold": float(self.threshold),
            "high_start_price": float(self.high_start_price),
            "high_start_date": self.high_start_date.isoformat(),
            "low_threshold_price": (
                float(self.low_threshold_price) if self.low_threshold_price else None
            ),
            "low_threshold_date": (
                self.low_threshold_date.isoformat() if self.low_threshold_date else None
            ),
            "lowest_price": float(self.lowest_price) if self.lowest_price else None,
            "lowest_date": self.lowest_date.isoformat() if self.lowest_date else None,
            "high_threshold_price": (
                float(self.high_threshold_price) if self.high_threshold_price else None
            ),
            "high_threshold_date": (
                self.high_threshold_date.isoformat() if self.high_threshold_date else None
            ),
            "number_of_high_thresholds": self.number_of_high_thresholds,
            "last_updated": self.last_updated.isoformat(),
            "spawned": self.spawned,
            "expired": self.expired,
        }

    def __str__(self) -> str:
        """String representation of Low pattern."""
        return (
            f"Low(id={self.id}, ticker_history_id={self.ticker_history_id}, "
            f"threshold={self.threshold}, last_updated={self.last_updated})"
        )

    def __repr__(self) -> str:
        """Detailed string representation of Low pattern."""
        return self.__str__()

    def to_db_model(self) -> DBLow:
        """Convert data model to SQLAlchemy database model.

        Returns:
            DBLow: SQLAlchemy model instance ready for database operations
        """
        from src.database.algorithms.tables.lows import (
            PRICE_MULTIPLIER,
        )
        from src.database.algorithms.tables.lows import (
            Low as DBLow,
        )

        # Convert threshold from decimal to basis points (0.20 -> 2000)
        threshold_bp = int(self.threshold * Decimal("10000"))

        db_model = DBLow(
            ticker_history_id=self.ticker_history_id,
            threshold=threshold_bp,
            high_start_price=int(self.high_start_price * PRICE_MULTIPLIER),
            high_start_date=self.high_start_date,
            low_threshold_price=(
                int(self.low_threshold_price * PRICE_MULTIPLIER)
                if self.low_threshold_price is not None
                else None
            ),
            low_threshold_date=self.low_threshold_date,
            lowest_price=(
                int(self.lowest_price * PRICE_MULTIPLIER)
                if self.lowest_price is not None
                else None
            ),
            lowest_date=self.lowest_date,
            high_threshold_price=(
                int(self.high_threshold_price * PRICE_MULTIPLIER)
                if self.high_threshold_price is not None
                else None
            ),
            high_threshold_date=self.high_threshold_date,
            number_of_high_thresholds=self.number_of_high_thresholds,
            last_updated=self.last_updated,
            spawned=self.spawned,
            expired=self.expired,
        )

        if self.id is not None:
            db_model.id = self.id

        return db_model

    @classmethod
    def from_db_model(cls, db_model: DBLow) -> Low:
        """Create data model from SQLAlchemy database model.

        Args:
            db_model: SQLAlchemy Low instance from database

        Returns:
            Low: Data model instance
        """
        from src.database.algorithms.tables.lows import PRICE_MULTIPLIER

        # Convert threshold from basis points to decimal (2000 -> 0.20)
        threshold = Decimal(db_model.threshold) / Decimal("10000")

        return cls(
            id=db_model.id,
            ticker_history_id=db_model.ticker_history_id,
            threshold=threshold,
            high_start_price=Decimal(db_model.high_start_price) / PRICE_MULTIPLIER,
            high_start_date=db_model.high_start_date,
            low_threshold_price=(
                Decimal(db_model.low_threshold_price) / PRICE_MULTIPLIER
                if db_model.low_threshold_price is not None
                else None
            ),
            low_threshold_date=db_model.low_threshold_date,
            lowest_price=(
                Decimal(db_model.lowest_price) / PRICE_MULTIPLIER
                if db_model.lowest_price is not None
                else None
            ),
            lowest_date=db_model.lowest_date,
            high_threshold_price=(
                Decimal(db_model.high_threshold_price) / PRICE_MULTIPLIER
                if db_model.high_threshold_price is not None
                else None
            ),
            high_threshold_date=db_model.high_threshold_date,
            number_of_high_thresholds=db_model.number_of_high_thresholds,
            last_updated=db_model.last_updated,
            spawned=db_model.spawned,
            expired=db_model.expired,
        )

    def update_db_model(self, db_model: DBLow) -> None:
        """Update existing SQLAlchemy database model with data from this model.

        Note: Does not update id or ticker_history_id as they are immutable.

        Args:
            db_model: SQLAlchemy Low instance to update
        """
        from src.database.algorithms.tables.lows import PRICE_MULTIPLIER

        # Convert threshold from decimal to basis points
        threshold_bp = int(self.threshold * Decimal("10000"))

        db_model.threshold = threshold_bp
        db_model.high_start_price = int(self.high_start_price * PRICE_MULTIPLIER)
        db_model.high_start_date = self.high_start_date
        db_model.low_threshold_price = (
            int(self.low_threshold_price * PRICE_MULTIPLIER)
            if self.low_threshold_price is not None
            else None
        )
        db_model.low_threshold_date = self.low_threshold_date
        db_model.lowest_price = (
            int(self.lowest_price * PRICE_MULTIPLIER)
            if self.lowest_price is not None
            else None
        )
        db_model.lowest_date = self.lowest_date
        db_model.high_threshold_price = (
            int(self.high_threshold_price * PRICE_MULTIPLIER)
            if self.high_threshold_price is not None
            else None
        )
        db_model.high_threshold_date = self.high_threshold_date
        db_model.number_of_high_thresholds = self.number_of_high_thresholds
        db_model.last_updated = self.last_updated
        db_model.spawned = self.spawned
        db_model.expired = self.expired
