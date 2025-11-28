"""Ticker history statistics data model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class TickerHistoryStats:
    """Ticker history statistics data model.

    Stores computed statistics for a ticker history including price ranges and data coverage.
    Coverage percentage stored as basis points (0-10000).
    """

    ticker_history_id: int | None = None
    data_coverage_pct: int | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    average_price: Decimal | None = None
    median_price: Decimal | None = None
    has_insufficient_coverage: bool | None = None
    low_suspicious_price: bool | None = None
    high_suspicious_price: bool | None = None
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert stats data to dictionary for serialization."""
        return {
            "id": self.id,
            "ticker_history_id": self.ticker_history_id,
            "data_coverage_pct": self.data_coverage_pct,
            "min_price": float(self.min_price) if self.min_price is not None else None,
            "max_price": float(self.max_price) if self.max_price is not None else None,
            "average_price": float(self.average_price) if self.average_price is not None else None,
            "median_price": float(self.median_price) if self.median_price is not None else None,
            "has_insufficient_coverage": self.has_insufficient_coverage,
            "low_suspicious_price": self.low_suspicious_price,
            "high_suspicious_price": self.high_suspicious_price,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TickerHistoryStats:
        """Create TickerHistoryStats instance from dictionary.

        Args:
            data: Dictionary with stats data

        Returns:
            TickerHistoryStats instance
        """
        # Parse datetime from string if needed
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return cls(
            id=data.get("id"),
            ticker_history_id=data["ticker_history_id"],
            data_coverage_pct=data.get("data_coverage_pct"),
            min_price=Decimal(str(data["min_price"])) if data.get("min_price") is not None else None,
            max_price=Decimal(str(data["max_price"])) if data.get("max_price") is not None else None,
            average_price=Decimal(str(data["average_price"])) if data.get("average_price") is not None else None,
            median_price=Decimal(str(data["median_price"])) if data.get("median_price") is not None else None,
            has_insufficient_coverage=data.get("has_insufficient_coverage", False),
            low_suspicious_price=data.get("low_suspicious_price", False),
            high_suspicious_price=data.get("high_suspicious_price", False),
            created_at=created_at,
            updated_at=updated_at,
        )

    def print(self) -> None:
        """Print stats information."""
        print(f"\nTicker History Stats (ID: {self.ticker_history_id})")
        if self.data_coverage_pct is not None:
            coverage_percent = self.data_coverage_pct / 100.0
            print(f"  Data Coverage: {coverage_percent:.2f}%")
        if self.min_price is not None:
            print(f"  Min Price: ${self.min_price:.2f}")
        if self.max_price is not None:
            print(f"  Max Price: ${self.max_price:.2f}")
        if self.average_price is not None:
            print(f"  Average Price: ${self.average_price:.2f}")
        if self.median_price is not None:
            print(f"  Median Price: ${self.median_price:.2f}")

    def __str__(self) -> str:
        """String representation of stats data."""
        return f"TickerHistoryStats(ticker_history_id={self.ticker_history_id}, coverage={self.data_coverage_pct})"

    def __repr__(self) -> str:
        """Detailed string representation of stats data."""
        return self.__str__()
