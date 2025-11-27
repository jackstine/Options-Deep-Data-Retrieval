"""Comprehensive unit tests for high_low_processor state machine.

This test suite covers the core algorithm logic for processing high/low patterns:
- State 1: Searching for low_threshold
- State 2: Tracking lowest, waiting for high_threshold
- State 3: Waiting for rebound
- Pattern spawning logic
- Rebound creation and completion
- Edge cases and error handling
"""

from __future__ import annotations

import unittest
from datetime import date, timedelta
from decimal import Decimal

from src.algorithms.high_lows.models.low import Low
from src.algorithms.high_lows.processor import (
    _create_rebound_from_low,
    process_high_low_patterns,
)
from src.models.date_price import DatePrice


class TestProcessorStateOne(unittest.TestCase):
    """Test State 1: Searching for low_threshold."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.threshold = Decimal("0.20")
        self.ticker_history_id = 1
        self.base_date = date(2024, 1, 1)

    def test_price_drops_by_threshold_sets_low_threshold(self) -> None:
        """Test that price drop by threshold sets low_threshold and lowest."""
        # Arrange
        pattern = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            last_updated=self.base_date,
        )

        # Price drops to 80 (20% drop)
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=1),
                price=Decimal("80.00"),
            )
        ]

        # Act
        result = process_high_low_patterns([pattern], new_prices, self.threshold)

        # Assert
        self.assertEqual(len(result.active_lows), 1)
        self.assertEqual(len(result.completed_rebounds), 0)

        updated_pattern = result.active_lows[0]
        self.assertEqual(updated_pattern.low_threshold_price, Decimal("80.00"))
        self.assertEqual(
            updated_pattern.low_threshold_date, self.base_date + timedelta(days=1)
        )
        self.assertEqual(updated_pattern.lowest_price, Decimal("80.00"))
        self.assertEqual(updated_pattern.lowest_date, self.base_date + timedelta(days=1))

    def test_price_exceeds_high_start_updates_peak(self) -> None:
        """Test that price exceeding high_start updates the peak."""
        # Arrange
        pattern = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            last_updated=self.base_date,
        )

        # Price goes up to 110
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=1),
                price=Decimal("110.00"),
            )
        ]

        # Act
        result = process_high_low_patterns([pattern], new_prices, self.threshold)

        # Assert
        self.assertEqual(len(result.active_lows), 1)
        updated_pattern = result.active_lows[0]
        self.assertEqual(updated_pattern.high_start_price, Decimal("110.00"))
        self.assertEqual(
            updated_pattern.high_start_date, self.base_date + timedelta(days=1)
        )
        # low_threshold should still be None
        self.assertIsNone(updated_pattern.low_threshold_price)

    def test_price_between_threshold_and_high_no_change(self) -> None:
        """Test that price between threshold and high causes no state change."""
        # Arrange
        pattern = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            last_updated=self.base_date,
        )

        # Price goes to 85 (15% drop, less than 20% threshold)
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=1),
                price=Decimal("85.00"),
            )
        ]

        # Act
        result = process_high_low_patterns([pattern], new_prices, self.threshold)

        # Assert
        self.assertEqual(len(result.active_lows), 1)
        updated_pattern = result.active_lows[0]
        # No state change - still searching
        self.assertIsNone(updated_pattern.low_threshold_price)
        self.assertEqual(updated_pattern.high_start_price, Decimal("100.00"))


class TestProcessorStateTwo(unittest.TestCase):
    """Test State 2: Tracking lowest, waiting for high_threshold."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.threshold = Decimal("0.20")
        self.ticker_history_id = 1
        self.base_date = date(2024, 1, 1)

    def test_price_recovers_by_threshold_sets_high_threshold(self) -> None:
        """Test that price recovery by threshold sets high_threshold."""
        # Arrange - Pattern already in State 2 (low_threshold set), already spawned
        pattern = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            low_threshold_price=Decimal("80.00"),
            low_threshold_date=self.base_date + timedelta(days=1),
            lowest_price=Decimal("75.00"),
            lowest_date=self.base_date + timedelta(days=2),
            last_updated=self.base_date + timedelta(days=2),
            spawned=True,  # Already spawned, won't spawn again
        )

        # Price recovers to 90 (20% above lowest of 75)
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=3),
                price=Decimal("90.00"),
            )
        ]

        # Act
        result = process_high_low_patterns([pattern], new_prices, self.threshold)

        # Assert
        self.assertEqual(len(result.active_lows), 1)
        updated_pattern = result.active_lows[0]
        self.assertEqual(updated_pattern.high_threshold_price, Decimal("90.00"))
        self.assertEqual(
            updated_pattern.high_threshold_date, self.base_date + timedelta(days=3)
        )

    def test_pattern_spawns_when_high_threshold_reached(self) -> None:
        """Test that new pattern spawns when high_threshold is reached."""
        # Arrange - Pattern in State 2, not yet spawned
        pattern = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            low_threshold_price=Decimal("80.00"),
            low_threshold_date=self.base_date + timedelta(days=1),
            lowest_price=Decimal("75.00"),
            lowest_date=self.base_date + timedelta(days=2),
            last_updated=self.base_date + timedelta(days=2),
            spawned=False,
        )

        # Price recovers to 90
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=3),
                price=Decimal("90.00"),
            )
        ]

        # Act
        result = process_high_low_patterns([pattern], new_prices, self.threshold)

        # Assert
        # Should have original pattern + spawned pattern
        self.assertEqual(len(result.active_lows), 2)

        # Find the spawned pattern
        spawned = [p for p in result.active_lows if p.spawned is False]
        self.assertEqual(len(spawned), 1)

        spawned_pattern = spawned[0]
        self.assertEqual(spawned_pattern.high_start_price, Decimal("90.00"))
        self.assertEqual(
            spawned_pattern.high_start_date, self.base_date + timedelta(days=3)
        )
        self.assertIsNone(spawned_pattern.low_threshold_price)

    def test_immediate_rebound_at_high_threshold_completes_pattern(self) -> None:
        """Test that pattern completes if price >= high_start at high_threshold."""
        # Arrange - Pattern in State 2, lowest at 80, high_start at 100
        pattern = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            low_threshold_price=Decimal("80.00"),
            low_threshold_date=self.base_date + timedelta(days=1),
            lowest_price=Decimal("80.00"),
            lowest_date=self.base_date + timedelta(days=2),
            last_updated=self.base_date + timedelta(days=2),
        )

        # Price recovers to 100 (meets both high_threshold and rebound)
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=3),
                price=Decimal("100.00"),
            )
        ]

        # Act
        result = process_high_low_patterns([pattern], new_prices, self.threshold)

        # Assert
        # Pattern completes immediately - no active lows (except maybe spawned)
        self.assertEqual(len(result.completed_rebounds), 1)
        self.assertEqual(len(result.active_lows), 1)    # spawns a new active low as well

        rebound = result.completed_rebounds[0]
        self.assertEqual(rebound.rebound_price, Decimal("100.00"))
        self.assertEqual(rebound.rebound_date, self.base_date + timedelta(days=3))
        self.assertEqual(rebound.high_start_price, Decimal("100.00"))

    def test_price_continues_to_fall_updates_lowest(self) -> None:
        """Test that price continuing to fall updates lowest."""
        # Arrange - Pattern in State 2
        pattern = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            low_threshold_price=Decimal("80.00"),
            low_threshold_date=self.base_date + timedelta(days=1),
            lowest_price=Decimal("75.00"),
            lowest_date=self.base_date + timedelta(days=2),
            last_updated=self.base_date + timedelta(days=2),
        )

        # Price drops to 70
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=3),
                price=Decimal("70.00"),
            )
        ]

        # Act
        result = process_high_low_patterns([pattern], new_prices, self.threshold)

        # Assert
        self.assertEqual(len(result.active_lows), 1)
        updated_pattern = result.active_lows[0]
        self.assertEqual(updated_pattern.lowest_price, Decimal("70.00"))
        self.assertEqual(updated_pattern.lowest_date, self.base_date + timedelta(days=3))
        # Should still be in State 2
        self.assertIsNone(updated_pattern.high_threshold_price)


class TestProcessorStateThree(unittest.TestCase):
    """Test State 3: Waiting for rebound."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.threshold = Decimal("0.20")
        self.ticker_history_id = 1
        self.base_date = date(2024, 1, 1)

    def test_price_returns_to_high_start_completes_rebound(self) -> None:
        """Test that price returning to high_start completes the pattern.

        With new behavior: Pattern that hasn't spawned creates new pattern at rebound.
        """
        # Arrange - Pattern in State 3 (high_threshold set)
        pattern = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            low_threshold_price=Decimal("80.00"),
            low_threshold_date=self.base_date + timedelta(days=1),
            lowest_price=Decimal("75.00"),
            lowest_date=self.base_date + timedelta(days=2),
            high_threshold_price=Decimal("90.00"),
            high_threshold_date=self.base_date + timedelta(days=3),
            last_updated=self.base_date + timedelta(days=3),
        )

        # Price returns to 100
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=4),
                price=Decimal("100.00"),
            )
        ]

        # Act
        result = process_high_low_patterns([pattern], new_prices, self.threshold)

        # Assert - Pattern completes AND creates new pattern at rebound
        self.assertEqual(len(result.completed_rebounds), 1)
        self.assertEqual(len(result.active_lows), 1,
                        "Should have 1 active low (new pattern created at rebound)")

        rebound = result.completed_rebounds[0]
        self.assertEqual(rebound.rebound_price, Decimal("100.00"))
        self.assertEqual(rebound.rebound_date, self.base_date + timedelta(days=4))

        # Verify new pattern created at rebound price
        new_pattern = result.active_lows[0]
        self.assertEqual(new_pattern.high_start_price, Decimal("100.00"))
        self.assertEqual(new_pattern.high_start_date, self.base_date + timedelta(days=4))
        self.assertIsNone(new_pattern.low_threshold_price)
        self.assertEqual(new_pattern.spawned, False)


    def test_completes_rebound_then_what(self) -> None:
        """Test that pattern completes rebound and continues with new pattern.

        With new behavior: After rebound, new pattern created at rebound price
        and processes remaining prices.
        """
        # Arrange - Pattern in State 3 (high_threshold set)
        pattern = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            low_threshold_price=Decimal("80.00"),
            low_threshold_date=self.base_date + timedelta(days=1),
            lowest_price=Decimal("75.00"),
            lowest_date=self.base_date + timedelta(days=2),
            high_threshold_price=Decimal("90.00"),
            high_threshold_date=self.base_date + timedelta(days=3),
            last_updated=self.base_date + timedelta(days=3),
        )

        # Price returns to 100, then continues
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=4),
                price=Decimal("100.00"),
            ),
            DatePrice(
                date=self.base_date + timedelta(days=5),
                price=Decimal("105.00"),
            ),
            DatePrice(
                date=self.base_date + timedelta(days=6),
                price=Decimal("103.00"),
            )
        ]

        # Act
        result = process_high_low_patterns([pattern], new_prices, self.threshold)

        # Assert - Pattern completes AND new pattern processes remaining prices
        self.assertEqual(len(result.completed_rebounds), 1)
        self.assertEqual(len(result.active_lows), 1,
                        "Should have 1 active low (new pattern created at rebound)")

        rebound = result.completed_rebounds[0]
        self.assertEqual(rebound.rebound_price, Decimal("100.00"))
        self.assertEqual(rebound.rebound_date, self.base_date + timedelta(days=4))

        # Verify new pattern processed remaining prices
        new_pattern = result.active_lows[0]
        self.assertEqual(new_pattern.high_start_price, Decimal("105.00"),
                        "New pattern should update high_start to $105")
        self.assertEqual(new_pattern.high_start_date, self.base_date + timedelta(days=5))
        self.assertIsNone(new_pattern.low_threshold_price,
                        "New pattern should still be in State 1")
        self.assertEqual(new_pattern.spawned, False)
        self.assertEqual(new_pattern.last_updated, self.base_date + timedelta(days=6),
                        "New pattern should have processed all remaining prices")

    def test_price_falls_below_lowest_resets_to_state_two(self) -> None:
        """Test that price falling below lowest resets high_threshold."""
        # Arrange - Pattern in State 3
        pattern = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            low_threshold_price=Decimal("80.00"),
            low_threshold_date=self.base_date + timedelta(days=1),
            lowest_price=Decimal("75.00"),
            lowest_date=self.base_date + timedelta(days=2),
            high_threshold_price=Decimal("90.00"),
            high_threshold_date=self.base_date + timedelta(days=3),
            number_of_high_thresholds=1,  # Counter was incremented when high_threshold was set
            last_updated=self.base_date + timedelta(days=3),
        )

        # Price drops to 70 (below lowest)
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=4),
                price=Decimal("70.00"),
            )
        ]

        # Act
        result = process_high_low_patterns([pattern], new_prices, self.threshold)

        # Assert
        self.assertEqual(len(result.active_lows), 1)
        self.assertEqual(len(result.completed_rebounds), 0)

        updated_pattern = result.active_lows[0]
        # High threshold should be reset
        self.assertIsNone(updated_pattern.high_threshold_price)
        self.assertIsNone(updated_pattern.high_threshold_date)
        # Lowest should be updated
        self.assertEqual(updated_pattern.lowest_price, Decimal("70.00"))
        self.assertEqual(updated_pattern.lowest_date, self.base_date + timedelta(days=4))
        # Counter should remain unchanged (retains previous count)
        self.assertEqual(updated_pattern.number_of_high_thresholds, 1)

    def test_high_threshold_counter_increments_on_each_crossing(self) -> None:
        """Test that number_of_high_thresholds increments on each threshold crossing."""
        # Arrange - Pattern in State 2 (low_threshold set, waiting for high_threshold)
        pattern = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            low_threshold_price=Decimal("80.00"),
            low_threshold_date=self.base_date + timedelta(days=1),
            lowest_price=Decimal("75.00"),
            lowest_date=self.base_date + timedelta(days=2),
            last_updated=self.base_date + timedelta(days=2),
            spawned=False,
        )

        # Simulate oscillating pattern:
        # Day 3: Rise to 90.00 (crosses high_threshold) - count should be 1
        # Day 4: Fall to 70.00 (below lowest, resets high_threshold) - count stays 1
        # Day 5: Rise to 84.00 (crosses high_threshold again) - count should be 2
        # Day 6: Fall to 65.00 (below lowest, resets high_threshold) - count stays 2
        # Day 7: Rise to 78.00 (crosses high_threshold again) - count should be 3
        new_prices = [
            DatePrice(date=self.base_date + timedelta(days=3), price=Decimal("90.00")),  # 1st crossing
            DatePrice(date=self.base_date + timedelta(days=4), price=Decimal("70.00")),  # Reset
            DatePrice(date=self.base_date + timedelta(days=5), price=Decimal("84.00")),  # 2nd crossing
            DatePrice(date=self.base_date + timedelta(days=6), price=Decimal("65.00")),  # Reset
            DatePrice(date=self.base_date + timedelta(days=7), price=Decimal("78.00")),  # 3rd crossing
        ]

        # Act
        result = process_high_low_patterns([pattern], new_prices, self.threshold)

        # Assert
        self.assertGreaterEqual(len(result.active_lows), 1)  # At least original pattern
        self.assertEqual(len(result.completed_rebounds), 0)

        # Find the original pattern by checking which one started at high_start_price 100
        original_pattern = None
        for p in result.active_lows:
            if p.high_start_price == Decimal("100.00"):
                original_pattern = p
                break

        self.assertIsNotNone(original_pattern, "Original pattern should still be active")

        # Should have crossed high_threshold 3 times
        self.assertEqual(original_pattern.number_of_high_thresholds, 3)     # pyright: ignore[reportOptionalMemberAccess]
        # Should still be in State 3 (high_threshold set, waiting for rebound)
        self.assertIsNotNone(original_pattern.high_threshold_price)         # pyright: ignore[reportOptionalMemberAccess]
        self.assertEqual(original_pattern.lowest_price, Decimal("65.00"))   # pyright: ignore[reportOptionalMemberAccess]


class TestProcessorEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.threshold = Decimal("0.20")
        self.ticker_history_id = 1
        self.base_date = date(2024, 1, 1)

    def test_empty_patterns_list_returns_empty_result(self) -> None:
        """Test processing with no patterns returns empty result."""
        # Arrange
        new_prices = [
            DatePrice(
                date=self.base_date,
                price=Decimal("100.00"),
            )
        ]

        # Act
        result = process_high_low_patterns([], new_prices, self.threshold)

        # Assert
        self.assertEqual(len(result.active_lows), 0)
        self.assertEqual(len(result.completed_rebounds), 0)

    def test_empty_prices_list_returns_unchanged_patterns(self) -> None:
        """Test processing with no prices returns patterns unchanged."""
        # Arrange
        pattern = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            last_updated=self.base_date,
        )

        # Act
        result = process_high_low_patterns([pattern], [], self.threshold)

        # Assert
        self.assertEqual(len(result.active_lows), 1)
        self.assertEqual(len(result.completed_rebounds), 0)
        # Pattern should be unchanged
        unchanged_pattern = result.active_lows[0]
        self.assertEqual(unchanged_pattern.high_start_price, Decimal("100.00"))
        self.assertEqual(unchanged_pattern.high_start_date, self.base_date)
        self.assertIsNone(unchanged_pattern.low_threshold_price)
        self.assertIsNone(unchanged_pattern.low_threshold_date)
        self.assertIsNone(unchanged_pattern.lowest_price)
        self.assertIsNone(unchanged_pattern.lowest_date)
        self.assertIsNone(unchanged_pattern.high_threshold_price)
        self.assertIsNone(unchanged_pattern.high_threshold_date)
        self.assertEqual(unchanged_pattern.last_updated, self.base_date)
        self.assertEqual(unchanged_pattern.spawned, False)
        self.assertEqual(unchanged_pattern.ticker_history_id, self.ticker_history_id)
        self.assertEqual(unchanged_pattern.threshold, self.threshold)

    def test_null_price_is_skipped(self) -> None:
        """Test that prices with None close are skipped."""
        # Arrange
        pattern = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            last_updated=self.base_date,
        )

        # Price with None close
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=1),
                price=None,  # pyright: ignore[reportArgumentType]
            )
        ]

        # Act
        result = process_high_low_patterns([pattern], new_prices, self.threshold)

        # Assert
        self.assertEqual(len(result.active_lows), 1)
        # Pattern should be unchanged (except last_updated might change)
        updated_pattern = result.active_lows[0]
        self.assertEqual(updated_pattern.high_start_price, Decimal("100.00"))
        self.assertEqual(updated_pattern.high_start_date, self.base_date)
        self.assertIsNone(updated_pattern.low_threshold_price)
        self.assertIsNone(updated_pattern.low_threshold_date)
        self.assertIsNone(updated_pattern.lowest_price)
        self.assertIsNone(updated_pattern.lowest_date)
        self.assertIsNone(updated_pattern.high_threshold_price)
        self.assertIsNone(updated_pattern.high_threshold_date)
        self.assertEqual(updated_pattern.last_updated, self.base_date)
        self.assertEqual(updated_pattern.spawned, False)
        self.assertEqual(updated_pattern.ticker_history_id, self.ticker_history_id)
        self.assertEqual(updated_pattern.threshold, self.threshold)

    def test_prices_already_processed_are_skipped(self) -> None:
        """Test that prices with date <= last_updated are skipped."""
        # Arrange
        pattern = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            last_updated=self.base_date + timedelta(days=5),  # Already processed up to day 5
        )

        # Price on day 3 (already processed)
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=3),
                price=Decimal("80.00"),  # Would trigger low_threshold
            )
        ]

        # Act
        result = process_high_low_patterns([pattern], new_prices, self.threshold)

        # Assert
        self.assertEqual(len(result.active_lows), 1)
        updated_pattern = result.active_lows[0]
        # Should not have triggered low_threshold
        self.assertEqual(updated_pattern.high_start_price, Decimal("100.00"))
        self.assertEqual(updated_pattern.high_start_date, self.base_date)
        self.assertIsNone(updated_pattern.low_threshold_price)
        self.assertIsNone(updated_pattern.low_threshold_date)
        self.assertIsNone(updated_pattern.lowest_price)
        self.assertIsNone(updated_pattern.lowest_date)
        self.assertIsNone(updated_pattern.high_threshold_price)
        self.assertIsNone(updated_pattern.high_threshold_date)
        self.assertEqual(updated_pattern.last_updated, self.base_date + timedelta(days=5))
        self.assertEqual(updated_pattern.spawned, False)
        self.assertEqual(updated_pattern.ticker_history_id, self.ticker_history_id)
        self.assertEqual(updated_pattern.threshold, self.threshold)

    def test_prices_are_sorted_chronologically(self) -> None:
        """Test that prices are processed in chronological order."""
        # Arrange
        pattern = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            last_updated=self.base_date,
        )

        # Prices out of order
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=3),
                price=Decimal("70.00"),
            ),
            DatePrice(
                date=self.base_date + timedelta(days=1),
                price=Decimal("80.00"),  # Should be processed first
            ),
        ]

        # Act
        result = process_high_low_patterns([pattern], new_prices, self.threshold)

        # Assert
        self.assertEqual(len(result.active_lows), 1)
        updated_pattern = result.active_lows[0]
        # Should have processed day 1 first (80.00) setting low_threshold
        self.assertEqual(updated_pattern.low_threshold_price, Decimal("80.00"))
        self.assertEqual(
            updated_pattern.low_threshold_date, self.base_date + timedelta(days=1)
        )

    def test_multiple_patterns_processed_independently(self) -> None:
        """Test that multiple patterns are processed independently."""
        # Arrange - Two patterns with different high_start prices
        pattern1 = Low(
            id=1,
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            last_updated=self.base_date,
        )

        pattern2 = Low(
            id=2,
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date - timedelta(days=10),  # Older pattern
            low_threshold_price=Decimal("80.00"),
            low_threshold_date=self.base_date - timedelta(days=5),
            lowest_price=Decimal("75.00"),
            lowest_date=self.base_date - timedelta(days=3),
            last_updated=self.base_date,
        )

        # Price that affects both patterns differently
        new_prices = [
            DatePrice(
                date=self.base_date + timedelta(days=1),
                price=Decimal("77.00"),
            )
        ]

        # Act
        result = process_high_low_patterns([pattern1, pattern2], new_prices, self.threshold)

        # Assert
        self.assertEqual(len(result.active_lows), 2)

        # Find each pattern by ID
        pattern1_results = [p for p in result.active_lows if p.id == 1]
        pattern2_results = [p for p in result.active_lows if p.id == 2]

        # Pattern 1 should have triggered low_threshold
        self.assertEqual(len(pattern1_results), 1)
        pattern1_result = pattern1_results[0]
        self.assertEqual(pattern1_result.low_threshold_price, Decimal("77.00"))
        self.assertEqual(pattern1_result.low_threshold_date, self.base_date + timedelta(days=1))
        self.assertEqual(pattern1_result.lowest_price, Decimal("77.00"))
        self.assertEqual(pattern1_result.lowest_date, self.base_date + timedelta(days=1))

        # Pattern 2 should have updated lowest (price <= current lowest)
        self.assertEqual(len(pattern2_results), 1)
        pattern2_result = pattern2_results[0]
        self.assertEqual(pattern2_result.lowest_price, Decimal("75.00"))  # Unchanged (77 > 75)
        self.assertEqual(pattern2_result.low_threshold_price, Decimal("80.00"))  # Unchanged


class TestCreateReboundFromLow(unittest.TestCase):
    """Test _create_rebound_from_low helper function."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.threshold = Decimal("0.20")
        self.ticker_history_id = 1
        self.base_date = date(2024, 1, 1)

    def test_create_rebound_from_complete_low(self) -> None:
        """Test creating rebound from complete low pattern."""
        # Arrange
        low = Low(
            id=1,
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            low_threshold_price=Decimal("80.00"),
            low_threshold_date=self.base_date + timedelta(days=1),
            lowest_price=Decimal("75.00"),
            lowest_date=self.base_date + timedelta(days=2),
            high_threshold_price=Decimal("90.00"),
            high_threshold_date=self.base_date + timedelta(days=3),
            last_updated=self.base_date + timedelta(days=3),
        )

        rebound_price = Decimal("100.00")
        rebound_date = self.base_date + timedelta(days=4)

        # Act
        rebound = _create_rebound_from_low(low, rebound_price, rebound_date)

        # Assert
        self.assertEqual(rebound.ticker_history_id, self.ticker_history_id)
        self.assertEqual(rebound.threshold, self.threshold)
        self.assertEqual(rebound.high_start_price, Decimal("100.00"))
        self.assertEqual(rebound.high_start_date, self.base_date)
        self.assertEqual(rebound.low_threshold_price, Decimal("80.00"))
        self.assertEqual(rebound.low_threshold_date, self.base_date + timedelta(days=1))
        self.assertEqual(rebound.lowest_price, Decimal("75.00"))
        self.assertEqual(rebound.lowest_date, self.base_date + timedelta(days=2))
        self.assertEqual(rebound.high_threshold_price, Decimal("90.00"))
        self.assertEqual(rebound.high_threshold_date, self.base_date + timedelta(days=3))
        self.assertEqual(rebound.rebound_price, Decimal("100.00"))
        self.assertEqual(rebound.rebound_date, self.base_date + timedelta(days=4))

    def test_create_rebound_from_incomplete_low_raises_error(self) -> None:
        """Test that creating rebound from incomplete low raises ValueError."""
        # Arrange - Low missing high_threshold
        low = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            last_updated=self.base_date + timedelta(days=2),
            low_threshold_price=Decimal("80.00"),
            low_threshold_date=self.base_date + timedelta(days=1),
            lowest_price=Decimal("75.00"),
            lowest_date=self.base_date + timedelta(days=2),
            # Missing high_threshold_price and high_threshold_date
        )

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            _create_rebound_from_low(low, Decimal("100.00"), self.base_date + timedelta(days=4))

        self.assertIn("Cannot create rebound from incomplete low pattern", str(context.exception))

    def test_create_rebound_missing_low_threshold_raises_error(self) -> None:
        """Test that missing low_threshold raises ValueError."""
        # Arrange
        low = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            last_updated=self.base_date + timedelta(days=3),
            # Missing low_threshold_price and low_threshold_date
            lowest_price=Decimal("75.00"),
            lowest_date=self.base_date + timedelta(days=2),
            high_threshold_price=Decimal("90.00"),
            high_threshold_date=self.base_date + timedelta(days=3),
        )

        # Act & Assert
        with self.assertRaises(ValueError):
            _create_rebound_from_low(low, Decimal("100.00"), self.base_date + timedelta(days=4))

    def test_create_rebound_missing_lowest_raises_error(self) -> None:
        """Test that missing lowest raises ValueError."""
        # Arrange
        low = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            last_updated=self.base_date + timedelta(days=3),
            low_threshold_price=Decimal("80.00"),
            low_threshold_date=self.base_date + timedelta(days=1),
            # Missing lowest_price and lowest_date
            high_threshold_price=Decimal("90.00"),
            high_threshold_date=self.base_date + timedelta(days=3),
        )

        # Act & Assert
        with self.assertRaises(ValueError):
            _create_rebound_from_low(low, Decimal("100.00"), self.base_date + timedelta(days=4))


if __name__ == "__main__":
    unittest.main()
