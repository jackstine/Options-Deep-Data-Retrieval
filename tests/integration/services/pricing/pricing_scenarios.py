"""Test scenarios for pricing integration tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class PricingTestScenario:
    """Test scenario for pricing data."""

    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adjusted_close: Decimal
    volume: int


@dataclass
class SplitTestScenario:
    """Test scenario for split data."""

    date: date
    split_ratio: str  # Format: "numerator/denominator"
