"""Comprehensive unit tests for low_high_processor state machine.

This test suite covers the core algorithm logic for processing low/high patterns:
- State 1: Searching for high_threshold
- State 2: Tracking highest, waiting for low_threshold
- State 3: Waiting for reversal
- Pattern spawning logic
- Reversal creation and completion
- Edge cases and error handling
"""

from __future__ import annotations

import unittest
from datetime import date, timedelta
from decimal import Decimal

from src.algorithms.low_highs.models.high import High
from src.algorithms.low_highs.processor import (
    _create_reversal_from_high,
    process_low_high_patterns,
)
from src.models.date_price import DatePrice


class TestProcessorStateOne(unittest.TestCase):
    """Test State 1: Searching for high_threshold."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.threshold = Decimal("0.20")
        self.ticker_history_id = 1
        self.base_date = date(2024, 1, 1)

    def test_price_rises_by_threshold_sets_high_threshold(self) -> None:
        """Test that price rise by threshold sets high_threshold and highest."""
        # Arrange
        pattern = High(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            low_start_price=Decimal("80.00"),
            low_start_date=self.base_date,
            last_updated=self.base_date,
        )

        # Price rises to 96 (20% rise)
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=1),
                price=Decimal("96.00"),
            )
        ]

        # Act
        result = process_low_high_patterns([pattern], new_prices, self.threshold)

        # Assert
        # TODO needs to verify that other things do not change,  that they are none
        self.assertEqual(len(result.active_highs), 1)
        self.assertEqual(len(result.completed_reversals), 0)

        updated_pattern = result.active_highs[0]
        self.assertEqual(updated_pattern.high_threshold_price, Decimal("96.00"))
        self.assertEqual(
            updated_pattern.high_threshold_date, self.base_date + timedelta(days=1)
        )
        self.assertEqual(updated_pattern.highest_price, Decimal("96.00"))
        self.assertEqual(updated_pattern.highest_date, self.base_date + timedelta(days=1))

    def test_price_falls_below_low_start_updates_trough(self) -> None:
        """Test that price falling below low_start updates the trough."""
        # Arrange
        pattern = High(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            low_start_price=Decimal("80.00"),
            low_start_date=self.base_date,
            last_updated=self.base_date,
        )

        # Price goes down to 70
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=1),
                price=Decimal("70.00"),
            )
        ]

        # Act
        result = process_low_high_patterns([pattern], new_prices, self.threshold)

        # Assert
        # TODO needs to verify that other things do not change,  that they are none
        self.assertEqual(len(result.active_highs), 1)
        updated_pattern = result.active_highs[0]
        self.assertEqual(updated_pattern.low_start_price, Decimal("70.00"))
        self.assertEqual(
            updated_pattern.low_start_date, self.base_date + timedelta(days=1)
        )
        # high_threshold should still be None
        self.assertIsNone(updated_pattern.high_threshold_price)

    def test_price_between_threshold_and_low_no_change(self) -> None:
        """Test that price between threshold and low causes no state change."""
        # Arrange
        pattern = High(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            low_start_price=Decimal("80.00"),
            low_start_date=self.base_date,
            last_updated=self.base_date,
        )

        # Price goes to 90 (12.5% rise, less than 20% threshold)
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=1),
                price=Decimal("90.00"),
            )
        ]

        # Act
        result = process_low_high_patterns([pattern], new_prices, self.threshold)

        # Assert
        self.assertEqual(len(result.active_highs), 1)
        updated_pattern = result.active_highs[0]
        # No state change - still searching
        # TODO needs to verify that other things do not change,  that they are none
        self.assertIsNone(updated_pattern.high_threshold_price)
        self.assertEqual(updated_pattern.low_start_price, Decimal("80.00"))


class TestProcessorStateTwo(unittest.TestCase):
    """Test State 2: Tracking highest, waiting for low_threshold."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.threshold = Decimal("0.20")
        self.ticker_history_id = 1
        self.base_date = date(2024, 1, 1)

    def test_price_declines_by_threshold_sets_low_threshold(self) -> None:
        """Test that price decline by threshold sets low_threshold."""
        # Arrange - Pattern already in State 2 (high_threshold set), already spawned
        pattern = High(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            low_start_price=Decimal("80.00"),
            low_start_date=self.base_date,
            high_threshold_price=Decimal("96.00"),
            high_threshold_date=self.base_date + timedelta(days=1),
            highest_price=Decimal("100.00"),
            highest_date=self.base_date + timedelta(days=2),
            last_updated=self.base_date + timedelta(days=2),
            spawned=True,  # Already spawned, won't spawn again
        )

        # Price declines to ~83.33 (20% below highest of 100)
        # 100 / 1.20 = 83.333...
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=3),
                price=Decimal("83.00"),
            )
        ]

        # Act
        result = process_low_high_patterns([pattern], new_prices, self.threshold)

        # Assert
        self.assertEqual(len(result.active_highs), 1)
        updated_pattern = result.active_highs[0]
        self.assertEqual(updated_pattern.low_threshold_price, Decimal("83.00"))
        self.assertEqual(
            updated_pattern.low_threshold_date, self.base_date + timedelta(days=3)
        )

    def test_pattern_spawns_when_low_threshold_reached(self) -> None:
        """Test that new pattern spawns when low_threshold is reached."""
        # Arrange - Pattern in State 2, not yet spawned
        pattern = High(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            low_start_price=Decimal("80.00"),
            low_start_date=self.base_date,
            high_threshold_price=Decimal("96.00"),
            high_threshold_date=self.base_date + timedelta(days=1),
            highest_price=Decimal("100.00"),
            highest_date=self.base_date + timedelta(days=2),
            last_updated=self.base_date + timedelta(days=2),
            spawned=False,
        )

        # Price declines to 83
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=3),
                price=Decimal("83.00"),
            )
        ]

        # Act
        result = process_low_high_patterns([pattern], new_prices, self.threshold)

        # Assert
        # Should have original pattern + spawned pattern
        self.assertEqual(len(result.active_highs), 2)

        # Original pattern should have spawned flag set (at index 0)
        original = result.active_highs[0]
        self.assertTrue(original.spawned)

        # Check spawned pattern (added via extend, so it's at index 1)
        spawned = result.active_highs[1]
        self.assertEqual(spawned.low_start_price, Decimal("83.00"))
        self.assertEqual(spawned.spawned, False)
        self.assertIsNone(spawned.high_threshold_price)

    def test_price_continues_to_rise_updates_highest(self) -> None:
        """Test that price continuing to rise updates highest."""
        # Arrange
        pattern = High(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            low_start_price=Decimal("80.00"),
            low_start_date=self.base_date,
            high_threshold_price=Decimal("96.00"),
            high_threshold_date=self.base_date + timedelta(days=1),
            highest_price=Decimal("100.00"),
            highest_date=self.base_date + timedelta(days=2),
            last_updated=self.base_date + timedelta(days=2),
            spawned=True,
        )

        # Price rises to 110
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=3),
                price=Decimal("110.00"),
            )
        ]

        # Act
        result = process_low_high_patterns([pattern], new_prices, self.threshold)

        # Assert
        self.assertEqual(len(result.active_highs), 1)
        updated_pattern = result.active_highs[0]
        self.assertEqual(updated_pattern.highest_price, Decimal("110.00"))
        self.assertEqual(updated_pattern.highest_date, self.base_date + timedelta(days=3))

    def test_immediate_reversal_on_low_threshold(self) -> None:
        """Test pattern completes immediately if low_threshold <= low_start."""
        # Arrange - Pattern not yet spawned, so it will spawn before completing
        pattern = High(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            low_start_price=Decimal("80.00"),
            low_start_date=self.base_date,
            high_threshold_price=Decimal("96.00"),
            high_threshold_date=self.base_date + timedelta(days=1),
            highest_price=Decimal("96.00"),
            highest_date=self.base_date + timedelta(days=1),
            last_updated=self.base_date + timedelta(days=1),
            spawned=False,  # Not yet spawned
        )

        # Price declines all the way to 79 (below low_start of 80)
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=2),
                price=Decimal("79.00"),
            )
        ]

        # Act
        result = process_low_high_patterns([pattern], new_prices, self.threshold)

        # Assert
        # Should have spawned pattern + completed reversal
        self.assertEqual(len(result.active_highs), 1)  # spawned pattern
        self.assertEqual(len(result.completed_reversals), 1)

        # Check spawned pattern
        spawned = result.active_highs[0]
        self.assertEqual(spawned.low_start_price, Decimal("79.00"))

        # Check completed reversal
        reversal = result.completed_reversals[0]
        self.assertEqual(reversal.reversal_price, Decimal("79.00"))
        self.assertEqual(reversal.reversal_date, self.base_date + timedelta(days=2))


class TestProcessorStateThree(unittest.TestCase):
    """Test State 3: Waiting for reversal."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.threshold = Decimal("0.20")
        self.ticker_history_id = 1
        self.base_date = date(2024, 1, 1)

    def test_price_returns_to_low_start_completes_reversal(self) -> None:
        """Test that price returning to low_start completes the pattern."""
        # Arrange - Pattern in State 3 (low_threshold set)
        pattern = High(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            low_start_price=Decimal("80.00"),
            low_start_date=self.base_date,
            high_threshold_price=Decimal("96.00"),
            high_threshold_date=self.base_date + timedelta(days=1),
            highest_price=Decimal("100.00"),
            highest_date=self.base_date + timedelta(days=2),
            low_threshold_price=Decimal("83.00"),
            low_threshold_date=self.base_date + timedelta(days=3),
            last_updated=self.base_date + timedelta(days=3),
            spawned=True,
        )

        # Price returns to 80
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=4),
                price=Decimal("80.00"),
            )
        ]

        # Act
        result = process_low_high_patterns([pattern], new_prices, self.threshold)

        # Assert
        self.assertEqual(len(result.active_highs), 0)
        self.assertEqual(len(result.completed_reversals), 1)

        reversal = result.completed_reversals[0]
        self.assertEqual(reversal.reversal_price, Decimal("80.00"))
        self.assertEqual(reversal.low_start_price, Decimal("80.00"))
        self.assertEqual(reversal.highest_price, Decimal("100.00"))

    def test_price_rises_above_highest_resets_low_threshold(self) -> None:
        """Test that price rising above highest resets low_threshold."""
        # Arrange
        pattern = High(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            low_start_price=Decimal("80.00"),
            low_start_date=self.base_date,
            high_threshold_price=Decimal("96.00"),
            high_threshold_date=self.base_date + timedelta(days=1),
            highest_price=Decimal("100.00"),
            highest_date=self.base_date + timedelta(days=2),
            low_threshold_price=Decimal("83.00"),
            low_threshold_date=self.base_date + timedelta(days=3),
            last_updated=self.base_date + timedelta(days=3),
            spawned=True,
        )

        # Price rises to 105
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=4),
                price=Decimal("105.00"),
            )
        ]

        # Act
        result = process_low_high_patterns([pattern], new_prices, self.threshold)

        # Assert
        self.assertEqual(len(result.active_highs), 1)
        self.assertEqual(len(result.completed_reversals), 0)

        updated_pattern = result.active_highs[0]
        # Should have reset low_threshold and updated highest
        self.assertIsNone(updated_pattern.low_threshold_price)
        self.assertIsNone(updated_pattern.low_threshold_date)
        self.assertEqual(updated_pattern.highest_price, Decimal("105.00"))
        self.assertEqual(updated_pattern.highest_date, self.base_date + timedelta(days=4))


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.threshold = Decimal("0.20")
        self.ticker_history_id = 1
        self.base_date = date(2024, 1, 1)

    def test_empty_price_list_returns_unchanged_patterns(self) -> None:
        """Test that empty price list returns patterns unchanged."""
        # Arrange
        pattern = High(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            low_start_price=Decimal("80.00"),
            low_start_date=self.base_date,
            last_updated=self.base_date,
        )

        # Act
        result = process_low_high_patterns([pattern], [], self.threshold)

        # Assert
        self.assertEqual(len(result.active_highs), 1)
        self.assertEqual(len(result.completed_reversals), 0)
        self.assertEqual(result.active_highs[0].low_start_price, Decimal("80.00"))

    def test_null_price_is_skipped(self) -> None:
        """Test that null prices are skipped."""
        # Arrange
        pattern = High(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            low_start_price=Decimal("80.00"),
            low_start_date=self.base_date,
            last_updated=self.base_date,
        )

        new_prices = [
            DatePrice(date=self.base_date + timedelta(days=1), price=None), # pyright: ignore[reportArgumentType]
            DatePrice(date=self.base_date + timedelta(days=2), price=Decimal("96.00")),
        ]

        # Act
        result = process_low_high_patterns([pattern], new_prices, self.threshold)

        # Assert
        updated_pattern = result.active_highs[0]
        # Should have processed day 2, not day 1
        self.assertEqual(updated_pattern.high_threshold_price, Decimal("96.00"))
        self.assertEqual(updated_pattern.last_updated, self.base_date + timedelta(days=2))

    def test_already_processed_dates_are_skipped(self) -> None:
        """Test that dates already processed are skipped."""
        # Arrange
        pattern = High(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            low_start_price=Decimal("80.00"),
            low_start_date=self.base_date,
            last_updated=self.base_date + timedelta(days=2),
        )

        new_prices = [
            DatePrice(date=self.base_date + timedelta(days=1), price=Decimal("90.00")),
            DatePrice(date=self.base_date + timedelta(days=2), price=Decimal("95.00")),
            DatePrice(date=self.base_date + timedelta(days=3), price=Decimal("96.00")),
        ]

        # Act
        result = process_low_high_patterns([pattern], new_prices, self.threshold)

        # Assert
        updated_pattern = result.active_highs[0]
        # Should only have processed day 3
        self.assertEqual(updated_pattern.high_threshold_price, Decimal("96.00"))
        self.assertEqual(updated_pattern.last_updated, self.base_date + timedelta(days=3))

    def test_create_reversal_validates_required_fields(self) -> None:
        """Test that create_reversal raises error for incomplete patterns."""
        # Arrange - Pattern missing low_threshold
        pattern = High(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            low_start_price=Decimal("80.00"),
            low_start_date=self.base_date,
            high_threshold_price=Decimal("96.00"),
            high_threshold_date=self.base_date + timedelta(days=1),
            highest_price=Decimal("100.00"),
            highest_date=self.base_date + timedelta(days=2),
            last_updated=self.base_date + timedelta(days=2),
        )

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            _create_reversal_from_high(
                pattern, Decimal("80.00"), self.base_date + timedelta(days=3)
            )

        self.assertIn("incomplete", str(context.exception).lower())

    def test_multiple_patterns_processed_independently(self) -> None:
        """Test that multiple patterns are processed independently."""
        # Arrange
        pattern1 = High(
            ticker_history_id=1,
            threshold=self.threshold,
            low_start_price=Decimal("80.00"),
            low_start_date=self.base_date,
            last_updated=self.base_date,
        )

        pattern2 = High(
            ticker_history_id=2,
            threshold=self.threshold,
            low_start_price=Decimal("50.00"),
            low_start_date=self.base_date,
            last_updated=self.base_date,
        )

        new_prices = [
            DatePrice(date=self.base_date + timedelta(days=1), price=Decimal("96.00"))
        ]

        # Act
        result = process_low_high_patterns(
            [pattern1, pattern2], new_prices, self.threshold
        )

        # Assert
        # TODO need to check that the value is the same as new_prices[0].price
        self.assertEqual(len(result.active_highs), 2)
        # First pattern should trigger (96 >= 80 * 1.20)
        self.assertIsNotNone(result.active_highs[0].high_threshold_price)
        # Second pattern should trigger (96 >= 50 * 1.20)
        self.assertIsNotNone(result.active_highs[1].high_threshold_price)


if __name__ == "__main__":
    unittest.main()
