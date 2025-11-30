"""Date utility functions for algorithm calculations."""

from datetime import date


def days_between(date1: date, date2: date) -> int:
    """Calculate the number of days between two dates.

    Args:
        date1: The earlier date
        date2: The later date

    Returns:
        Number of days between the two dates (absolute value)
    """
    return abs((date2 - date1).days)


def get_year_month(d: date) -> str:
    """Get year-month string from date.

    Args:
        d: The date to format

    Returns:
        String in format "YYYY-MM"
    """
    return d.strftime("%Y-%m")
