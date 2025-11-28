"""Reversal pattern data model for low/high algorithm."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from src.algorithms.low_highs.constants import EXPIRED_DAYS_OUT
from src.algorithms.low_highs.derived_data import LowHighDerivedData
from src.utils.date_utils import days_between, get_year_month

if TYPE_CHECKING:
    from src.database.algorithms.tables.reversals import Reversal as DBReversal


@dataclass
class Reversal:
    """Data model for a completed reversal pattern in the low/high algorithm.

    A reversal represents a completed price pattern where a stock rose by
    a threshold percentage and then declined back to the original low.

    Complete pattern lifecycle:
    1. low_start: The trough price before a rise
    2. high_threshold: First price at or above low_start * (1 + threshold)
    3. highest: The actual highest point reached
    4. low_threshold: Decline to highest / (1 + threshold)
    5. reversal: Price returned to or fell below low_start (PATTERN COMPLETE)

    Threshold is stored as a decimal (e.g., 0.20 for 20%)
    """

    ticker_history_id: int
    threshold: Decimal
    low_start_price: Decimal
    high_threshold_price: Decimal
    highest_price: Decimal
    low_threshold_price: Decimal
    reversal_price: Decimal
    low_start_date: date | None = None
    high_threshold_date: date | None = None
    highest_date: date | None = None
    low_threshold_date: date | None = None
    reversal_date: date | None = None
    number_of_low_thresholds: int | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        """Validate required fields are set."""
        if self.ticker_history_id is None:
            raise ValueError("ticker_history_id is required and cannot be None")
        if self.low_start_date is None:
            raise ValueError("low_start_date is required and cannot be None")
        if self.high_threshold_date is None:
            raise ValueError("high_threshold_date is required and cannot be None")
        if self.highest_date is None:
            raise ValueError("highest_date is required and cannot be None")
        if self.low_threshold_date is None:
            raise ValueError("low_threshold_date is required and cannot be None")
        if self.reversal_date is None:
            raise ValueError("reversal_date is required and cannot be None")
        if self.number_of_low_thresholds is None:
            raise ValueError("number_of_low_thresholds is required and cannot be None")

    def days_from_high_to_reversal(self) -> int:
        """Calculate number of days from high threshold to reversal.

        Returns:
            int: Number of days between high_threshold_date and reversal_date
        """
        return (self.reversal_date - self.high_threshold_date).days

    def days_from_low_to_high(self) -> int:
        """Calculate number of days from low start to high threshold.

        Returns:
            int: Number of days between low_start_date and high_threshold_date
        """
        return (self.high_threshold_date - self.low_start_date).days

    def total_pattern_days(self) -> int:
        """Calculate total days for complete pattern.

        Returns:
            int: Number of days from low_start_date to reversal_date
        """
        return (self.reversal_date - self.low_start_date).days

    def rise_percentage(self) -> Decimal:
        """Calculate actual rise percentage from low to highest.

        Returns:
            Decimal: Rise percentage (e.g., 0.25 for 25% rise)
        """
        if self.low_start_price == 0:
            return Decimal("0")
        return (self.highest_price - self.low_start_price) / self.low_start_price

    def decline_percentage(self) -> Decimal:
        """Calculate decline percentage from highest to reversal.

        Returns:
            Decimal: Decline percentage (e.g., 0.30 for 30% decline)
        """
        if self.highest_price == 0:
            return Decimal("0")
        return (self.highest_price - self.reversal_price) / self.highest_price

    def is_expired(self) -> bool:
        """Check if pattern was expired when it completed.

        For reversals, check if the pattern took longer than expiration threshold.
        See EXPIRED_DAYS_OUT in src.algorithms.low_highs.constants for threshold value.

        Returns:
            bool: True if pattern exceeded expiration period
        """
        days_from_ht_to_reversal = days_between(
            self.high_threshold_date, self.reversal_date
        )
        return days_from_ht_to_reversal > EXPIRED_DAYS_OUT

    def get_derived_data(self) -> LowHighDerivedData:
        """Calculate derived data from the pattern.

        This includes days between key points, status flags, and temporal metadata.
        Mimics the old repository's get_data() function.

        Returns:
            LowHighDerivedData: TypedDict with all derived metrics
        """
        # Reversal patterns are always complete
        is_complete = True

        # Calculate days between all combinations of key points
        days_ls_ht = days_between(self.low_start_date, self.high_threshold_date)
        days_ls_h = days_between(self.low_start_date, self.highest_date)
        days_ls_lt = days_between(self.low_start_date, self.low_threshold_date)
        days_ls_r = days_between(self.low_start_date, self.reversal_date)
        days_ht_h = days_between(self.high_threshold_date, self.highest_date)
        days_ht_lt = days_between(self.high_threshold_date, self.low_threshold_date)
        days_ht_r = days_between(self.high_threshold_date, self.reversal_date)
        days_h_lt = days_between(self.highest_date, self.low_threshold_date)
        days_h_r = days_between(self.highest_date, self.reversal_date)
        days_lt_r = days_between(self.low_threshold_date, self.reversal_date)

        # Temporal metadata for high threshold
        ht_year = self.high_threshold_date.year
        ht_year_month = get_year_month(self.high_threshold_date)
        ht_month = self.high_threshold_date.month

        # Temporal metadata for reversal
        r_year = self.reversal_date.year
        r_year_month = get_year_month(self.reversal_date)
        r_month = self.reversal_date.month

        # Status flags
        still_high = False  # Completed patterns are no longer "high"

        return LowHighDerivedData(
            # Base fields
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            low_start_price=self.low_start_price,
            low_start_date=self.low_start_date,
            # Price and date fields
            high_threshold_price=self.high_threshold_price,
            high_threshold_date=self.high_threshold_date,
            highest_price=self.highest_price,
            highest_date=self.highest_date,
            low_threshold_price=self.low_threshold_price,
            low_threshold_date=self.low_threshold_date,
            reversal_price=self.reversal_price,
            reversal_date=self.reversal_date,
            # Counter
            number_of_low_thresholds=self.number_of_low_thresholds,
            # Status flags
            is_high=not is_complete,
            is_reversal=is_complete,
            still_high=still_high,
            expired=self.is_expired(),
            # Days between key points
            days_ls_ht=days_ls_ht,
            days_ls_h=days_ls_h,
            days_ls_lt=days_ls_lt,
            days_ls_r=days_ls_r,
            days_ht_h=days_ht_h,
            days_ht_lt=days_ht_lt,
            days_ht_r=days_ht_r,
            days_h_lt=days_h_lt,
            days_h_r=days_h_r,
            days_lt_r=days_lt_r,
            days_ht_now=None,  # Not applicable for completed patterns
            # Temporal metadata
            ht_year=ht_year,
            ht_year_month=ht_year_month,
            ht_month=ht_month,
            r_year=r_year,
            r_year_month=r_year_month,
            r_month=r_month,
            # Constants
            days_till_expiration=EXPIRED_DAYS_OUT,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            dict: Dictionary representation of the reversal pattern
        """
        return {
            "id": self.id,
            "ticker_history_id": self.ticker_history_id,
            "threshold": float(self.threshold),
            "low_start_price": float(self.low_start_price),
            "low_start_date": self.low_start_date.isoformat(),
            "high_threshold_price": float(self.high_threshold_price),
            "high_threshold_date": self.high_threshold_date.isoformat(),
            "highest_price": float(self.highest_price),
            "highest_date": self.highest_date.isoformat(),
            "low_threshold_price": float(self.low_threshold_price),
            "low_threshold_date": self.low_threshold_date.isoformat(),
            "reversal_price": float(self.reversal_price),
            "reversal_date": self.reversal_date.isoformat(),
            "number_of_low_thresholds": self.number_of_low_thresholds,
            "days_from_high_to_reversal": self.days_from_high_to_reversal(),
            "total_pattern_days": self.total_pattern_days(),
            "rise_percentage": float(self.rise_percentage()),
            "decline_percentage": float(self.decline_percentage()),
        }

    def __str__(self) -> str:
        """String representation of Reversal pattern."""
        return (
            f"Reversal(id={self.id}, ticker_history_id={self.ticker_history_id}, "
            f"threshold={self.threshold}, reversal_date={self.reversal_date})"
        )

    def __repr__(self) -> str:
        """Detailed string representation of Reversal pattern."""
        return self.__str__()

    def to_db_model(self) -> DBReversal:
        """Convert data model to SQLAlchemy database model.

        Returns:
            DBReversal: SQLAlchemy model instance ready for database operations
        """
        from src.database.algorithms.tables.reversals import (
            PRICE_MULTIPLIER,
        )
        from src.database.algorithms.tables.reversals import (
            Reversal as DBReversal,
        )

        # Convert threshold from decimal to basis points (0.20 -> 2000)
        threshold_bp = int(self.threshold * Decimal("10000"))

        db_model = DBReversal(
            ticker_history_id=self.ticker_history_id,
            threshold=threshold_bp,
            low_start_price=int(self.low_start_price * PRICE_MULTIPLIER),
            low_start_date=self.low_start_date,
            high_threshold_price=int(self.high_threshold_price * PRICE_MULTIPLIER),
            high_threshold_date=self.high_threshold_date,
            highest_price=int(self.highest_price * PRICE_MULTIPLIER),
            highest_date=self.highest_date,
            low_threshold_price=int(self.low_threshold_price * PRICE_MULTIPLIER),
            low_threshold_date=self.low_threshold_date,
            reversal_price=int(self.reversal_price * PRICE_MULTIPLIER),
            reversal_date=self.reversal_date,
            number_of_low_thresholds=self.number_of_low_thresholds,
        )

        if self.id is not None:
            db_model.id = self.id

        return db_model

    @classmethod
    def from_db_model(cls, db_model: DBReversal) -> Reversal:
        """Create data model from SQLAlchemy database model.

        Args:
            db_model: SQLAlchemy Reversal instance from database

        Returns:
            Reversal: Data model instance
        """
        from src.database.algorithms.tables.reversals import PRICE_MULTIPLIER

        # Convert threshold from basis points to decimal (2000 -> 0.20)
        threshold = Decimal(db_model.threshold) / Decimal("10000")

        return cls(
            id=db_model.id,
            ticker_history_id=db_model.ticker_history_id,
            threshold=threshold,
            low_start_price=Decimal(db_model.low_start_price) / PRICE_MULTIPLIER,
            low_start_date=db_model.low_start_date,
            high_threshold_price=Decimal(db_model.high_threshold_price)
            / PRICE_MULTIPLIER,
            high_threshold_date=db_model.high_threshold_date,
            highest_price=Decimal(db_model.highest_price) / PRICE_MULTIPLIER,
            highest_date=db_model.highest_date,
            low_threshold_price=Decimal(db_model.low_threshold_price)
            / PRICE_MULTIPLIER,
            low_threshold_date=db_model.low_threshold_date,
            reversal_price=Decimal(db_model.reversal_price) / PRICE_MULTIPLIER,
            reversal_date=db_model.reversal_date,
            number_of_low_thresholds=db_model.number_of_low_thresholds,
        )

    def update_db_model(self, db_model: DBReversal) -> None:
        """Update existing SQLAlchemy database model with data from this model.

        Note: Does not update id or ticker_history_id as they are immutable.

        Args:
            db_model: SQLAlchemy Reversal instance to update
        """
        from src.database.algorithms.tables.reversals import PRICE_MULTIPLIER

        # Convert threshold from decimal to basis points
        threshold_bp = int(self.threshold * Decimal("10000"))

        db_model.threshold = threshold_bp
        db_model.low_start_price = int(self.low_start_price * PRICE_MULTIPLIER)
        db_model.low_start_date = self.low_start_date
        db_model.high_threshold_price = int(
            self.high_threshold_price * PRICE_MULTIPLIER
        )
        db_model.high_threshold_date = self.high_threshold_date
        db_model.highest_price = int(self.highest_price * PRICE_MULTIPLIER)
        db_model.highest_date = self.highest_date
        db_model.low_threshold_price = int(
            self.low_threshold_price * PRICE_MULTIPLIER
        )
        db_model.low_threshold_date = self.low_threshold_date
        db_model.reversal_price = int(self.reversal_price * PRICE_MULTIPLIER)
        db_model.reversal_date = self.reversal_date
        db_model.number_of_low_thresholds = self.number_of_low_thresholds
