"""Comprehensive unit tests for PatternCalculator using unittest framework.

This test suite covers all functionality of the PatternCalculator class including:
- Threshold price calculations
- Boolean threshold checks with boundary conditions
- Default threshold retrieval
- Rise and decline percentage calculations
"""

from __future__ import annotations

import unittest
from decimal import Decimal

from src.algorithms.low_highs.pattern_calculator import PatternCalculator


class TestPatternCalculatorThresholds(unittest.TestCase):
    """Test threshold calculations."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.calc = PatternCalculator()

    def test_calculate_high_threshold_price_20_percent(self) -> None:
        """Test calculating high threshold price for 20% rise."""
        # Arrange
        low_start_price = Decimal("80.00")
        threshold = Decimal("0.20")

        # Act
        result = self.calc.calculate_high_threshold_price(low_start_price, threshold)

        # Assert
        self.assertEqual(result, Decimal("96.00"))

    def test_calculate_high_threshold_price_various_thresholds(self) -> None:
        """Test high threshold calculation with various threshold values."""
        low_start_price = Decimal("80.00")

        test_cases = [
            (Decimal("0.15"), Decimal("92.00")),
            (Decimal("0.25"), Decimal("100.00")),
            (Decimal("0.30"), Decimal("104.00")),
            (Decimal("0.50"), Decimal("120.00")),
        ]

        for threshold, expected in test_cases:
            with self.subTest(threshold=threshold):
                result = self.calc.calculate_high_threshold_price(
                    low_start_price, threshold
                )
                self.assertEqual(result, expected)

    def test_calculate_low_threshold_price_20_percent(self) -> None:
        """Test calculating low threshold price for 20% decline."""
        # Arrange
        highest_price = Decimal("96.00")
        threshold = Decimal("0.20")

        # Act
        result = self.calc.calculate_low_threshold_price(highest_price, threshold)

        # Assert
        self.assertEqual(result, Decimal("80.00"))

    def test_calculate_low_threshold_price_various_thresholds(self) -> None:
        """Test low threshold calculation with various threshold values."""
        highest_price = Decimal("100.00")

        test_cases = [
            (Decimal("0.15"), Decimal("86.95652173913043478260869565")),
            (Decimal("0.25"), Decimal("80.00")),
            (Decimal("0.30"), Decimal("76.92307692307692307692307692")),
            (Decimal("0.50"), Decimal("66.66666666666666666666666667")),
        ]

        for threshold, expected in test_cases:
            with self.subTest(threshold=threshold):
                result = self.calc.calculate_low_threshold_price(
                    highest_price, threshold
                )
                # Round to 2 decimal places for comparison
                self.assertAlmostEqual(
                    float(result), float(expected), places=2
                )

    def test_calculate_threshold_prices_with_decimal_precision(self) -> None:
        """Test that threshold calculations maintain decimal precision."""
        # Arrange
        low_start_price = Decimal("98.76")
        threshold = Decimal("0.20")

        # Act
        high_threshold = self.calc.calculate_high_threshold_price(
            low_start_price, threshold
        )

        # Assert
        self.assertEqual(high_threshold, Decimal("118.512"))
        # Verify it's a Decimal type
        self.assertIsInstance(high_threshold, Decimal)


class TestPatternCalculatorBooleanChecks(unittest.TestCase):
    """Test boolean threshold checks."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.calc = PatternCalculator()

    def test_is_above_high_threshold_true(self) -> None:
        """Test that price above threshold returns True."""
        # Arrange
        price = Decimal("100.00")
        low_start_price = Decimal("80.00")
        threshold = Decimal("0.20")  # High threshold is 96.00

        # Act
        result = self.calc.is_above_high_threshold(price, low_start_price, threshold)

        # Assert
        self.assertTrue(result)

    def test_is_above_high_threshold_false(self) -> None:
        """Test that price below threshold returns False."""
        # Arrange
        price = Decimal("90.00")
        low_start_price = Decimal("80.00")
        threshold = Decimal("0.20")  # High threshold is 96.00

        # Act
        result = self.calc.is_above_high_threshold(price, low_start_price, threshold)

        # Assert
        self.assertFalse(result)

    def test_is_above_high_threshold_exact_boundary(self) -> None:
        """Test that price exactly at threshold returns True (inclusive)."""
        # Arrange
        price = Decimal("96.00")
        low_start_price = Decimal("80.00")
        threshold = Decimal("0.20")  # High threshold is 96.00

        # Act
        result = self.calc.is_above_high_threshold(price, low_start_price, threshold)

        # Assert
        self.assertTrue(result)

    def test_is_below_low_threshold_true(self) -> None:
        """Test that price below threshold returns True."""
        # Arrange
        price = Decimal("75.00")
        highest_price = Decimal("96.00")
        threshold = Decimal("0.20")  # Low threshold is 80.00

        # Act
        result = self.calc.is_below_low_threshold(price, highest_price, threshold)

        # Assert
        self.assertTrue(result)

    def test_is_below_low_threshold_false(self) -> None:
        """Test that price above threshold returns False."""
        # Arrange
        price = Decimal("85.00")
        highest_price = Decimal("96.00")
        threshold = Decimal("0.20")  # Low threshold is 80.00

        # Act
        result = self.calc.is_below_low_threshold(price, highest_price, threshold)

        # Assert
        self.assertFalse(result)

    def test_is_below_low_threshold_exact_boundary(self) -> None:
        """Test that price exactly at threshold returns True (inclusive)."""
        # Arrange
        price = Decimal("80.00")
        highest_price = Decimal("96.00")
        threshold = Decimal("0.20")  # Low threshold is 80.00

        # Act
        result = self.calc.is_below_low_threshold(price, highest_price, threshold)

        # Assert
        self.assertTrue(result)

    def test_is_at_reversal_true(self) -> None:
        """Test that price at or below low_start returns True."""
        # Arrange
        price = Decimal("75.00")
        low_start_price = Decimal("80.00")

        # Act
        result = self.calc.is_at_reversal(price, low_start_price)

        # Assert
        self.assertTrue(result)

    def test_is_at_reversal_false(self) -> None:
        """Test that price above low_start returns False."""
        # Arrange
        price = Decimal("85.00")
        low_start_price = Decimal("80.00")

        # Act
        result = self.calc.is_at_reversal(price, low_start_price)

        # Assert
        self.assertFalse(result)

    def test_is_at_reversal_exact_boundary(self) -> None:
        """Test that price exactly at low_start returns True (inclusive)."""
        # Arrange
        price = Decimal("80.00")
        low_start_price = Decimal("80.00")

        # Act
        result = self.calc.is_at_reversal(price, low_start_price)

        # Assert
        self.assertTrue(result)


class TestPatternCalculatorDefaultThresholds(unittest.TestCase):
    """Test default threshold retrieval."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.calc = PatternCalculator()

    def test_get_default_thresholds_returns_correct_list(self) -> None:
        """Test that default thresholds are returned correctly."""
        # Act
        thresholds = self.calc.get_default_thresholds()

        # Assert
        expected = [
            Decimal("0.15"),
            Decimal("0.20"),
            Decimal("0.25"),
            Decimal("0.30"),
            Decimal("0.35"),
            Decimal("0.40"),
            Decimal("0.45"),
            Decimal("0.50"),
            Decimal("0.55"),
            Decimal("0.60"),
            Decimal("0.65"),
            Decimal("0.70"),
        ]
        self.assertEqual(thresholds, expected)
        self.assertEqual(len(thresholds), 12)

    def test_get_default_thresholds_returns_copy(self) -> None:
        """Test that get_default_thresholds returns a copy, not a reference."""
        # Act
        thresholds1 = self.calc.get_default_thresholds()
        thresholds2 = self.calc.get_default_thresholds()

        # Modify first list
        thresholds1.append(Decimal("0.99"))

        # Assert
        self.assertNotEqual(thresholds1, thresholds2)
        self.assertEqual(len(thresholds2), 12)

    def test_default_thresholds_are_decimal_type(self) -> None:
        """Test that all default thresholds are Decimal type."""
        # Act
        thresholds = self.calc.get_default_thresholds()

        # Assert
        for threshold in thresholds:
            self.assertIsInstance(threshold, Decimal)

    def test_default_thresholds_increment_by_5_percent(self) -> None:
        """Test that thresholds increment by 5% (0.05)."""
        # Act
        thresholds = self.calc.get_default_thresholds()

        # Assert
        for i in range(len(thresholds) - 1):
            diff = thresholds[i + 1] - thresholds[i]
            self.assertEqual(diff, Decimal("0.05"))


class TestPatternCalculatorPercentages(unittest.TestCase):
    """Test percentage calculations."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.calc = PatternCalculator()

    def test_calculate_rise_percentage_normal(self) -> None:
        """Test rise percentage calculation for normal case."""
        # Arrange
        low_price = Decimal("80.00")
        high_price = Decimal("96.00")

        # Act
        result = self.calc.calculate_rise_percentage(low_price, high_price)

        # Assert
        self.assertEqual(result, Decimal("0.20"))  # 20% rise

    def test_calculate_rise_percentage_50_percent(self) -> None:
        """Test rise percentage calculation for 50% rise."""
        # Arrange
        low_price = Decimal("100.00")
        high_price = Decimal("150.00")

        # Act
        result = self.calc.calculate_rise_percentage(low_price, high_price)

        # Assert
        self.assertEqual(result, Decimal("0.50"))  # 50% rise

    def test_calculate_rise_percentage_zero_low_price(self) -> None:
        """Test that zero low price returns zero to avoid division by zero."""
        # Arrange
        low_price = Decimal("0")
        high_price = Decimal("100.00")

        # Act
        result = self.calc.calculate_rise_percentage(low_price, high_price)

        # Assert
        self.assertEqual(result, Decimal("0"))

    def test_calculate_rise_percentage_no_rise(self) -> None:
        """Test that same prices result in zero rise."""
        # Arrange
        low_price = Decimal("100.00")
        high_price = Decimal("100.00")

        # Act
        result = self.calc.calculate_rise_percentage(low_price, high_price)

        # Assert
        self.assertEqual(result, Decimal("0"))

    def test_calculate_decline_percentage_normal(self) -> None:
        """Test decline percentage calculation for normal case."""
        # Arrange
        high_price = Decimal("100.00")
        decline_price = Decimal("80.00")

        # Act
        result = self.calc.calculate_decline_percentage(high_price, decline_price)

        # Assert
        self.assertEqual(result, Decimal("0.20"))  # 20% decline

    def test_calculate_decline_percentage_50_percent(self) -> None:
        """Test decline percentage calculation for 50% decline."""
        # Arrange
        high_price = Decimal("100.00")
        decline_price = Decimal("50.00")

        # Act
        result = self.calc.calculate_decline_percentage(high_price, decline_price)

        # Assert
        self.assertEqual(result, Decimal("0.50"))  # 50% decline

    def test_calculate_decline_percentage_zero_high_price(self) -> None:
        """Test that zero high price returns zero to avoid division by zero."""
        # Arrange
        high_price = Decimal("0")
        decline_price = Decimal("50.00")

        # Act
        result = self.calc.calculate_decline_percentage(high_price, decline_price)

        # Assert
        self.assertEqual(result, Decimal("0"))

    def test_calculate_decline_percentage_no_decline(self) -> None:
        """Test that same prices result in zero decline."""
        # Arrange
        high_price = Decimal("100.00")
        decline_price = Decimal("100.00")

        # Act
        result = self.calc.calculate_decline_percentage(high_price, decline_price)

        # Assert
        self.assertEqual(result, Decimal("0"))

    def test_calculate_rise_percentage_double_rise(self) -> None:
        """Test rise percentage for price doubling."""
        # Arrange
        low_price = Decimal("50.00")
        high_price = Decimal("100.00")

        # Act
        result = self.calc.calculate_rise_percentage(low_price, high_price)

        # Assert
        self.assertEqual(result, Decimal("1.00"))  # 100% rise (doubled)

    def test_percentage_calculations_maintain_decimal_precision(self) -> None:
        """Test that percentage calculations maintain decimal precision."""
        # Arrange
        low_price = Decimal("98.76")
        high_price = Decimal("123.45")

        # Act
        rise_result = self.calc.calculate_rise_percentage(low_price, high_price)

        # Assert
        self.assertIsInstance(rise_result, Decimal)
        # Verify it's calculated correctly with precision
        expected = (high_price - low_price) / low_price
        self.assertEqual(rise_result, expected)


if __name__ == "__main__":
    unittest.main()
