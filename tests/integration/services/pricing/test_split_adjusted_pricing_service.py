"""Integration tests for SplitAdjustedPricingService.

Tests the service layer operations for split-adjusted pricing calculations.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

# IMPORTANT: Set environment variables BEFORE importing any src modules
from tests.integration.common_setup import setup_test_environment

setup_test_environment()

import pytest

from src.database.equities.enums import DataSourceEnum
from src.models.company import Company
from src.models.historical_eod_pricing import HistoricalEndOfDayPricing
from src.models.split import Split
from src.models.ticker import Ticker
from src.models.ticker_history import TickerHistory
from tests.integration.common_setup import integration_test_container
from tests.integration.services.pricing.mock_pricing_data_source import (
    MockPricingDataSource,
)
from tests.integration.services.pricing.pricing_scenarios import PricingTestScenario


@pytest.mark.integration
class TestSplitAdjustedPricingService:
    """Integration tests for SplitAdjustedPricingService split adjustment calculations."""

    def test_split_adjusted_pricing_comprehensive(self):
        """Test split-adjusted pricing with various split scenarios.

        Validates:
        - No splits: prices remain unchanged
        - Single split: correct adjustment for prices before split
        - Multiple splits: cumulative ratio calculation
        - Correct count of price records
        - Prices sorted by date (oldest first)
        """
        with integration_test_container() as (postgres, company_repo, port):
            from src.repos.equities.pricing.historical_eod_pricing_repository import (
                HistoricalEodPricingRepository,
            )
            from src.repos.equities.splits.splits_repository import SplitsRepository
            from src.repos.equities.tickers.ticker_history_repository import (
                TickerHistoryRepository,
            )
            from src.repos.equities.tickers.ticker_repository import TickerRepository
            from src.services.pricing.split_adjusted_pricing_service import (
                SplitAdjustedPricingService,
            )

            mock_data = MockPricingDataSource()
            ticker_repo = TickerRepository()
            ticker_history_repo = TickerHistoryRepository()
            pricing_repo = HistoricalEodPricingRepository()
            splits_repo = SplitsRepository()

            service = SplitAdjustedPricingService(
                pricing_repo, splits_repo, ticker_repo, ticker_history_repo
            )

            # Test 1: No splits scenario
            pricing_no_split, splits_no_split = mock_data.get_no_split_scenario()

            company1 = Company(
                company_name="NoSplit Corp",
                exchange="NASDAQ",
                active=True,
                source=DataSourceEnum.EODHD,
            )
            inserted_company1 = company_repo.insert(company1)

            th1 = TickerHistory(
                symbol="NOSPLIT",
                company_id=inserted_company1.id,
                valid_from=date(2020, 1, 1),
            )
            th1_inserted = ticker_history_repo.insert(th1)

            ticker1 = Ticker(
                symbol="NOSPLIT",
                company_id=inserted_company1.id,
                ticker_history_id=th1_inserted.id,
            )
            ticker_repo.insert(ticker1)

            # Insert pricing data
            pricing_models_1 = [
                HistoricalEndOfDayPricing(
                    ticker_history_id=th1_inserted.id,
                    date=p.date,
                    open=p.open,
                    high=p.high,
                    low=p.low,
                    close=p.close,
                    adjusted_close=p.adjusted_close,
                    volume=p.volume,
                )
                for p in pricing_no_split
            ]
            pricing_repo.bulk_upsert_pricing(th1_inserted.id, pricing_models_1)

            result1 = service.get_split_adjusted_pricing_with_symbol(
                symbol="NOSPLIT",
                from_date=date(2023, 1, 1),
                to_date=date(2023, 1, 2),
                include_ohlc=False,
            )

            # Assertions: No adjustments
            assert len(result1.prices) == len(pricing_no_split)
            for i, pricing_scenario in enumerate(pricing_no_split):
                assert result1.prices[i].date == pricing_scenario.date
                assert result1.prices[i].price == pricing_scenario.close

            # Test 2: Single split scenario
            (
                pricing_single_split,
                splits_single_split,
                expected_single,
            ) = mock_data.get_single_split_scenario()

            company2 = Company(
                company_name="SingleSplit Corp",
                exchange="NASDAQ",
                active=True,
                source=DataSourceEnum.EODHD,
            )
            inserted_company2 = company_repo.insert(company2)

            th2 = TickerHistory(
                symbol="SINGLE",
                company_id=inserted_company2.id,
                valid_from=date(2020, 1, 1),
            )
            th2_inserted = ticker_history_repo.insert(th2)

            ticker2 = Ticker(
                symbol="SINGLE",
                company_id=inserted_company2.id,
                ticker_history_id=th2_inserted.id,
            )
            ticker_repo.insert(ticker2)

            # Insert pricing and splits
            pricing_models_2 = [
                HistoricalEndOfDayPricing(
                    ticker_history_id=th2_inserted.id,
                    date=p.date,
                    open=p.open,
                    high=p.high,
                    low=p.low,
                    close=p.close,
                    adjusted_close=p.adjusted_close,
                    volume=p.volume,
                )
                for p in pricing_single_split
            ]
            pricing_repo.bulk_upsert_pricing(th2_inserted.id, pricing_models_2)

            split_models_2 = [
                Split(
                    ticker_history_id=th2_inserted.id,
                    date=s.date,
                    split_ratio=s.split_ratio,
                )
                for s in splits_single_split
            ]
            splits_repo.bulk_upsert_splits(th2_inserted.id, split_models_2)

            result2 = service.get_split_adjusted_pricing_with_symbol(
                symbol="SINGLE",
                from_date=date(2023, 1, 1),
                to_date=date(2023, 7, 1),
                include_ohlc=False,
            )

            # Assertions: Single split adjustments
            assert len(result2.prices) == len(pricing_single_split)
            for price_result in result2.prices:
                assert price_result.price == expected_single[price_result.date]

            # Test 3: Multiple splits scenario
            (
                pricing_multi_split,
                splits_multi_split,
                expected_multi,
            ) = mock_data.get_multiple_splits_scenario()

            company3 = Company(
                company_name="MultiSplit Corp",
                exchange="NASDAQ",
                active=True,
                source=DataSourceEnum.EODHD,
            )
            inserted_company3 = company_repo.insert(company3)

            th3 = TickerHistory(
                symbol="MULTI",
                company_id=inserted_company3.id,
                valid_from=date(2020, 1, 1),
            )
            th3_inserted = ticker_history_repo.insert(th3)

            ticker3 = Ticker(
                symbol="MULTI",
                company_id=inserted_company3.id,
                ticker_history_id=th3_inserted.id,
            )
            ticker_repo.insert(ticker3)

            # Insert pricing and splits
            pricing_models_3 = [
                HistoricalEndOfDayPricing(
                    ticker_history_id=th3_inserted.id,
                    date=p.date,
                    open=p.open,
                    high=p.high,
                    low=p.low,
                    close=p.close,
                    adjusted_close=p.adjusted_close,
                    volume=p.volume,
                )
                for p in pricing_multi_split
            ]
            pricing_repo.bulk_upsert_pricing(th3_inserted.id, pricing_models_3)

            split_models_3 = [
                Split(
                    ticker_history_id=th3_inserted.id,
                    date=s.date,
                    split_ratio=s.split_ratio,
                )
                for s in splits_multi_split
            ]
            splits_repo.bulk_upsert_splits(th3_inserted.id, split_models_3)

            result3 = service.get_split_adjusted_pricing_with_symbol(
                symbol="MULTI",
                from_date=date(2020, 1, 1),
                to_date=date(2022, 7, 1),
                include_ohlc=False,
            )

            # Assertions: Multiple splits with cumulative ratios
            assert len(result3.prices) == len(pricing_multi_split)
            for price_result in result3.prices:
                assert price_result.price == expected_multi[price_result.date]

    def test_split_adjusted_pricing_ohlc_mode(self):
        """Test OHLCV data adjustment with splits across multiple pricing records.

        Validates:
        - All OHLC prices adjusted correctly for records before split
        - Volume multiplied by split ratio for records before split
        - Adjusted close calculated correctly
        - Records after split remain unchanged
        - Correct count of pricing records
        - Prices sorted by date
        """
        with integration_test_container() as (postgres, company_repo, port):
            from src.repos.equities.pricing.historical_eod_pricing_repository import (
                HistoricalEodPricingRepository,
            )
            from src.repos.equities.splits.splits_repository import SplitsRepository
            from src.repos.equities.tickers.ticker_history_repository import (
                TickerHistoryRepository,
            )
            from src.repos.equities.tickers.ticker_repository import TickerRepository
            from src.services.pricing.split_adjusted_pricing_service import (
                SplitAdjustedPricingService,
            )

            mock_data = MockPricingDataSource()
            ticker_repo = TickerRepository()
            ticker_history_repo = TickerHistoryRepository()
            pricing_repo = HistoricalEodPricingRepository()
            splits_repo = SplitsRepository()

            service = SplitAdjustedPricingService(
                pricing_repo, splits_repo, ticker_repo, ticker_history_repo
            )

            # Get OHLC test scenario with multiple pricing records
            pricing_scenarios, split_scenarios, expected_values = mock_data.get_ohlc_test_scenario()

            company = Company(
                company_name="OHLC Test Corp",
                exchange="NASDAQ",
                active=True,
                source=DataSourceEnum.EODHD,
            )
            inserted_company = company_repo.insert(company)

            th = TickerHistory(
                symbol="OHLC",
                company_id=inserted_company.id,
                valid_from=date(2020, 1, 1),
            )
            th_inserted = ticker_history_repo.insert(th)

            ticker = Ticker(
                symbol="OHLC",
                company_id=inserted_company.id,
                ticker_history_id=th_inserted.id,
            )
            ticker_repo.insert(ticker)

            # Insert all pricing records
            pricing_models = [
                HistoricalEndOfDayPricing(
                    ticker_history_id=th_inserted.id,
                    date=p.date,
                    open=p.open,
                    high=p.high,
                    low=p.low,
                    close=p.close,
                    adjusted_close=p.adjusted_close,
                    volume=p.volume,
                )
                for p in pricing_scenarios
            ]
            pricing_repo.bulk_upsert_pricing(th_inserted.id, pricing_models)

            # Insert splits
            split_models = [
                Split(
                    ticker_history_id=th_inserted.id,
                    date=s.date,
                    split_ratio=s.split_ratio,
                )
                for s in split_scenarios
            ]
            splits_repo.bulk_upsert_splits(th_inserted.id, split_models)

            # Test with OHLC mode
            result = service.get_split_adjusted_pricing_with_symbol(
                symbol="OHLC",
                from_date=pricing_scenarios[0].date,
                to_date=pricing_scenarios[-1].date,
                include_ohlc=True,
            )

            # Assertions using expected values from mock
            assert len(result.prices) == len(pricing_scenarios)

            # Verify each price record matches expected adjusted values
            for price in result.prices:
                expected = expected_values[price.date]
                assert price.open == expected["open"]
                assert price.high == expected["high"]
                assert price.low == expected["low"]
                assert price.close == expected["close"]
                assert price.adjusted_close == expected["adjusted_close"]
                assert price.volume == expected["volume"]

            # Verify sorted by date
            for i in range(len(result.prices) - 1):
                assert result.prices[i].date < result.prices[i + 1].date

    def test_company_id_pricing_multiple_ticker_histories(self):
        """Test getting pricing for all ticker histories of a company (symbol change).

        Validates:
        - Pricing from multiple ticker histories combined
        - Sorted by date across all ticker histories
        - Correct total count of pricing records
        """
        with integration_test_container() as (postgres, company_repo, port):
            from src.repos.equities.pricing.historical_eod_pricing_repository import (
                HistoricalEodPricingRepository,
            )
            from src.repos.equities.splits.splits_repository import SplitsRepository
            from src.repos.equities.tickers.ticker_history_repository import (
                TickerHistoryRepository,
            )
            from src.repos.equities.tickers.ticker_repository import TickerRepository
            from src.services.pricing.split_adjusted_pricing_service import (
                SplitAdjustedPricingService,
            )

            ticker_repo = TickerRepository()
            ticker_history_repo = TickerHistoryRepository()
            pricing_repo = HistoricalEodPricingRepository()
            splits_repo = SplitsRepository()

            service = SplitAdjustedPricingService(
                pricing_repo, splits_repo, ticker_repo, ticker_history_repo
            )

            # Create company with two ticker histories
            company = Company(
                company_name="Symbol Change Corp",
                exchange="NASDAQ",
                active=True,
                source=DataSourceEnum.EODHD,
            )
            inserted_company = company_repo.insert(company)

            # Old ticker history
            th_old = TickerHistory(
                symbol="OLD",
                company_id=inserted_company.id,
                valid_from=date(2020, 1, 1),
                valid_to=date(2021, 12, 31),
            )
            th_old_inserted = ticker_history_repo.insert(th_old)

            # New ticker history
            th_new = TickerHistory(
                symbol="NEW",
                company_id=inserted_company.id,
                valid_from=date(2022, 1, 1),
            )
            th_new_inserted = ticker_history_repo.insert(th_new)

            # Create pricing for both ticker histories
            pricing_old_data = [
                PricingTestScenario(
                    date=date(2021, 1, 1),
                    open=Decimal("50.00"),
                    high=Decimal("52.00"),
                    low=Decimal("49.00"),
                    close=Decimal("51.00"),
                    adjusted_close=Decimal("51.00"),
                    volume=500000,
                ),
            ]
            pricing_new_data = [
                PricingTestScenario(
                    date=date(2022, 1, 1),
                    open=Decimal("55.00"),
                    high=Decimal("57.00"),
                    low=Decimal("54.00"),
                    close=Decimal("56.00"),
                    adjusted_close=Decimal("56.00"),
                    volume=600000,
                ),
            ]

            pricing_old = [
                HistoricalEndOfDayPricing(
                    ticker_history_id=th_old_inserted.id,
                    date=p.date,
                    open=p.open,
                    high=p.high,
                    low=p.low,
                    close=p.close,
                    adjusted_close=p.adjusted_close,
                    volume=p.volume,
                )
                for p in pricing_old_data
            ]
            pricing_new = [
                HistoricalEndOfDayPricing(
                    ticker_history_id=th_new_inserted.id,
                    date=p.date,
                    open=p.open,
                    high=p.high,
                    low=p.low,
                    close=p.close,
                    adjusted_close=p.adjusted_close,
                    volume=p.volume,
                )
                for p in pricing_new_data
            ]

            pricing_repo.bulk_upsert_pricing(th_old_inserted.id, pricing_old)
            pricing_repo.bulk_upsert_pricing(th_new_inserted.id, pricing_new)

            # Test service method with company_id
            result = service.get_split_adjusted_pricing_with_company_id(
                company_id=inserted_company.id, include_ohlc=False
            )

            # Assertions using expected data
            expected_count = len(pricing_old_data) + len(pricing_new_data)
            assert len(result.prices) == expected_count

            # Verify sorted by date and prices match
            assert result.prices[0].date == pricing_old_data[0].date
            assert result.prices[0].price == pricing_old_data[0].close
            assert result.prices[1].date == pricing_new_data[0].date
            assert result.prices[1].price == pricing_new_data[0].close

    def test_edge_cases_comprehensive(self):
        """Test edge cases for split-adjusted pricing.

        Validates:
        - Empty result when no pricing data exists
        - ValueError when symbol doesn't exist
        - Splits before date range don't affect prices
        """
        with integration_test_container() as (postgres, company_repo, port):
            from src.repos.equities.pricing.historical_eod_pricing_repository import (
                HistoricalEodPricingRepository,
            )
            from src.repos.equities.splits.splits_repository import SplitsRepository
            from src.repos.equities.tickers.ticker_history_repository import (
                TickerHistoryRepository,
            )
            from src.repos.equities.tickers.ticker_repository import TickerRepository
            from src.services.pricing.split_adjusted_pricing_service import (
                SplitAdjustedPricingService,
            )

            ticker_repo = TickerRepository()
            ticker_history_repo = TickerHistoryRepository()
            pricing_repo = HistoricalEodPricingRepository()
            splits_repo = SplitsRepository()

            service = SplitAdjustedPricingService(
                pricing_repo, splits_repo, ticker_repo, ticker_history_repo
            )

            # Test 1: Empty result when no pricing data
            company1 = Company(
                company_name="Empty Corp",
                exchange="NASDAQ",
                active=True,
                source=DataSourceEnum.EODHD,
            )
            inserted_company1 = company_repo.insert(company1)

            th1 = TickerHistory(
                symbol="EMPTY",
                company_id=inserted_company1.id,
                valid_from=date(2020, 1, 1),
            )
            th1_inserted = ticker_history_repo.insert(th1)

            ticker1 = Ticker(
                symbol="EMPTY",
                company_id=inserted_company1.id,
                ticker_history_id=th1_inserted.id,
            )
            ticker_repo.insert(ticker1)

            result_empty = service.get_split_adjusted_pricing_with_symbol(
                symbol="EMPTY",
                from_date=date(2023, 1, 1),
                to_date=date(2023, 12, 31),
                include_ohlc=False,
            )
            assert len(result_empty.prices) == 0

            # Test 2: ValueError when symbol doesn't exist
            with pytest.raises(ValueError, match="Symbol 'NONEXIST' not found"):
                service.get_split_adjusted_pricing_with_symbol(
                    symbol="NONEXIST",
                    from_date=date(2023, 1, 1),
                    to_date=date(2023, 12, 31),
                    include_ohlc=False,
                )

            # Test 3: Splits before date range don't affect prices
            company2 = Company(
                company_name="Past Split Corp",
                exchange="NASDAQ",
                active=True,
                source=DataSourceEnum.EODHD,
            )
            inserted_company2 = company_repo.insert(company2)

            th2 = TickerHistory(
                symbol="PAST",
                company_id=inserted_company2.id,
                valid_from=date(2020, 1, 1),
            )
            th2_inserted = ticker_history_repo.insert(th2)

            ticker2 = Ticker(
                symbol="PAST",
                company_id=inserted_company2.id,
                ticker_history_id=th2_inserted.id,
            )
            ticker_repo.insert(ticker2)

            # Create split in past
            split_past = Split(
                ticker_history_id=th2_inserted.id,
                date=date(2020, 6, 1),
                split_ratio="2.000000/1.000000",
            )
            splits_repo.bulk_upsert_splits(th2_inserted.id, [split_past])

            # Create pricing AFTER split
            pricing_after_split = HistoricalEndOfDayPricing(
                ticker_history_id=th2_inserted.id,
                date=date(2023, 1, 1),
                open=Decimal("50.00"),
                high=Decimal("52.00"),
                low=Decimal("49.00"),
                close=Decimal("50.00"),
                adjusted_close=Decimal("50.00"),
                volume=1000000,
            )
            pricing_repo.bulk_upsert_pricing(th2_inserted.id, [pricing_after_split])

            result_past_split = service.get_split_adjusted_pricing_with_symbol(
                symbol="PAST",
                from_date=date(2023, 1, 1),
                to_date=date(2023, 1, 1),
                include_ohlc=False,
            )

            # Price should be unchanged (split already reflected)
            assert len(result_past_split.prices) == 1
            assert result_past_split.prices[0].price == Decimal("50.00")
