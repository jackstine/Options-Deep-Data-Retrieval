"""Unit tests for get_derived_data() methods in low_highs models."""

import unittest
from datetime import date, timedelta
from decimal import Decimal

from src.algorithms.low_highs.constants import EXPIRED_DAYS_OUT
from src.algorithms.low_highs.models.high import High
from src.algorithms.low_highs.models.reversal import Reversal


class TestHighDerivedData(unittest.TestCase):
    """Test get_derived_data() for High model."""

    def test_high_with_all_fields_set(self) -> None:
        """Test derived data for a High pattern with all fields populated."""
        # Create a High pattern with all fields
        base_date = date(2024, 1, 1)
        high = High(
            ticker_history_id=1,
            threshold=Decimal("0.20"),
            low_start_price=Decimal("50.00"),
            low_start_date=base_date,
            high_threshold_price=Decimal("60.00"),
            high_threshold_date=base_date + timedelta(days=10),
            highest_price=Decimal("65.00"),
            highest_date=base_date + timedelta(days=15),
            low_threshold_price=Decimal("54.17"),
            low_threshold_date=base_date + timedelta(days=25),
            number_of_low_thresholds=2,
            last_updated=base_date + timedelta(days=25),
        )

        derived = high.get_derived_data()

        # Check base fields
        self.assertEqual(derived["ticker_history_id"], 1)
        self.assertEqual(derived["threshold"], Decimal("0.20"))
        self.assertEqual(derived["low_start_price"], Decimal("50.00"))
        self.assertEqual(derived["low_start_date"], base_date)

        # Check price/date fields
        self.assertEqual(derived["high_threshold_price"], Decimal("60.00"))
        self.assertEqual(derived["highest_price"], Decimal("65.00"))
        self.assertEqual(derived["low_threshold_price"], Decimal("54.17"))
        self.assertIsNone(derived["reversal_price"])
        self.assertIsNone(derived["reversal_date"])

        # Check counter
        self.assertEqual(derived["number_of_low_thresholds"], 2)

        # Check status flags
        self.assertTrue(derived["is_high"])
        self.assertFalse(derived["is_reversal"])
        self.assertTrue(derived["still_high"])
        self.assertFalse(derived["expired"])

        # Check days between calculations
        self.assertEqual(derived["days_ls_ht"], 10)
        self.assertEqual(derived["days_ls_h"], 15)
        self.assertEqual(derived["days_ls_lt"], 25)
        self.assertIsNone(derived["days_ls_r"])
        self.assertEqual(derived["days_ht_h"], 5)
        self.assertEqual(derived["days_ht_lt"], 15)
        self.assertIsNone(derived["days_ht_r"])
        self.assertEqual(derived["days_h_lt"], 10)
        self.assertIsNone(derived["days_h_r"])
        self.assertIsNone(derived["days_lt_r"])

        # Check temporal metadata
        self.assertEqual(derived["ht_year"], 2024)
        self.assertEqual(derived["ht_year_month"], "2024-01")
        self.assertEqual(derived["ht_month"], 1)
        self.assertIsNone(derived["r_year"])
        self.assertIsNone(derived["r_year_month"])
        self.assertIsNone(derived["r_month"])

        # Check constants
        self.assertEqual(derived["days_till_expiration"], EXPIRED_DAYS_OUT)

    def test_high_with_minimal_fields(self) -> None:
        """Test derived data for a High pattern with only required fields."""
        base_date = date(2024, 1, 1)
        high = High(
            ticker_history_id=1,
            threshold=Decimal("0.20"),
            low_start_price=Decimal("50.00"),
            low_start_date=base_date,
            last_updated=base_date,
        )

        derived = high.get_derived_data()

        # Check that None fields are properly None
        self.assertIsNone(derived["high_threshold_price"])
        self.assertIsNone(derived["high_threshold_date"])
        self.assertIsNone(derived["highest_price"])
        self.assertIsNone(derived["highest_date"])
        self.assertIsNone(derived["low_threshold_price"])
        self.assertIsNone(derived["low_threshold_date"])

        # Check that days between are all None
        self.assertIsNone(derived["days_ls_ht"])
        self.assertIsNone(derived["days_ls_h"])
        self.assertIsNone(derived["days_ls_lt"])
        self.assertIsNone(derived["days_ht_h"])
        self.assertIsNone(derived["days_ht_lt"])
        self.assertIsNone(derived["days_h_lt"])

        # Check status flags
        self.assertTrue(derived["is_high"])
        self.assertFalse(derived["is_reversal"])
        self.assertTrue(derived["still_high"])


class TestReversalDerivedData(unittest.TestCase):
    """Test get_derived_data() for Reversal model."""

    def test_reversal_with_all_fields(self) -> None:
        """Test derived data for a completed Reversal pattern."""
        base_date = date(2024, 1, 1)
        reversal = Reversal(
            ticker_history_id=1,
            threshold=Decimal("0.20"),
            low_start_price=Decimal("50.00"),
            low_start_date=base_date,
            high_threshold_price=Decimal("60.00"),
            high_threshold_date=base_date + timedelta(days=10),
            highest_price=Decimal("65.00"),
            highest_date=base_date + timedelta(days=15),
            low_threshold_price=Decimal("54.17"),
            low_threshold_date=base_date + timedelta(days=25),
            reversal_price=Decimal("49.00"),
            reversal_date=base_date + timedelta(days=40),
            number_of_low_thresholds=3,
        )

        derived = reversal.get_derived_data()

        # Check base fields
        self.assertEqual(derived["ticker_history_id"], 1)
        self.assertEqual(derived["threshold"], Decimal("0.20"))
        self.assertEqual(derived["low_start_price"], Decimal("50.00"))

        # Check reversal fields are set
        self.assertEqual(derived["reversal_price"], Decimal("49.00"))
        self.assertEqual(derived["reversal_date"], base_date + timedelta(days=40))

        # Check counter
        self.assertEqual(derived["number_of_low_thresholds"], 3)

        # Check status flags
        self.assertFalse(derived["is_high"])
        self.assertTrue(derived["is_reversal"])
        self.assertFalse(derived["still_high"])
        self.assertFalse(derived["expired"])

        # Check days between calculations including reversal
        self.assertEqual(derived["days_ls_r"], 40)
        self.assertEqual(derived["days_ht_r"], 30)
        self.assertEqual(derived["days_h_r"], 25)
        self.assertEqual(derived["days_lt_r"], 15)

        # Check temporal metadata for reversal
        self.assertEqual(derived["r_year"], 2024)
        self.assertEqual(derived["r_year_month"], "2024-02")
        self.assertEqual(derived["r_month"], 2)

        # days_ht_now should be None for completed patterns
        self.assertIsNone(derived["days_ht_now"])

    def test_reversal_expiration(self) -> None:
        """Test that reversal patterns can be marked as expired."""
        base_date = date(2024, 1, 1)
        # Create a reversal that took longer than expiration threshold
        reversal = Reversal(
            ticker_history_id=1,
            threshold=Decimal("0.20"),
            low_start_price=Decimal("50.00"),
            low_start_date=base_date,
            high_threshold_price=Decimal("60.00"),
            high_threshold_date=base_date + timedelta(days=10),
            highest_price=Decimal("65.00"),
            highest_date=base_date + timedelta(days=15),
            low_threshold_price=Decimal("54.17"),
            low_threshold_date=base_date + timedelta(days=25),
            reversal_price=Decimal("49.00"),
            reversal_date=base_date + timedelta(days=EXPIRED_DAYS_OUT + 20),
            number_of_low_thresholds=1,
        )

        derived = reversal.get_derived_data()

        # Should be marked as expired
        self.assertTrue(derived["expired"])
        self.assertTrue(derived["is_reversal"])
        self.assertFalse(derived["still_high"])


if __name__ == "__main__":
    unittest.main()
