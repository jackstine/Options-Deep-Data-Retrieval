"""Pattern calculator for low/high algorithm.

This module provides utility functions and constants for pattern calculations.
"""

from __future__ import annotations

from decimal import Decimal

from src.algorithms.constants import DEFAULT_THRESHOLDS


class PatternCalculator:
    """Calculator for pattern-related computations."""

    @staticmethod
    def calculate_high_threshold_price(low_start_price: Decimal, threshold: Decimal) -> Decimal:
        """Calculate the price at which high_threshold would be triggered.

        Args:
            low_start_price: The low start price
            threshold: Threshold as decimal (e.g., 0.20 for 20%)

        Returns:
            Price at which high_threshold triggers
        """
        return low_start_price * (Decimal("1") + threshold)

    @staticmethod
    def calculate_low_threshold_price(highest_price: Decimal, threshold: Decimal) -> Decimal:
        """Calculate the price at which low_threshold would be triggered.

        Args:
            highest_price: The highest price
            threshold: Threshold as decimal (e.g., 0.20 for 20%)

        Returns:
            Price at which low_threshold triggers
        """
        return highest_price / (Decimal("1") + threshold)

    @staticmethod
    def is_above_high_threshold(
        price: Decimal, low_start_price: Decimal, threshold: Decimal
    ) -> bool:
        """Check if a price is at or above the high threshold.

        Args:
            price: Current price
            low_start_price: The low start price
            threshold: Threshold as decimal

        Returns:
            True if price >= low_start_price * (1 + threshold)
        """
        return price >= PatternCalculator.calculate_high_threshold_price(
            low_start_price, threshold
        )

    @staticmethod
    def is_below_low_threshold(
        price: Decimal, highest_price: Decimal, threshold: Decimal
    ) -> bool:
        """Check if a price is at or below the low threshold.

        Args:
            price: Current price
            highest_price: The highest price
            threshold: Threshold as decimal

        Returns:
            True if price <= highest_price / (1 + threshold)
        """
        return price <= PatternCalculator.calculate_low_threshold_price(
            highest_price, threshold
        )

    @staticmethod
    def is_at_reversal(price: Decimal, low_start_price: Decimal) -> bool:
        """Check if a price has reached reversal level.

        Args:
            price: Current price
            low_start_price: The original low start price

        Returns:
            True if price <= low_start_price
        """
        return price <= low_start_price

    @staticmethod
    def get_default_thresholds() -> list[Decimal]:
        """Get the default list of thresholds to use.

        Returns:
            List of Decimal thresholds from 15% to 70% in 5% increments
        """
        return DEFAULT_THRESHOLDS.copy()

    @staticmethod
    def calculate_rise_percentage(low_price: Decimal, high_price: Decimal) -> Decimal:
        """Calculate the percentage rise from low to high.

        Args:
            low_price: The low price
            high_price: The high price

        Returns:
            Rise percentage as decimal (e.g., 0.25 for 25% rise)
        """
        if low_price == 0:
            return Decimal("0")
        return (high_price - low_price) / low_price

    @staticmethod
    def calculate_decline_percentage(high_price: Decimal, decline_price: Decimal) -> Decimal:
        """Calculate the percentage decline from high to decline price.

        Args:
            high_price: The high price
            decline_price: The decline price

        Returns:
            Decline percentage as decimal (e.g., 0.30 for 30% decline)
        """
        if high_price == 0:
            return Decimal("0")
        return (high_price - decline_price) / high_price
