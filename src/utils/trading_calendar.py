"""Trading calendar utilities for US stock market.

This module provides functions to work with US stock market trading days,
handling weekends and holidays automatically using the NYSE calendar.
"""

from __future__ import annotations

from datetime import date

import pandas_market_calendars as mcal  # type: ignore


def get_all_trading_days(start_date: date, end_date: date) -> list[date]:
    """Get all valid trading days between two dates (inclusive).

    Uses the NYSE calendar to determine valid trading days, automatically
    excluding weekends and market holidays.

    Args:
        start_date: The start date of the range
        end_date: The end date of the range (inclusive)

    Returns:
        List of dates that are valid trading days, sorted chronologically

    Raises:
        ValueError: If start_date is after end_date
    """
    # TODO not efficient,  better to have a cache of a set dates and use windowing arrays
    # to get the start and end dates
    if start_date > end_date:
        raise ValueError(
            f"start_date ({start_date}) must be before or equal to end_date ({end_date})"
        )

    # Get NYSE calendar
    nyse = mcal.get_calendar("NYSE")

    # Get trading days schedule
    schedule = nyse.schedule(start_date=start_date, end_date=end_date)

    # Extract dates and convert to list of date objects
    trading_days = [day.date() for day in schedule.index]

    return trading_days


def is_trading_day(check_date: date) -> bool:
    """Check if a specific date is a valid US stock market trading day.

    Args:
        check_date: The date to check

    Returns:
        True if the date is a trading day, False otherwise
    """
    # Get NYSE calendar
    nyse = mcal.get_calendar("NYSE")

    # Check if the date is in the valid trading days
    schedule = nyse.schedule(start_date=check_date, end_date=check_date)

    return len(schedule) > 0


def get_missing_trading_days(
    existing_dates: set[date], start_date: date, end_date: date
) -> list[date]:
    """Find missing trading days in a dataset.

    Compares the provided dates against all valid trading days in the range
    to identify which trading days are missing from the dataset.

    Args:
        existing_dates: Set of dates that exist in the dataset
        start_date: The start date of the range to check
        end_date: The end date of the range to check (inclusive)

    Returns:
        List of dates that are valid trading days but missing from existing_dates,
        sorted chronologically

    Raises:
        ValueError: If start_date is after end_date
    """
    # Get all valid trading days in the range
    all_trading_days = get_all_trading_days(start_date, end_date)

    # Find which trading days are missing
    missing_days = [day for day in all_trading_days if day not in existing_dates]

    return missing_days
