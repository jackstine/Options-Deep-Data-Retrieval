"""Pattern calculator for high/low algorithm.

This module provides utility functions and constants for pattern calculations.
"""

from __future__ import annotations

from decimal import Decimal

from src.algorithms.constants import DEFAULT_THRESHOLDS


class PatternCalculator:
    """Calculator for pattern-related computations."""

    @staticmethod
    def calculate_low_threshold_price(high_start_price: Decimal, threshold: Decimal) -> Decimal:
        """Calculate the price at which low_threshold would be triggered.

        Args:
            high_start_price: The high start price
            threshold: Threshold as decimal (e.g., 0.20 for 20%)

        Returns:
            Price at which low_threshold triggers
        """
        return high_start_price * (Decimal("1") - threshold)

    @staticmethod
    def calculate_high_threshold_price(lowest_price: Decimal, threshold: Decimal) -> Decimal:
        """Calculate the price at which high_threshold would be triggered.

        Args:
            lowest_price: The lowest price
            threshold: Threshold as decimal (e.g., 0.20 for 20%)

        Returns:
            Price at which high_threshold triggers
        """
        return lowest_price * (Decimal("1") + threshold)

    @staticmethod
    def is_below_low_threshold(
        price: Decimal, high_start_price: Decimal, threshold: Decimal
    ) -> bool:
        """Check if a price is at or below the low threshold.

        Args:
            price: Current price
            high_start_price: The high start price
            threshold: Threshold as decimal

        Returns:
            True if price <= high_start_price * (1 - threshold)
        """
        return price <= PatternCalculator.calculate_low_threshold_price(
            high_start_price, threshold
        )

    @staticmethod
    def is_above_high_threshold(
        price: Decimal, lowest_price: Decimal, threshold: Decimal
    ) -> bool:
        """Check if a price is at or above the high threshold.

        Args:
            price: Current price
            lowest_price: The lowest price
            threshold: Threshold as decimal

        Returns:
            True if price >= lowest_price * (1 + threshold)
        """
        return price >= PatternCalculator.calculate_high_threshold_price(
            lowest_price, threshold
        )

    @staticmethod
    def is_at_rebound(price: Decimal, high_start_price: Decimal) -> bool:
        """Check if a price has reached rebound level.

        Args:
            price: Current price
            high_start_price: The original high start price

        Returns:
            True if price >= high_start_price
        """
        return price >= high_start_price

    @staticmethod
    def get_default_thresholds() -> list[Decimal]:
        """Get the default list of thresholds to use.

        Returns:
            List of Decimal thresholds from 15% to 70% in 5% increments
        """
        return DEFAULT_THRESHOLDS.copy()

    @staticmethod
    def calculate_drop_percentage(high_price: Decimal, low_price: Decimal) -> Decimal:
        """Calculate the percentage drop from high to low.

        Args:
            high_price: The high price
            low_price: The low price

        Returns:
            Drop percentage as decimal (e.g., 0.25 for 25% drop)
        """
        if high_price == 0:
            return Decimal("0")
        return (high_price - low_price) / high_price

    @staticmethod
    def calculate_recovery_percentage(low_price: Decimal, recovery_price: Decimal) -> Decimal:
        """Calculate the percentage recovery from low to recovery price.

        Args:
            low_price: The low price
            recovery_price: The recovery price

        Returns:
            Recovery percentage as decimal (e.g., 0.30 for 30% recovery)
        """
        if low_price == 0:
            return Decimal("0")
        return (recovery_price - low_price) / low_price
