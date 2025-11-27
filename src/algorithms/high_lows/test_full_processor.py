"""Full lifecycle integration tests for high_low_processor.

This test suite demonstrates the complete behavior of the high/low pattern
algorithm over extended price sequences, showing:
- Multiple complete pattern lifecycles (rebounds)
- Pattern spawning when high_threshold is reached
- Multiple active patterns being tracked simultaneously
- How patterns transition through all three states
- Impact of spawning on pattern continuity
"""

from __future__ import annotations

import unittest
from datetime import date, timedelta
from decimal import Decimal

from src.algorithms.high_lows.models.low import Low
from src.algorithms.high_lows.processor import process_high_low_patterns
from src.models.date_price import DatePrice


class TestFullLifecycleMultiplePatterns(unittest.TestCase):
    """Test complete algorithm behavior over extended price sequences."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.threshold = Decimal("0.20")
        self.ticker_history_id = 1
        self.base_date = date(2024, 1, 1)

    def test_full_lifecycle_with_spawning_over_30_days(self) -> None:
        """Test full algorithm lifecycle with ~30 days showing multiple rebounds.

        This test demonstrates the complete pattern lifecycle including:
        - Pattern A: Completes full rebound cycle (spawns Pattern B at day 6)
        - Pattern B: Spawned pattern that processes remaining prices and completes
        - Pattern C: Spawned from Pattern B, remains active
        - Multiple state transitions and rebounds in single call
        - How spawned patterns process remaining prices

        New Behavior:
        - When Pattern A hits high_threshold at $96 (day 6), Pattern B spawns
        - Pattern B immediately processes remaining prices (days 7-30)
        - Pattern B completes its own rebound, spawning Pattern C
        - This generates multiple completed rebounds in single processing call

        Timeline:
        Days 1-2:   Pattern A searching for low (updates high_start to $110)
        Days 3-5:   Pattern A in State 2 (low_threshold hit, tracking lowest to $80)
        Day 6:      Pattern A enters State 3 at $96, Pattern B SPAWNS at $96
        Days 7-9:   Pattern A in State 3 waiting for rebound, Pattern B updates high_start to $110
        Day 9:      Pattern A COMPLETES rebound at $110
        Days 10-12: Pattern B still in State 1
        Day 13:     Pattern B enters State 2 at $88 (low_threshold)
        Day 14:     Pattern B tracks lowest to $85
        Day 15:     Pattern B enters State 3 at $102, Pattern C SPAWNS at $102
        Days 16-17: Pattern B in State 3 waiting for rebound, Pattern C updates high_start to $110
        Day 17:     Pattern B COMPLETES rebound at $110
        Days 18-20: Pattern C in State 1, day 20 enters State 2 at $88
        Days 21-22: Pattern C tracks lowest to $82
        Day 23:     Pattern C enters State 3 at $98.40, Pattern D SPAWNS at $98.40
        Days 24-28: Pattern C in State 3, Pattern D updates high_start to $108, enters State 2 at $86.40
        Days 29-30: Pattern C in State 3, Pattern D tracks lowest to $85, enters State 3 at $102, Pattern E SPAWNS

        Expected Result (single processing call):
        - 2 completed rebounds (Pattern A at day 9, Pattern B at day 17)
        - 3 active lows (Pattern C in State 3, Pattern D in State 3, Pattern E in State 1)
        """
        # Start with initial pattern
        initial_pattern = Low(
            ticker_history_id=self.ticker_history_id,
            threshold=self.threshold,
            high_start_price=Decimal("100.00"),
            high_start_date=self.base_date,
            last_updated=self.base_date,
        )

        # Generate 30 days of price data
        new_prices = [
            # Days 1-9: Pattern A lifecycle (will complete)
            DatePrice(date=self.base_date + timedelta(days=1), price=Decimal("105.00")),  # A: high_start → 105
            DatePrice(date=self.base_date + timedelta(days=2), price=Decimal("110.00")),  # A: high_start → 110
            DatePrice(date=self.base_date + timedelta(days=3), price=Decimal("88.00")),   # A: low_threshold (State 2)
            DatePrice(date=self.base_date + timedelta(days=4), price=Decimal("82.00")),   # A: lowest → 82
            DatePrice(date=self.base_date + timedelta(days=5), price=Decimal("80.00")),   # A: lowest → 80
            DatePrice(date=self.base_date + timedelta(days=6), price=Decimal("96.00")),   # A: high_threshold (State 3), B SPAWNS
            DatePrice(date=self.base_date + timedelta(days=7), price=Decimal("100.00")),  # A: waiting for rebound
            DatePrice(date=self.base_date + timedelta(days=8), price=Decimal("105.00")),  # A: waiting for rebound
            DatePrice(date=self.base_date + timedelta(days=9), price=Decimal("110.00")),  # A: REBOUND ✓

            # Days 10-30: These would process Pattern B in daily pipeline's next calls
            # Pattern B would not process these in the same call where it spawns
            DatePrice(date=self.base_date + timedelta(days=10), price=Decimal("105.00")),
            DatePrice(date=self.base_date + timedelta(days=11), price=Decimal("100.00")),
            DatePrice(date=self.base_date + timedelta(days=12), price=Decimal("95.00")),
            DatePrice(date=self.base_date + timedelta(days=13), price=Decimal("88.00")),
            DatePrice(date=self.base_date + timedelta(days=14), price=Decimal("85.00")),
            DatePrice(date=self.base_date + timedelta(days=15), price=Decimal("102.00")),
            DatePrice(date=self.base_date + timedelta(days=16), price=Decimal("108.00")),
            DatePrice(date=self.base_date + timedelta(days=17), price=Decimal("110.00")),
            DatePrice(date=self.base_date + timedelta(days=18), price=Decimal("105.00")),
            DatePrice(date=self.base_date + timedelta(days=19), price=Decimal("92.00")),
            DatePrice(date=self.base_date + timedelta(days=20), price=Decimal("88.00")),
            DatePrice(date=self.base_date + timedelta(days=21), price=Decimal("84.00")),
            DatePrice(date=self.base_date + timedelta(days=22), price=Decimal("82.00")),
            DatePrice(date=self.base_date + timedelta(days=23), price=Decimal("98.40")),
            DatePrice(date=self.base_date + timedelta(days=24), price=Decimal("105.00")),
            DatePrice(date=self.base_date + timedelta(days=25), price=Decimal("108.00")),
            DatePrice(date=self.base_date + timedelta(days=26), price=Decimal("102.00")),
            DatePrice(date=self.base_date + timedelta(days=27), price=Decimal("95.00")),
            DatePrice(date=self.base_date + timedelta(days=28), price=Decimal("86.40")),
            DatePrice(date=self.base_date + timedelta(days=29), price=Decimal("85.00")),
            DatePrice(date=self.base_date + timedelta(days=30), price=Decimal("102.00")),
        ]

        # Act
        result = process_high_low_patterns([initial_pattern], new_prices, self.threshold)

        # Assert: Should have 2 completed rebounds (Pattern A and Pattern B)
        self.assertEqual(len(result.completed_rebounds), 2,
                        "Should have 2 completed rebounds (Pattern A and Pattern B)")

        # Verify Pattern A rebound (first rebound)
        rebound_a = result.completed_rebounds[0]
        self.assertEqual(rebound_a.high_start_price, Decimal("110.00"),
                        "Pattern A should have high_start at 110")
        self.assertEqual(rebound_a.low_threshold_price, Decimal("88.00"),
                        "Pattern A should have low_threshold at 88")
        self.assertEqual(rebound_a.lowest_price, Decimal("80.00"),
                        "Pattern A should have lowest at 80")
        self.assertEqual(rebound_a.high_threshold_price, Decimal("96.00"),
                        "Pattern A should have high_threshold at 96")
        self.assertEqual(rebound_a.rebound_price, Decimal("110.00"),
                        "Pattern A should have rebound at 110")
        self.assertEqual(rebound_a.rebound_date, self.base_date + timedelta(days=9),
                        "Pattern A should complete on day 9")

        # Verify Pattern B rebound (second rebound)
        rebound_b = result.completed_rebounds[1]
        self.assertEqual(rebound_b.high_start_price, Decimal("110.00"),
                        "Pattern B should have high_start at 110 (updated from initial $96)")
        self.assertEqual(rebound_b.low_threshold_price, Decimal("88.00"),
                        "Pattern B should have low_threshold at 88")
        self.assertEqual(rebound_b.lowest_price, Decimal("85.00"),
                        "Pattern B should have lowest at 85")
        self.assertEqual(rebound_b.high_threshold_price, Decimal("102.00"),
                        "Pattern B should have high_threshold at 102")
        self.assertEqual(rebound_b.rebound_price, Decimal("110.00"),
                        "Pattern B should have rebound at 110")
        self.assertEqual(rebound_b.rebound_date, self.base_date + timedelta(days=17),
                        "Pattern B should complete on day 17")

        # Assert: Should have 3 active patterns (Patterns C, D, E)
        self.assertEqual(len(result.active_lows), 3,
                        "Should have 3 active patterns (C, D, E from multiple spawns)")

        # Verify Pattern C (spawned from Pattern B at day 15, in State 3)
        pattern_c = result.active_lows[0]
        self.assertEqual(pattern_c.high_start_price, Decimal("110.00"),
                        "Pattern C should have high_start at $110 (updated from initial $102)")
        self.assertEqual(pattern_c.high_start_date, self.base_date + timedelta(days=17),
                        "Pattern C high_start should be from day 17")
        self.assertEqual(pattern_c.low_threshold_price, Decimal("88.00"),
                        "Pattern C should have low_threshold at $88")
        self.assertEqual(pattern_c.lowest_price, Decimal("82.00"),
                        "Pattern C should have lowest at $82")
        self.assertEqual(pattern_c.high_threshold_price, Decimal("98.40"),
                        "Pattern C should have high_threshold at $98.40")
        self.assertEqual(pattern_c.spawned, True,
                        "Pattern C should have spawned Pattern D")
        self.assertEqual(pattern_c.last_updated, self.base_date + timedelta(days=30),
                        "Pattern C's last_updated should be day 30")
        self.assertEqual(pattern_c.ticker_history_id, self.ticker_history_id)
        self.assertEqual(pattern_c.threshold, self.threshold)

        # Verify Pattern D (spawned from Pattern C at day 23, in State 3)
        pattern_d = result.active_lows[1]
        self.assertEqual(pattern_d.high_start_price, Decimal("108.00"),
                        "Pattern D should have high_start at $108 (updated from initial $98.40)")
        self.assertEqual(pattern_d.low_threshold_price, Decimal("86.40"),
                        "Pattern D should have low_threshold at $86.40")
        self.assertEqual(pattern_d.lowest_price, Decimal("85.00"),
                        "Pattern D should have lowest at $85")
        self.assertEqual(pattern_d.high_threshold_price, Decimal("102.00"),
                        "Pattern D should have high_threshold at $102")
        self.assertEqual(pattern_d.spawned, True,
                        "Pattern D should have spawned Pattern E")
        self.assertEqual(pattern_d.last_updated, self.base_date + timedelta(days=30),
                        "Pattern D's last_updated should be day 30")

        # Verify Pattern E (spawned from Pattern D at day 30, in State 1)
        pattern_e = result.active_lows[2]
        self.assertEqual(pattern_e.high_start_price, Decimal("102.00"),
                        "Pattern E should start at $102")
        self.assertEqual(pattern_e.high_start_date, self.base_date + timedelta(days=30),
                        "Pattern E should start on day 30")
        self.assertIsNone(pattern_e.low_threshold_price,
                        "Pattern E should be in State 1 (no low_threshold yet)")
        self.assertIsNone(pattern_e.lowest_price,
                        "Pattern E should be in State 1 (no lowest yet)")
        self.assertIsNone(pattern_e.high_threshold_price,
                        "Pattern E should be in State 1 (no high_threshold yet)")
        self.assertEqual(pattern_e.spawned, False,
                        "Pattern E has not spawned yet")
        self.assertEqual(pattern_e.last_updated, self.base_date + timedelta(days=30),
                        "Pattern E's last_updated should be day 30")
        self.assertEqual(pattern_e.ticker_history_id, self.ticker_history_id)
        self.assertEqual(pattern_e.threshold, self.threshold)


if __name__ == "__main__":
    unittest.main()
