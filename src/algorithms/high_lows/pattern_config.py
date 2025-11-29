"""Configuration for high/low pattern processing."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class HighLowPatternConfig:
    """Configuration for processing high/low patterns.

    Attributes:
        threshold: The threshold percentage as a decimal (e.g., 0.20 for 20%)
    """

    threshold: Decimal
