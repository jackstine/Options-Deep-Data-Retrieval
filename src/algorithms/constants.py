"""Shared constants for all algorithms.

This module contains constants that are used across multiple algorithms
to ensure consistency and provide a single source of truth.
"""

from decimal import Decimal

# Standard thresholds for pattern algorithms
# These represent percentage thresholds from 15% to 70% in 5% increments
# Used by both low/high and high/low algorithms for pattern detection
DEFAULT_THRESHOLDS = [
    Decimal("0.15"),  # 15%
    Decimal("0.20"),  # 20%
    Decimal("0.25"),  # 25%
    Decimal("0.30"),  # 30%
    Decimal("0.35"),  # 35%
    Decimal("0.40"),  # 40%
    Decimal("0.45"),  # 45%
    Decimal("0.50"),  # 50%
    Decimal("0.55"),  # 55%
    Decimal("0.60"),  # 60%
    Decimal("0.65"),  # 65%
    Decimal("0.70"),  # 70%
]
