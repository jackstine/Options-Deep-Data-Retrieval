"""Database enums for the equities schema."""

from enum import Enum


class DataSourceEnum(str, Enum):
    """Enum for data source providers."""

    EODHD = "EODHD"
    NASDAQ_SCREENER = "NASDAQ_SCREENER"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value
