"""Integration tests for Low/High backfill pipeline.

Tests the backfill pipeline using pre-populated test data from options-deep-test-data:latest image.
The image contains:
- TESTSPLIT: Active company with 30 days pricing + split on day 15
- TESTDELIST: Delisted company with 25 days pricing
- TESTACTIVE: Active company with 30 days pricing, no splits
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

# IMPORTANT: Set environment variables BEFORE importing any src modules
from tests.integration.common_setup import setup_test_environment

setup_test_environment()

import pytest

from src.algorithms.low_highs.pattern_config import LowHighPatternConfig
from tests.integration.algorithms.low_highs.backfill_test_helpers import (
    FixtureDataExpectations,
    validate_backfill_result,
    validate_pattern_dates_before_delisting,
    validate_patterns_in_database,
)
from tests.integration.common_setup import integration_test_container


@pytest.mark.integration
class TestLowHighBackfillPipeline:
    """Integration tests for low/high backfill pipeline with split adjustment and multiple configs."""

    def test_backfill_with_split_and_multiple_configs(self):
        """Test backfill pipeline with pre-populated fixture data.

        Validates:
        - Backfill processes all three test companies (TESTSPLIT, TESTDELIST, TESTACTIVE)
        - Multiple threshold configurations generate different pattern counts
        - Split-adjusted pricing works correctly for TESTSPLIT
        - Delisted company (TESTDELIST) is processed correctly
        - Patterns are stored in database
        """
        with integration_test_container("options-deep-test-data:latest") as (
            postgres,
            _,
            port,
        ):
            # Import repositories after container starts
            from src.pipelines.algorithms.low_highs import get_backfill_pipeline
            from src.repos.algorithms.low_highs.highs_repository import (
                HighsRepository,
            )
            from src.repos.algorithms.low_highs.reversals_repository import (
                ReversalsRepository,
            )
            from src.repos.equities.tickers.ticker_history_repository import (
                TickerHistoryRepository,
            )

            # Initialize repositories
            ticker_history_repo = TickerHistoryRepository()
            highs_repo = HighsRepository()
            reversals_repo = ReversalsRepository()

            # Get ticker history IDs for test companies
            testsplit_th_list = ticker_history_repo.get_ticker_history_by_symbol("TESTSPLIT")
            testdelist_th_list = ticker_history_repo.get_ticker_history_by_symbol("TESTDELIST")
            testactive_th_list = ticker_history_repo.get_ticker_history_by_symbol("TESTACTIVE")

            assert len(testsplit_th_list) > 0, "TESTSPLIT ticker_history not found"
            assert len(testdelist_th_list) > 0, "TESTDELIST ticker_history not found"
            assert len(testactive_th_list) > 0, "TESTACTIVE ticker_history not found"

            testsplit_th = testsplit_th_list[0]
            testdelist_th = testdelist_th_list[0]
            testactive_th = testactive_th_list[0]

            # Create multiple threshold configurations using fixture expectations
            configs = [
                LowHighPatternConfig(threshold=threshold)
                for threshold in sorted(FixtureDataExpectations.MULTI_CONFIG_THRESHOLDS)
            ]

            # Get backfill pipeline
            pipeline = get_backfill_pipeline(configs)

            # Run backfill for all ticker histories
            print("\n🔄 Running backfill pipeline for all test companies...")
            results = pipeline.run(
                from_date=FixtureDataExpectations.FROM_DATE,
                to_date=FixtureDataExpectations.TO_DATE,
            )

            # Verify exactly 3 results were returned
            assert len(results) == 3, f"Expected exactly 3 results, got {len(results)}"

            # Find results for each ticker
            testsplit_result = next(
                r for r in results if r["ticker_history_id"] == testsplit_th.id
            )
            testdelist_result = next(
                r for r in results if r["ticker_history_id"] == testdelist_th.id
            )
            testactive_result = next(
                r for r in results if r["ticker_history_id"] == testactive_th.id
            )

            # Validate TESTSPLIT result with exact assertions
            print(f"\n✅ TESTSPLIT result: {testsplit_result}")
            validate_backfill_result(
                result=testsplit_result,
                ticker_symbol="TESTSPLIT",
                ticker_history_id=testsplit_th.id,
                expected_from_date="2025-11-01",
                expected_to_date="2025-11-30",
                expected_pattern_count=FixtureDataExpectations.TESTSPLIT_TOTAL,
            )

            # Validate TESTDELIST result with exact assertions
            print(f"✅ TESTDELIST result: {testdelist_result}")
            validate_backfill_result(
                result=testdelist_result,
                ticker_symbol="TESTDELIST",
                ticker_history_id=testdelist_th.id,
                expected_from_date="2025-11-01",
                expected_to_date="2025-11-25",  # Delisted on day 25
                expected_pattern_count=FixtureDataExpectations.TESTDELIST_TOTAL,
            )

            # Validate TESTACTIVE result with exact assertions
            print(f"✅ TESTACTIVE result: {testactive_result}")
            validate_backfill_result(
                result=testactive_result,
                ticker_symbol="TESTACTIVE",
                ticker_history_id=testactive_th.id,
                expected_from_date="2025-11-01",
                expected_to_date="2025-11-30",
                expected_pattern_count=FixtureDataExpectations.TESTACTIVE_TOTAL,
            )

            # Query database to verify patterns were stored
            testsplit_highs = highs_repo.get_by_ticker_history_id(testsplit_th.id)
            testdelist_highs = highs_repo.get_by_ticker_history_id(testdelist_th.id)
            testactive_highs = highs_repo.get_by_ticker_history_id(testactive_th.id)

            print(f"\n📊 TESTSPLIT: {len(testsplit_highs)} highs in database")
            print(f"📊 TESTDELIST: {len(testdelist_highs)} highs in database")
            print(f"📊 TESTACTIVE: {len(testactive_highs)} highs in database")

            # Validate TESTSPLIT patterns in database with exact assertions
            validate_patterns_in_database(
                patterns=testsplit_highs,
                ticker_symbol="TESTSPLIT",
                ticker_history_id=testsplit_th.id,
                expected_count=FixtureDataExpectations.TESTSPLIT_DB_COUNT,
                expected_thresholds=FixtureDataExpectations.MULTI_CONFIG_THRESHOLDS,
            )

            # Validate TESTDELIST patterns in database with exact assertions
            validate_patterns_in_database(
                patterns=testdelist_highs,
                ticker_symbol="TESTDELIST",
                ticker_history_id=testdelist_th.id,
                expected_count=FixtureDataExpectations.TESTDELIST_DB_COUNT,
                expected_thresholds=FixtureDataExpectations.MULTI_CONFIG_THRESHOLDS,
            )

            # Validate delisting date constraint for TESTDELIST
            validate_pattern_dates_before_delisting(
                patterns=testdelist_highs,
                delisting_date=FixtureDataExpectations.TESTDELIST_DELIST_DATE,
                ticker_symbol="TESTDELIST",
            )

            # Validate TESTACTIVE patterns in database with exact assertions
            validate_patterns_in_database(
                patterns=testactive_highs,
                ticker_symbol="TESTACTIVE",
                ticker_history_id=testactive_th.id,
                expected_count=FixtureDataExpectations.TESTACTIVE_DB_COUNT,
                expected_thresholds=FixtureDataExpectations.MULTI_CONFIG_THRESHOLDS,
            )

            print("\n✅ All backfill integration tests passed!")

    def test_backfill_single_ticker_with_split(self):
        """Test backfill for a single ticker with split adjustment.

        Validates:
        - Single ticker processing works correctly
        - Split adjustment is applied
        - Pattern generation respects date range
        """
        with integration_test_container("options-deep-test-data:latest") as (
            postgres,
            _,
            port,
        ):
            from src.pipelines.algorithms.low_highs import get_backfill_pipeline
            from src.repos.algorithms.low_highs.highs_repository import (
                HighsRepository,
            )
            from src.repos.equities.tickers.ticker_history_repository import (
                TickerHistoryRepository,
            )

            ticker_history_repo = TickerHistoryRepository()
            highs_repo = HighsRepository()

            # Get TESTSPLIT ticker history
            testsplit_th_list = ticker_history_repo.get_ticker_history_by_symbol("TESTSPLIT")
            assert len(testsplit_th_list) > 0, "TESTSPLIT ticker_history not found"
            testsplit_th = testsplit_th_list[0]

            # Create single config using 20% threshold
            single_threshold = Decimal("0.20")
            configs = [LowHighPatternConfig(threshold=single_threshold)]

            # Get pipeline and process single ticker
            pipeline = get_backfill_pipeline(configs)
            result = pipeline._process_single_ticker(
                ticker_history_id=testsplit_th.id,
                from_date=FixtureDataExpectations.FROM_DATE,
                to_date=FixtureDataExpectations.TO_DATE,
            )

            print(f"\n✅ Single ticker result: {result}")

            # Expected counts for single threshold (20%)
            # Active patterns in DB
            expected_db_count = FixtureDataExpectations.TESTSPLIT_PATTERNS[single_threshold]
            # Total patterns generated (active + completed) - TESTSPLIT 20% = 2 total
            expected_total_count = 2

            # Validate result with exact assertions
            validate_backfill_result(
                result=result,
                ticker_symbol="TESTSPLIT",
                ticker_history_id=testsplit_th.id,
                expected_from_date="2025-11-01",
                expected_to_date="2025-11-30",
                expected_pattern_count=expected_total_count,
            )

            # Verify patterns in database with exact count and threshold
            highs = highs_repo.get_by_ticker_history_id(testsplit_th.id)
            validate_patterns_in_database(
                patterns=highs,
                ticker_symbol="TESTSPLIT",
                ticker_history_id=testsplit_th.id,
                expected_count=expected_db_count,
                expected_thresholds={single_threshold},
            )

            print(f"📊 Generated {len(highs)} high patterns for TESTSPLIT")
            print("✅ Single ticker backfill test passed!")

    def test_backfill_delisted_company(self):
        """Test backfill for delisted company.

        Validates:
        - Delisted companies are processed correctly
        - Patterns respect delisting date (valid_to)
        - No patterns generated after delisting
        """
        with integration_test_container("options-deep-test-data:latest") as (
            postgres,
            _,
            port,
        ):
            from src.pipelines.algorithms.low_highs import get_backfill_pipeline
            from src.repos.algorithms.low_highs.highs_repository import (
                HighsRepository,
            )
            from src.repos.equities.tickers.ticker_history_repository import (
                TickerHistoryRepository,
            )

            ticker_history_repo = TickerHistoryRepository()
            highs_repo = HighsRepository()

            # Get TESTDELIST ticker history
            testdelist_th_list = ticker_history_repo.get_ticker_history_by_symbol("TESTDELIST")
            assert len(testdelist_th_list) > 0, "TESTDELIST ticker_history not found"
            testdelist_th = testdelist_th_list[0]
            assert testdelist_th.valid_to is not None, "TESTDELIST should be delisted"
            assert testdelist_th.valid_to == FixtureDataExpectations.TESTDELIST_DELIST_DATE, (
                f"TESTDELIST should be delisted on {FixtureDataExpectations.TESTDELIST_DELIST_DATE}"
            )

            # Create config using 15% threshold
            single_threshold = Decimal("0.15")
            configs = [LowHighPatternConfig(threshold=single_threshold)]

            # Get pipeline and process delisted ticker
            pipeline = get_backfill_pipeline(configs)
            result = pipeline._process_single_ticker(
                ticker_history_id=testdelist_th.id,
                from_date=FixtureDataExpectations.FROM_DATE,
                to_date=FixtureDataExpectations.TO_DATE,  # Range extends beyond delisting
            )

            print(f"\n✅ Delisted company result: {result}")

            # Expected counts for single threshold (15%)
            # Active patterns in DB
            expected_db_count = FixtureDataExpectations.TESTDELIST_PATTERNS[single_threshold]
            # Total patterns generated (active + completed) - TESTDELIST 15% = 2 total
            expected_total_count = 2

            # Validate result with exact assertions
            validate_backfill_result(
                result=result,
                ticker_symbol="TESTDELIST",
                ticker_history_id=testdelist_th.id,
                expected_from_date="2025-11-01",
                expected_to_date="2025-11-25",  # Should only process up to delisting date
                expected_pattern_count=expected_total_count,
            )

            # Verify patterns in database with exact count and threshold
            highs = highs_repo.get_by_ticker_history_id(testdelist_th.id)
            validate_patterns_in_database(
                patterns=highs,
                ticker_symbol="TESTDELIST",
                ticker_history_id=testdelist_th.id,
                expected_count=expected_db_count,
                expected_thresholds={single_threshold},
            )

            # Validate all patterns are dated on or before delisting date
            validate_pattern_dates_before_delisting(
                patterns=highs,
                delisting_date=FixtureDataExpectations.TESTDELIST_DELIST_DATE,
                ticker_symbol="TESTDELIST",
            )

            print(f"📊 Generated {len(highs)} high patterns for TESTDELIST")
            print("✅ Delisted company backfill test passed!")
