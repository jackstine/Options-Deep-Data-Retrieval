"""TypedDict definitions for High/Low and Rebound derived data."""

from datetime import date
from decimal import Decimal
from typing import TypedDict


class HighLowDerivedData(TypedDict):
    """Derived data calculated from High/Low or Rebound pattern.

    This includes all the metrics that can be calculated from the pattern data,
    such as days between key points, status flags, and temporal metadata.
    """

    # Base fields - always present
    ticker_history_id: int
    threshold: Decimal
    high_start_price: Decimal
    high_start_date: date

    # Price and date fields - may be None for incomplete patterns
    low_threshold_price: Decimal | None
    low_threshold_date: date | None
    lowest_price: Decimal | None
    lowest_date: date | None
    high_threshold_price: Decimal | None
    high_threshold_date: date | None
    rebound_price: Decimal | None
    rebound_date: date | None

    # Counter field
    number_of_high_thresholds: int

    # Status flags
    is_low: bool  # True if pattern is still active (no rebound)
    is_rebound: bool  # True if pattern is complete (has rebound)
    still_low: bool  # True if pattern is active and not expired
    expired: bool  # True if pattern exceeded expiration threshold

    # Days between key points
    days_hs_lt: int | None  # High Start to Low Threshold
    days_hs_l: int | None  # High Start to Lowest
    days_hs_ht: int | None  # High Start to High Threshold
    days_hs_r: int | None  # High Start to Rebound
    days_lt_l: int | None  # Low Threshold to Lowest
    days_lt_ht: int | None  # Low Threshold to High Threshold
    days_lt_r: int | None  # Low Threshold to Rebound
    days_l_ht: int | None  # Lowest to High Threshold
    days_l_r: int | None  # Lowest to Rebound
    days_ht_r: int | None  # High Threshold to Rebound
    days_lt_now: int | None  # Low Threshold to current date (for active patterns)

    # Temporal metadata
    lt_year: int | None  # Year of low threshold
    lt_year_month: str | None  # Year-Month of low threshold (YYYY-MM)
    lt_month: int | None  # Month of low threshold
    r_year: int | None  # Year of rebound
    r_year_month: str | None  # Year-Month of rebound (YYYY-MM)
    r_month: int | None  # Month of rebound

    # Constants
    days_till_expiration: int  # Always 1200
