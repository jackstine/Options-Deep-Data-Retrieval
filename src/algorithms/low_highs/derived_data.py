"""TypedDict definitions for Low/High and Reversal derived data."""

from datetime import date
from decimal import Decimal
from typing import TypedDict


class LowHighDerivedData(TypedDict):
    """Derived data calculated from Low/High or Reversal pattern.

    This includes all the metrics that can be calculated from the pattern data,
    such as days between key points, status flags, and temporal metadata.
    """

    # Base fields - always present
    ticker_history_id: int
    threshold: Decimal
    low_start_price: Decimal
    low_start_date: date

    # Price and date fields - may be None for incomplete patterns
    high_threshold_price: Decimal | None
    high_threshold_date: date | None
    highest_price: Decimal | None
    highest_date: date | None
    low_threshold_price: Decimal | None
    low_threshold_date: date | None
    reversal_price: Decimal | None
    reversal_date: date | None

    # Counter field
    number_of_low_thresholds: int

    # Status flags
    is_high: bool  # True if pattern is still active (no reversal)
    is_reversal: bool  # True if pattern is complete (has reversal)
    still_high: bool  # True if pattern is active and not expired
    expired: bool  # True if pattern exceeded expiration threshold

    # Days between key points
    days_ls_ht: int | None  # Low Start to High Threshold
    days_ls_h: int | None  # Low Start to Highest
    days_ls_lt: int | None  # Low Start to Low Threshold
    days_ls_r: int | None  # Low Start to Reversal
    days_ht_h: int | None  # High Threshold to Highest
    days_ht_lt: int | None  # High Threshold to Low Threshold
    days_ht_r: int | None  # High Threshold to Reversal
    days_h_lt: int | None  # Highest to Low Threshold
    days_h_r: int | None  # Highest to Reversal
    days_lt_r: int | None  # Low Threshold to Reversal
    days_ht_now: int | None  # High Threshold to current date (for active patterns)

    # Temporal metadata
    ht_year: int | None  # Year of high threshold
    ht_year_month: str | None  # Year-Month of high threshold (YYYY-MM)
    ht_month: int | None  # Month of high threshold
    r_year: int | None  # Year of reversal
    r_year_month: str | None  # Year-Month of reversal (YYYY-MM)
    r_month: int | None  # Month of reversal

    # Constants
    days_till_expiration: int  # Always 1200
