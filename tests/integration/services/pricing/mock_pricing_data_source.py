"""Mock data source for pricing integration tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from tests.integration.services.pricing.pricing_scenarios import (
    PricingTestScenario,
    SplitTestScenario,
)


class MockPricingDataSource:
    """Mock data source providing test pricing scenarios."""

    def get_no_split_scenario(self) -> tuple[list[PricingTestScenario], list[SplitTestScenario]]:
        """Return pricing data with no splits."""
        pricing = [
            PricingTestScenario(
                date=date(2023, 1, 1),
                open=Decimal("100.00"),
                high=Decimal("105.00"),
                low=Decimal("99.00"),
                close=Decimal("102.00"),
                adjusted_close=Decimal("102.00"),
                volume=1000000,
            ),
            PricingTestScenario(
                date=date(2023, 1, 2),
                open=Decimal("102.00"),
                high=Decimal("107.00"),
                low=Decimal("101.00"),
                close=Decimal("105.00"),
                adjusted_close=Decimal("105.00"),
                volume=1100000,
            ),
        ]
        return pricing, []

    def get_single_split_scenario(
        self,
    ) -> tuple[list[PricingTestScenario], list[SplitTestScenario], dict[date, Decimal]]:
        """Return pricing data with single 2-for-1 split.

        Returns:
            Tuple of (pricing data, split data, expected adjusted prices dict)
        """
        pricing = [
            # Before split: $100
            PricingTestScenario(
                date=date(2023, 1, 1),
                open=Decimal("98.00"),
                high=Decimal("105.00"),
                low=Decimal("97.00"),
                close=Decimal("100.00"),
                adjusted_close=Decimal("100.00"),
                volume=1000000,
            ),
            # After split: $60
            PricingTestScenario(
                date=date(2023, 7, 1),
                open=Decimal("58.00"),
                high=Decimal("62.00"),
                low=Decimal("57.00"),
                close=Decimal("60.00"),
                adjusted_close=Decimal("60.00"),
                volume=2000000,
            ),
        ]
        splits = [
            SplitTestScenario(date=date(2023, 6, 1), split_ratio="2.000000/1.000000")
        ]
        expected_adjusted = {
            date(2023, 1, 1): Decimal("50.00"),  # $100 / 2 = $50
            date(2023, 7, 1): Decimal("60.00"),  # After split, unchanged
        }
        return pricing, splits, expected_adjusted

    def get_multiple_splits_scenario(
        self,
    ) -> tuple[list[PricingTestScenario], list[SplitTestScenario], dict[date, Decimal]]:
        """Return pricing data with multiple splits.

        Returns:
            Tuple of (pricing data, split data, expected adjusted prices dict)
        """
        pricing = [
            # 2020: Before all splits
            PricingTestScenario(
                date=date(2020, 1, 1),
                open=Decimal("600.00"),
                high=Decimal("610.00"),
                low=Decimal("595.00"),
                close=Decimal("600.00"),
                adjusted_close=Decimal("600.00"),
                volume=1000000,
            ),
            # 2021: After first split (2:1), before second split
            PricingTestScenario(
                date=date(2021, 7, 1),
                open=Decimal("150.00"),
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("150.00"),
                adjusted_close=Decimal("150.00"),
                volume=2000000,
            ),
            # 2022: After both splits
            PricingTestScenario(
                date=date(2022, 7, 1),
                open=Decimal("75.00"),
                high=Decimal("78.00"),
                low=Decimal("74.00"),
                close=Decimal("75.00"),
                adjusted_close=Decimal("75.00"),
                volume=6000000,
            ),
        ]
        splits = [
            SplitTestScenario(date=date(2021, 6, 1), split_ratio="2.000000/1.000000"),
            SplitTestScenario(date=date(2022, 6, 1), split_ratio="2.000000/1.000000"),
        ]
        expected_adjusted = {
            date(2020, 1, 1): Decimal("150.00"),  # $600 / 4 = $150 (cumulative 2×2)
            date(2021, 7, 1): Decimal("75.00"),  # $150 / 2 = $75 (only second split)
            date(2022, 7, 1): Decimal("75.00"),  # No future splits
        }
        return pricing, splits, expected_adjusted

    def get_ohlc_test_scenario(
        self,
    ) -> tuple[list[PricingTestScenario], list[SplitTestScenario], dict[date, dict[str, Decimal | int]]]:
        """Return multiple pricing records with split for OHLC testing.

        Returns:
            Tuple of (pricing data list, split data list, expected adjusted values dict)
            Expected values keyed by date, each containing OHLCV fields
        """
        pricing = [
            # Before split: Q1 2023
            PricingTestScenario(
                date=date(2023, 1, 15),
                open=Decimal("100.00"),
                high=Decimal("110.00"),
                low=Decimal("98.00"),
                close=Decimal("105.00"),
                adjusted_close=Decimal("105.00"),
                volume=1000000,
            ),
            PricingTestScenario(
                date=date(2023, 3, 15),
                open=Decimal("120.00"),
                high=Decimal("125.00"),
                low=Decimal("118.00"),
                close=Decimal("122.00"),
                adjusted_close=Decimal("122.00"),
                volume=1200000,
            ),
            PricingTestScenario(
                date=date(2023, 5, 15),
                open=Decimal("130.00"),
                high=Decimal("135.00"),
                low=Decimal("128.00"),
                close=Decimal("132.00"),
                adjusted_close=Decimal("132.00"),
                volume=1100000,
            ),
            # After split: Q3 2023
            PricingTestScenario(
                date=date(2023, 7, 15),
                open=Decimal("60.00"),
                high=Decimal("65.00"),
                low=Decimal("58.00"),
                close=Decimal("62.00"),
                adjusted_close=Decimal("62.00"),
                volume=2400000,
            ),
            PricingTestScenario(
                date=date(2023, 9, 15),
                open=Decimal("70.00"),
                high=Decimal("75.00"),
                low=Decimal("68.00"),
                close=Decimal("72.00"),
                adjusted_close=Decimal("72.00"),
                volume=2600000,
            ),
        ]
        splits = [
            SplitTestScenario(date=date(2023, 6, 1), split_ratio="2.000000/1.000000")
        ]
        expected_adjusted = {
            # Before split: All prices divided by 2, volumes multiplied by 2
            date(2023, 1, 15): {
                "open": Decimal("50.00"),      # 100 / 2
                "high": Decimal("55.00"),      # 110 / 2
                "low": Decimal("49.00"),       # 98 / 2
                "close": Decimal("52.50"),     # 105 / 2
                "adjusted_close": Decimal("52.50"),
                "volume": 2000000,             # 1M * 2
            },
            date(2023, 3, 15): {
                "open": Decimal("60.00"),      # 120 / 2
                "high": Decimal("62.50"),      # 125 / 2
                "low": Decimal("59.00"),       # 118 / 2
                "close": Decimal("61.00"),     # 122 / 2
                "adjusted_close": Decimal("61.00"),
                "volume": 2400000,             # 1.2M * 2
            },
            date(2023, 5, 15): {
                "open": Decimal("65.00"),      # 130 / 2
                "high": Decimal("67.50"),      # 135 / 2
                "low": Decimal("64.00"),       # 128 / 2
                "close": Decimal("66.00"),     # 132 / 2
                "adjusted_close": Decimal("66.00"),
                "volume": 2200000,             # 1.1M * 2
            },
            # After split: Unchanged
            date(2023, 7, 15): {
                "open": Decimal("60.00"),
                "high": Decimal("65.00"),
                "low": Decimal("58.00"),
                "close": Decimal("62.00"),
                "adjusted_close": Decimal("62.00"),
                "volume": 2400000,
            },
            date(2023, 9, 15): {
                "open": Decimal("70.00"),
                "high": Decimal("75.00"),
                "low": Decimal("68.00"),
                "close": Decimal("72.00"),
                "adjusted_close": Decimal("72.00"),
                "volume": 2600000,
            },
        }
        return pricing, splits, expected_adjusted
