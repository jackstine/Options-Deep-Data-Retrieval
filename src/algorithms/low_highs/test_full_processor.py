"""Full lifecycle integration tests for low_high_processor.

This test suite demonstrates the complete behavior of the low/high pattern
algorithm over extended price sequences, showing:
- Multiple complete pattern lifecycles (reversals)
- Pattern spawning when low_threshold is reached
- Multiple active patterns being tracked simultaneously
- How patterns transition through all three states
- Impact of spawning on pattern continuity
"""

from __future__ import annotations

import unittest
from datetime import date, timedelta
from decimal import Decimal

from src.algorithms.low_highs.models.high import High
from src.algorithms.low_highs.processor import process_low_high_patterns
from src.models.date_price import DatePrice


class TestFullLifecycleMultiplePatterns(unittest.TestCase):
    """Test complete algorithm behavior over extended price sequences."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.threshold = Decimal("0.20")
        self.ticker_history_id = 1
        self.base_date = date(2024, 1, 1)

    def test_full_lifecycle_with_spawning_over_30_days(self) -> None:
        """Test full algorithm lifecycle with ~30 days showing multiple reversals.

        This test demonstrates the complete pattern lifecycle including:
        - Pattern A: Completes full reversal cycle (spawns Pattern B at day 6)
        - Pattern B: Spawned pattern that processes remaining prices and completes
        - Pattern C: Spawned from Pattern B, remains active
        - Multiple state transitions and reversals in single call
        - How spawned patterns process remaining prices

        New Behavior:
        - When Pattern A hits low_threshold at $75 (day 6), Pattern B spawns
        - Pattern B immediately processes remaining prices (days 7-30)
        - Pattern B completes its own reversal, spawning Pattern C
        - This generates multiple completed reversals in single processing call

        Timeline (INVERTED from high_low):
        Days 1-2:   Pattern A searching for high (updates low_start to $70)
        Days 3-5:   Pattern A in State 2 (high_threshold hit, tracking highest to $90)
        Day 6:      Pattern A enters State 3 at $75, Pattern B SPAWNS at $75
        Days 7-9:   Pattern A in State 3 waiting for reversal, Pattern B updates low_start to $70
        Day 9:      Pattern A COMPLETES reversal at $70
        Days 10-12: Pattern B still in State 1
        Day 13:     Pattern B enters State 2 at $84 (high_threshold)
        Day 14:     Pattern B tracks highest to $88
        Day 15:     Pattern B enters State 3 at $73.33, Pattern C SPAWNS at $73.33
        Days 16-17: Pattern B in State 3 waiting for reversal, Pattern C updates low_start to $70
        Day 17:     Pattern B COMPLETES reversal at $70
        Days 18-20: Pattern C in State 1, day 20 enters State 2 at $84
        Days 21-22: Pattern C tracks highest to $92
        Day 23:     Pattern C enters State 3 at $76.67, Pattern D SPAWNS at $76.67
        Days 24-28: Pattern C in State 3, Pattern D updates low_start to $72, enters State 2 at $86.40
        Days 29-30: Pattern C in State 3, Pattern D tracks highest to $88, enters State 3 at $73.33, Pattern E SPAWNS

        Expected Result (single processing call):
        - 2 completed reversals (Pattern A at day 9, Pattern B at day 17)
        - 3 active highs (Pattern C in State 3, Pattern D in State 3, Pattern E in State 1)
        """
        # Start with initial pattern
        initial_pattern = High(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            low_start_price=Decimal("80.00"),
            low_start_date=self.base_date,
            last_updated=self.base_date,
        )

        # Generate 30 days of price data (inverted from high_low test)
        new_prices = [
            # Days 1-9: Pattern A lifecycle (will complete)
            DatePrice(date=self.base_date + timedelta(days=1), price=Decimal("75.00")),   # A: low_start → 75
            DatePrice(date=self.base_date + timedelta(days=2), price=Decimal("70.00")),   # A: low_start → 70
            DatePrice(date=self.base_date + timedelta(days=3), price=Decimal("84.00")),   # A: high_threshold (State 2)
            DatePrice(date=self.base_date + timedelta(days=4), price=Decimal("88.00")),   # A: highest → 88
            DatePrice(date=self.base_date + timedelta(days=5), price=Decimal("90.00")),   # A: highest → 90
            DatePrice(date=self.base_date + timedelta(days=6), price=Decimal("75.00")),   # A: low_threshold (State 3), B SPAWNS
            DatePrice(date=self.base_date + timedelta(days=7), price=Decimal("73.00")),   # A: waiting for reversal
            DatePrice(date=self.base_date + timedelta(days=8), price=Decimal("71.00")),   # A: waiting for reversal
            DatePrice(date=self.base_date + timedelta(days=9), price=Decimal("70.00")),   # A: REVERSAL ✓

            # Days 10-30: These process Pattern B in same call (spawned patterns process remaining prices)
            DatePrice(date=self.base_date + timedelta(days=10), price=Decimal("72.00")),
            DatePrice(date=self.base_date + timedelta(days=11), price=Decimal("75.00")),
            DatePrice(date=self.base_date + timedelta(days=12), price=Decimal("78.00")),
            DatePrice(date=self.base_date + timedelta(days=13), price=Decimal("84.00")),  # B: high_threshold
            DatePrice(date=self.base_date + timedelta(days=14), price=Decimal("88.00")),  # B: highest
            DatePrice(date=self.base_date + timedelta(days=15), price=Decimal("73.33")),  # B: low_threshold, C SPAWNS
            DatePrice(date=self.base_date + timedelta(days=16), price=Decimal("72.00")),
            DatePrice(date=self.base_date + timedelta(days=17), price=Decimal("70.00")),  # B: REVERSAL ✓
            DatePrice(date=self.base_date + timedelta(days=18), price=Decimal("75.00")),
            DatePrice(date=self.base_date + timedelta(days=19), price=Decimal("80.00")),
            DatePrice(date=self.base_date + timedelta(days=20), price=Decimal("84.00")),  # C: high_threshold
            DatePrice(date=self.base_date + timedelta(days=21), price=Decimal("88.00")),  # C: highest
            DatePrice(date=self.base_date + timedelta(days=22), price=Decimal("92.00")),  # C: highest
            DatePrice(date=self.base_date + timedelta(days=23), price=Decimal("76.67")),  # C: low_threshold, D SPAWNS
            DatePrice(date=self.base_date + timedelta(days=24), price=Decimal("74.00")),
            DatePrice(date=self.base_date + timedelta(days=25), price=Decimal("72.00")),
            DatePrice(date=self.base_date + timedelta(days=26), price=Decimal("76.00")),
            DatePrice(date=self.base_date + timedelta(days=27), price=Decimal("82.00")),
            DatePrice(date=self.base_date + timedelta(days=28), price=Decimal("86.40")),  # D: high_threshold
            DatePrice(date=self.base_date + timedelta(days=29), price=Decimal("88.00")),  # D: highest
            DatePrice(date=self.base_date + timedelta(days=30), price=Decimal("73.33")),  # D: low_threshold, E SPAWNS
        ]

        # Act
        result = process_low_high_patterns([initial_pattern], new_prices, self.threshold, self.ticker_history_id)

        # Assert: Should have 2 completed reversals (Pattern A and Pattern B)
        self.assertEqual(len(result.completed_reversals), 2,
                        "Should have 2 completed reversals (Pattern A and Pattern B)")

        # Verify Pattern A reversal (first reversal)
        reversal_a = result.completed_reversals[0]
        self.assertEqual(reversal_a.low_start_price, Decimal("70.00"),
                        "Pattern A should have low_start at 70")
        self.assertEqual(reversal_a.high_threshold_price, Decimal("84.00"),
                        "Pattern A should have high_threshold at 84")
        self.assertEqual(reversal_a.highest_price, Decimal("90.00"),
                        "Pattern A should have highest at 90")
        self.assertEqual(reversal_a.low_threshold_price, Decimal("75.00"),
                        "Pattern A should have low_threshold at 75")
        self.assertEqual(reversal_a.reversal_price, Decimal("70.00"),
                        "Pattern A should have reversal at 70")
        self.assertEqual(reversal_a.reversal_date, self.base_date + timedelta(days=9),
                        "Pattern A should complete on day 9")

        # Verify Pattern B reversal (second reversal)
        reversal_b = result.completed_reversals[1]
        self.assertEqual(reversal_b.low_start_price, Decimal("70.00"),
                        "Pattern B should have low_start at 70 (updated from initial $75)")
        self.assertEqual(reversal_b.high_threshold_price, Decimal("84.00"),
                        "Pattern B should have high_threshold at 84")
        self.assertEqual(reversal_b.highest_price, Decimal("88.00"),
                        "Pattern B should have highest at 88")
        self.assertEqual(reversal_b.low_threshold_price, Decimal("73.33"),
                        "Pattern B should have low_threshold at 73.33")
        self.assertEqual(reversal_b.reversal_price, Decimal("70.00"),
                        "Pattern B should have reversal at 70")
        self.assertEqual(reversal_b.reversal_date, self.base_date + timedelta(days=17),
                        "Pattern B should complete on day 17")

        # Assert: Should have 3 active patterns (Patterns C, D, E)
        self.assertEqual(len(result.active_highs), 3,
                        "Should have 3 active patterns (C, D, E from multiple spawns)")

        # Verify Pattern C (spawned from Pattern B at day 15, in State 3)
        pattern_c = result.active_highs[0]
        self.assertEqual(pattern_c.low_start_price, Decimal("70.00"),
                        "Pattern C should have low_start at $70 (updated from initial $73.33)")
        self.assertEqual(pattern_c.low_start_date, self.base_date + timedelta(days=17),
                        "Pattern C low_start should be from day 17")
        self.assertEqual(pattern_c.high_threshold_price, Decimal("84.00"),
                        "Pattern C should have high_threshold at $84")
        self.assertEqual(pattern_c.highest_price, Decimal("92.00"),
                        "Pattern C should have highest at $92")
        self.assertEqual(pattern_c.low_threshold_price, Decimal("74.00"),
                        "Pattern C should have low_threshold at $74")
        self.assertEqual(pattern_c.spawned, True,
                        "Pattern C should have spawned Pattern D")
        self.assertEqual(pattern_c.last_updated, self.base_date + timedelta(days=30),
                        "Pattern C's last_updated should be day 30")
        self.assertEqual(pattern_c.ticker_history_id, self.ticker_history_id)
        self.assertEqual(pattern_c.threshold, self.threshold)

        # Verify Pattern D (spawned from Pattern C at day 23, in State 3)
        pattern_d = result.active_highs[1]
        self.assertEqual(pattern_d.low_start_price, Decimal("72.00"),
                        "Pattern D should have low_start at $72 (updated from initial $76.67)")
        self.assertEqual(pattern_d.high_threshold_price, Decimal("86.40"),
                        "Pattern D should have high_threshold at $86.40")
        self.assertEqual(pattern_d.highest_price, Decimal("88.00"),
                        "Pattern D should have highest at $88")
        self.assertEqual(pattern_d.low_threshold_price, Decimal("73.33"),
                        "Pattern D should have low_threshold at $73.33")
        self.assertEqual(pattern_d.spawned, True,
                        "Pattern D should have spawned Pattern E")
        self.assertEqual(pattern_d.last_updated, self.base_date + timedelta(days=30),
                        "Pattern D's last_updated should be day 30")

        # Verify Pattern E (spawned from Pattern D at day 30, in State 1)
        pattern_e = result.active_highs[2]
        self.assertEqual(pattern_e.low_start_price, Decimal("73.33"),
                        "Pattern E should start at $73.33")
        self.assertEqual(pattern_e.low_start_date, self.base_date + timedelta(days=30),
                        "Pattern E should start on day 30")
        self.assertIsNone(pattern_e.high_threshold_price,
                        "Pattern E should be in State 1 (no high_threshold yet)")
        self.assertIsNone(pattern_e.highest_price,
                        "Pattern E should be in State 1 (no highest yet)")
        self.assertIsNone(pattern_e.low_threshold_price,
                        "Pattern E should be in State 1 (no low_threshold yet)")
        self.assertEqual(pattern_e.spawned, False,
                        "Pattern E has not spawned yet")
        self.assertEqual(pattern_e.last_updated, self.base_date + timedelta(days=30),
                        "Pattern E's last_updated should be day 30")
        self.assertEqual(pattern_e.ticker_history_id, self.ticker_history_id)
        self.assertEqual(pattern_e.threshold, self.threshold)


if __name__ == "__main__":
    unittest.main()
