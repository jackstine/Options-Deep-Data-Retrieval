"""Unit tests for get_derived_data() methods in high_lows models."""

import unittest
from datetime import date, timedelta
from decimal import Decimal

from src.algorithms.high_lows.constants import EXPIRED_DAYS_OUT
from src.algorithms.high_lows.models.low import Low
from src.algorithms.high_lows.models.rebound import Rebound


class TestLowDerivedData(unittest.TestCase):
    """Test get_derived_data() for Low model."""

    def test_low_with_all_fields_set(self) -> None:
        """Test derived data for a Low pattern with all fields populated."""
        # Create a Low pattern with all fields
        base_date = date(2024, 1, 1)
        low = Low(
            ticker_history_id=1,
            threshold=Decimal("0.20"),
            high_start_price=Decimal("100.00"),
            high_start_date=base_date,
            low_threshold_price=Decimal("80.00"),
            low_threshold_date=base_date + timedelta(days=10),
            lowest_price=Decimal("75.00"),
            lowest_date=base_date + timedelta(days=15),
            high_threshold_price=Decimal("90.00"),
            high_threshold_date=base_date + timedelta(days=25),
            number_of_high_thresholds=2,
            last_updated=base_date + timedelta(days=25),
        )

        derived = low.get_derived_data()

        # Check base fields
        self.assertEqual(derived["ticker_history_id"], 1)
        self.assertEqual(derived["threshold"], Decimal("0.20"))
        self.assertEqual(derived["high_start_price"], Decimal("100.00"))
        self.assertEqual(derived["high_start_date"], base_date)

        # Check price/date fields
        self.assertEqual(derived["low_threshold_price"], Decimal("80.00"))
        self.assertEqual(derived["lowest_price"], Decimal("75.00"))
        self.assertEqual(derived["high_threshold_price"], Decimal("90.00"))
        self.assertIsNone(derived["rebound_price"])
        self.assertIsNone(derived["rebound_date"])

        # Check counter
        self.assertEqual(derived["number_of_high_thresholds"], 2)

        # Check status flags
        self.assertTrue(derived["is_low"])
        self.assertFalse(derived["is_rebound"])
        self.assertTrue(derived["still_low"])
        self.assertFalse(derived["expired"])

        # Check days between calculations
        self.assertEqual(derived["days_hs_lt"], 10)
        self.assertEqual(derived["days_hs_l"], 15)
        self.assertEqual(derived["days_hs_ht"], 25)
        self.assertIsNone(derived["days_hs_r"])
        self.assertEqual(derived["days_lt_l"], 5)
        self.assertEqual(derived["days_lt_ht"], 15)
        self.assertIsNone(derived["days_lt_r"])
        self.assertEqual(derived["days_l_ht"], 10)
        self.assertIsNone(derived["days_l_r"])
        self.assertIsNone(derived["days_ht_r"])

        # Check temporal metadata
        self.assertEqual(derived["lt_year"], 2024)
        self.assertEqual(derived["lt_year_month"], "2024-01")
        self.assertEqual(derived["lt_month"], 1)
        self.assertIsNone(derived["r_year"])
        self.assertIsNone(derived["r_year_month"])
        self.assertIsNone(derived["r_month"])

        # Check constants
        self.assertEqual(derived["days_till_expiration"], EXPIRED_DAYS_OUT)

    def test_low_with_minimal_fields(self) -> None:
        """Test derived data for a Low pattern with only required fields."""
        base_date = date(2024, 1, 1)
        low = Low(
            ticker_history_id=1,
            threshold=Decimal("0.20"),
            high_start_price=Decimal("100.00"),
            high_start_date=base_date,
            last_updated=base_date,
        )

        derived = low.get_derived_data()

        # Check that None fields are properly None
        self.assertIsNone(derived["low_threshold_price"])
        self.assertIsNone(derived["low_threshold_date"])
        self.assertIsNone(derived["lowest_price"])
        self.assertIsNone(derived["lowest_date"])
        self.assertIsNone(derived["high_threshold_price"])
        self.assertIsNone(derived["high_threshold_date"])

        # Check that days between are all None
        self.assertIsNone(derived["days_hs_lt"])
        self.assertIsNone(derived["days_hs_l"])
        self.assertIsNone(derived["days_hs_ht"])
        self.assertIsNone(derived["days_lt_l"])
        self.assertIsNone(derived["days_lt_ht"])
        self.assertIsNone(derived["days_l_ht"])

        # Check status flags
        self.assertTrue(derived["is_low"])
        self.assertFalse(derived["is_rebound"])
        self.assertTrue(derived["still_low"])


class TestReboundDerivedData(unittest.TestCase):
    """Test get_derived_data() for Rebound model."""

    def test_rebound_with_all_fields(self) -> None:
        """Test derived data for a completed Rebound pattern."""
        base_date = date(2024, 1, 1)
        rebound = Rebound(
            ticker_history_id=1,
            threshold=Decimal("0.20"),
            high_start_price=Decimal("100.00"),
            high_start_date=base_date,
            low_threshold_price=Decimal("80.00"),
            low_threshold_date=base_date + timedelta(days=10),
            lowest_price=Decimal("75.00"),
            lowest_date=base_date + timedelta(days=15),
            high_threshold_price=Decimal("90.00"),
            high_threshold_date=base_date + timedelta(days=25),
            rebound_price=Decimal("102.00"),
            rebound_date=base_date + timedelta(days=40),
            number_of_high_thresholds=3,
        )

        derived = rebound.get_derived_data()

        # Check base fields
        self.assertEqual(derived["ticker_history_id"], 1)
        self.assertEqual(derived["threshold"], Decimal("0.20"))
        self.assertEqual(derived["high_start_price"], Decimal("100.00"))

        # Check rebound fields are set
        self.assertEqual(derived["rebound_price"], Decimal("102.00"))
        self.assertEqual(derived["rebound_date"], base_date + timedelta(days=40))

        # Check counter
        self.assertEqual(derived["number_of_high_thresholds"], 3)

        # Check status flags
        self.assertFalse(derived["is_low"])
        self.assertTrue(derived["is_rebound"])
        self.assertFalse(derived["still_low"])
        self.assertFalse(derived["expired"])

        # Check days between calculations including rebound
        self.assertEqual(derived["days_hs_r"], 40)
        self.assertEqual(derived["days_lt_r"], 30)
        self.assertEqual(derived["days_l_r"], 25)
        self.assertEqual(derived["days_ht_r"], 15)

        # Check temporal metadata for rebound
        self.assertEqual(derived["r_year"], 2024)
        self.assertEqual(derived["r_year_month"], "2024-02")
        self.assertEqual(derived["r_month"], 2)

        # days_lt_now should be None for completed patterns
        self.assertIsNone(derived["days_lt_now"])

    def test_rebound_expiration(self) -> None:
        """Test that rebound patterns can be marked as expired."""
        base_date = date(2024, 1, 1)
        # Create a rebound that took longer than expiration threshold
        rebound = Rebound(
            ticker_history_id=1,
            threshold=Decimal("0.20"),
            high_start_price=Decimal("100.00"),
            high_start_date=base_date,
            low_threshold_price=Decimal("80.00"),
            low_threshold_date=base_date + timedelta(days=10),
            lowest_price=Decimal("75.00"),
            lowest_date=base_date + timedelta(days=15),
            high_threshold_price=Decimal("90.00"),
            high_threshold_date=base_date + timedelta(days=25),
            rebound_price=Decimal("102.00"),
            rebound_date=base_date + timedelta(days=EXPIRED_DAYS_OUT + 20),
            number_of_high_thresholds=1,
        )

        derived = rebound.get_derived_data()

        # Should be marked as expired
        self.assertTrue(derived["expired"])
        self.assertTrue(derived["is_rebound"])
        self.assertFalse(derived["still_low"])


if __name__ == "__main__":
    unittest.main()
