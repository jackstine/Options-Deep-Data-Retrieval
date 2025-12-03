"""Rebound pattern data model for high/low algorithm."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from src.algorithms.high_lows.constants import EXPIRED_DAYS_OUT
from src.algorithms.high_lows.derived_data import HighLowDerivedData
from src.utils.date_utils import days_between, get_year_month


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
    low_threshold_price: Decimal
    lowest_price: Decimal
    high_threshold_price: Decimal
    rebound_price: Decimal
    high_start_date: date | None = None
    low_threshold_date: date | None = None
    lowest_date: date | None = None
    high_threshold_date: date | None = None
    rebound_date: date | None = None
    number_of_high_thresholds: int | None  = None
    id: int | None = None

    def __post_init__(self) -> None:
        """Validate required fields are set."""
        if self.ticker_history_id is None:
            raise ValueError("ticker_history_id is required and cannot be None")
        if self.high_start_date is None:
            raise ValueError("high_start_date is required and cannot be None")
        if self.low_threshold_date is None:
            raise ValueError("low_threshold_date is required and cannot be None")
        if self.lowest_date is None:
            raise ValueError("lowest_date is required and cannot be None")
        if self.high_threshold_date is None:
            raise ValueError("high_threshold_date is required and cannot be None")
        if self.rebound_date is None:
            raise ValueError("rebound_date is required and cannot be None")
        if self.number_of_high_thresholds is None:
            raise ValueError("number_of_high_thresholds is required and cannot be None")

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

    def is_expired(self) -> bool:
        """Check if pattern was expired when it completed.

        For rebounds, check if the pattern took longer than expiration threshold.
        See EXPIRED_DAYS_OUT in src.algorithms.high_lows.constants for threshold value.

        Returns:
            bool: True if pattern exceeded expiration period
        """
        days_from_lt_to_rebound = days_between(
            self.low_threshold_date, self.rebound_date
        )
        return days_from_lt_to_rebound > EXPIRED_DAYS_OUT

    def get_derived_data(self) -> HighLowDerivedData:
        """Calculate derived data from the pattern.

        This includes days between key points, status flags, and temporal metadata.
        Mimics the old repository's get_data() function.

        Returns:
            HighLowDerivedData: TypedDict with all derived metrics
        """
        # Rebound patterns are always complete
        is_complete = True

        # Calculate days between all combinations of key points
        days_hs_lt = days_between(self.high_start_date, self.low_threshold_date)
        days_hs_l = days_between(self.high_start_date, self.lowest_date)
        days_hs_ht = days_between(self.high_start_date, self.high_threshold_date)
        days_hs_r = days_between(self.high_start_date, self.rebound_date)
        days_lt_l = days_between(self.low_threshold_date, self.lowest_date)
        days_lt_ht = days_between(self.low_threshold_date, self.high_threshold_date)
        days_lt_r = days_between(self.low_threshold_date, self.rebound_date)
        days_l_ht = days_between(self.lowest_date, self.high_threshold_date)
        days_l_r = days_between(self.lowest_date, self.rebound_date)
        days_ht_r = days_between(self.high_threshold_date, self.rebound_date)

        # Temporal metadata for low threshold
        lt_year = self.low_threshold_date.year
        lt_year_month = get_year_month(self.low_threshold_date)
        lt_month = self.low_threshold_date.month

        # Temporal metadata for rebound
        r_year = self.rebound_date.year
        r_year_month = get_year_month(self.rebound_date)
        r_month = self.rebound_date.month

        # Status flags
        still_low = False  # Completed patterns are no longer "low"

        return HighLowDerivedData(
            # Base fields
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=self.high_start_price,
            high_start_date=self.high_start_date,
            # Price and date fields
            low_threshold_price=self.low_threshold_price,
            low_threshold_date=self.low_threshold_date,
            lowest_price=self.lowest_price,
            lowest_date=self.lowest_date,
            high_threshold_price=self.high_threshold_price,
            high_threshold_date=self.high_threshold_date,
            rebound_price=self.rebound_price,
            rebound_date=self.rebound_date,
            # Counter
            number_of_high_thresholds=self.number_of_high_thresholds,
            # Status flags
            is_low=not is_complete,
            is_rebound=is_complete,
            still_low=still_low,
            expired=self.is_expired(),
            # Days between key points
            days_hs_lt=days_hs_lt,
            days_hs_l=days_hs_l,
            days_hs_ht=days_hs_ht,
            days_hs_r=days_hs_r,
            days_lt_l=days_lt_l,
            days_lt_ht=days_lt_ht,
            days_lt_r=days_lt_r,
            days_l_ht=days_l_ht,
            days_l_r=days_l_r,
            days_ht_r=days_ht_r,
            days_lt_now=None,  # Not applicable for completed patterns
            # Temporal metadata
            lt_year=lt_year,
            lt_year_month=lt_year_month,
            lt_month=lt_month,
            r_year=r_year,
            r_year_month=r_year_month,
            r_month=r_month,
            # Constants
            days_till_expiration=EXPIRED_DAYS_OUT,
        )

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
            "number_of_high_thresholds": self.number_of_high_thresholds,
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
