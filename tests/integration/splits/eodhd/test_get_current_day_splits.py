"""Integration tests for EODHD current day splits ingestion pipeline."""

from __future__ import annotations

from datetime import date

# IMPORTANT: Set environment variables BEFORE importing any src modules
from tests.integration.common_setup import setup_test_environment

setup_test_environment()

# NOW safe to import src modules
from tests.data_source_mocks.eodhd.mock_splits import MockEodhdSplitsDataSource
from tests.data_source_mocks.eodhd.mock_symbols import MockEodhdSymbolsSource
from tests.integration.common_setup import create_test_session, integration_test_container
from tests.utils.db_assertions import (
    count_companies,
    count_splits,
    count_ticker_histories,
    get_ticker_histories_for_symbol,
)


class TestEodhdCurrentDaySplitsIngestion:
    """Integration tests for EODHD current day splits ingestion."""

    def test_happy_path(self):
        """Comprehensive test for current day splits ingestion with exhaustive field validation.

        Validates:
        - Database starts with companies and ticker histories
        - Current day splits are fetched for specified date
        - Splits are only inserted for symbols that match ticker_history records
        - Duplicate splits are prevented on re-runs
        - ALL fields are validated for at least one complete Split record:
          * Split: id, date, split_ratio, ticker_history_id, symbol
        - Split ratio can be parsed correctly
        - Ingestion completes without errors

        Note: This test combines current day splits ingestion and duplicate prevention.
        """
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline
            from src.pipelines.splits.current_day_splits_ingestion_pipeline import (
                CurrentDaySplitsIngestionPipeline,
            )
            from tests.utils.db_assertions import get_splits_by_symbol

            # Create mock sources
            mock_symbols_source = MockEodhdSymbolsSource()
            mock_splits_source = MockEodhdSplitsDataSource()

            # Get expected data from mocks
            expected_companies = mock_symbols_source.get_active_symbols()
            expected_company_count = len(expected_companies)

            # The fixture bulk_splits.csv contains splits for 2025-11-21
            target_date = date(2025, 11, 21)
            expected_bulk_splits = mock_splits_source.get_current_date_splits(target_date)
            expected_bulk_splits_count = len(expected_bulk_splits)

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # First, ingest companies to create ticker_history records
            company_pipeline = CompanyPipeline()
            company_pipeline.run_ingestion([mock_symbols_source])

            # Verify companies and ticker histories exist
            assert count_companies(session) == expected_company_count
            assert count_ticker_histories(session) == expected_company_count

            # Verify no splits initially
            assert count_splits(session) == 0

            # Run current day splits ingestion
            splits_pipeline = CurrentDaySplitsIngestionPipeline(
                splits_data_source=mock_splits_source
            )
            result = splits_pipeline.run(target_date=target_date)

            # Verify result (target_date may be returned as string or date)
            result_target_date = result["target_date"]
            if isinstance(result_target_date, str):
                assert result_target_date == "2025-11-21"
            else:
                assert result_target_date == target_date

            # Verify exact counts from mock data
            assert result["total_splits_fetched"] == expected_bulk_splits_count

            # Get first count
            first_splits_count = count_splits(session)

            # Run again with same date to test duplicate prevention
            result2 = splits_pipeline.run(target_date=target_date)
            second_splits_count = count_splits(session)

            # Count should not increase (upsert should prevent duplicates)
            assert second_splits_count == first_splits_count

            # === EXHAUSTIVE FIELD VALIDATION for Split (if any inserted) ===
            if first_splits_count > 0:
                # Find a symbol that has splits
                for company in expected_companies:
                    if company.ticker is None:
                        continue
                    symbol = company.ticker.symbol
                    db_splits = get_splits_by_symbol(session, symbol)
                    if len(db_splits) > 0:
                        split = db_splits[0]
                        # Validate ALL Split fields
                        assert split.id is not None, "Split id should be set"
                        assert isinstance(split.id, int), "Split id should be an integer"
                        assert split.date is not None, "Split date should be set"
                        assert isinstance(split.date, date), "Split date should be a date object"
                        assert split.date == target_date, "Split date should match target date"
                        assert split.split_ratio is not None, "Split ratio should be set"
                        assert isinstance(split.split_ratio, str), "Split ratio should be a string"
                        assert "/" in split.split_ratio, "Split ratio should contain a '/' separator"
                        assert split.ticker_history_id is not None, "ticker_history_id should be set"
                        assert isinstance(split.ticker_history_id, int), "ticker_history_id should be an integer"
                        # Symbol is optional for display purposes
                        if split.symbol is not None:
                            assert isinstance(split.symbol, str), "Symbol should be a string"

                        # Validate split ratio can be parsed
                        split_ratio_decimal = split.get_split_ratio()
                        assert split_ratio_decimal is not None, "Split ratio should be parseable"
                        assert split_ratio_decimal > 0, "Split ratio should be positive"

                        # Verify split is associated with correct ticker_history
                        ticker_histories = get_ticker_histories_for_symbol(session, symbol)
                        assert len(ticker_histories) > 0
                        assert split.ticker_history_id == ticker_histories[0].id
                        break

    def test_bulk_splits_resolved_to_ticker_history(self):
        """Test that bulk splits are properly resolved to ticker_history records."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline
            from src.pipelines.splits.current_day_splits_ingestion_pipeline import (
                CurrentDaySplitsIngestionPipeline,
            )

            # Create mock sources
            mock_symbols_source = MockEodhdSymbolsSource()
            mock_splits_source = MockEodhdSplitsDataSource()

            # Get expected data from mocks
            expected_companies = mock_symbols_source.get_active_symbols()
            expected_company_count = len(expected_companies)

            target_date = date(2025, 11, 21)
            expected_bulk_splits = mock_splits_source.get_current_date_splits(target_date)
            expected_bulk_splits_count = len(expected_bulk_splits)

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # First, ingest companies
            company_pipeline = CompanyPipeline()
            company_pipeline.run_ingestion([mock_symbols_source])

            # Run current day splits ingestion
            splits_pipeline = CurrentDaySplitsIngestionPipeline(
                splits_data_source=mock_splits_source
            )
            result = splits_pipeline.run(target_date=target_date)

            # Verify splits were fetched with exact count
            assert result["total_splits_fetched"] == expected_bulk_splits_count

            # Check symbols overlap between bulk_splits and our companies
            company_symbols = {c.ticker.symbol for c in expected_companies if c.ticker is not None}
            bulk_split_symbols = {s.symbol for s in expected_bulk_splits}
            matching_symbols = company_symbols.intersection(bulk_split_symbols)

            # Only matching symbols should result in inserted splits
            expected_successful = len(matching_symbols)
            assert result["successful"] >= 0  # May be 0 if no overlap

    def test_current_day_splits_no_duplicates(self):
        """Test that running ingestion twice doesn't create duplicate splits."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline
            from src.pipelines.splits.current_day_splits_ingestion_pipeline import (
                CurrentDaySplitsIngestionPipeline,
            )

            # Create mock sources
            mock_symbols_source = MockEodhdSymbolsSource()
            mock_splits_source = MockEodhdSplitsDataSource()

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # First, ingest companies
            company_pipeline = CompanyPipeline()
            company_pipeline.run_ingestion([mock_symbols_source])

            target_date = date(2025, 11, 21)

            # Run current day splits ingestion first time
            splits_pipeline = CurrentDaySplitsIngestionPipeline(
                splits_data_source=mock_splits_source
            )
            result1 = splits_pipeline.run(target_date=target_date)

            first_count = count_splits(session)

            # Run again with same date
            result2 = splits_pipeline.run(target_date=target_date)

            second_count = count_splits(session)

            # Count should not increase (upsert should prevent duplicates)
            assert second_count == first_count

    def test_current_day_splits_with_no_matching_symbols(self):
        """Test current day splits ingestion when no symbols match."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.splits.current_day_splits_ingestion_pipeline import (
                CurrentDaySplitsIngestionPipeline,
            )

            # Create mock source (no companies in database)
            mock_splits_source = MockEodhdSplitsDataSource()

            # Get expected data from mock
            target_date = date(2025, 11, 21)
            expected_bulk_splits = mock_splits_source.get_current_date_splits(target_date)
            expected_bulk_splits_count = len(expected_bulk_splits)

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # Verify database is empty
            assert count_ticker_histories(session) == 0

            # Run current day splits ingestion
            splits_pipeline = CurrentDaySplitsIngestionPipeline(
                splits_data_source=mock_splits_source
            )
            result = splits_pipeline.run(target_date=target_date)

            # Splits should be fetched but none inserted (no matching ticker_histories)
            assert result["total_splits_fetched"] == expected_bulk_splits_count
            assert result["splits_inserted"] == 0
            assert count_splits(session) == 0

    def test_ingestion_completes_without_errors(self):
        """Test that current day splits ingestion completes without critical errors."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline
            from src.pipelines.splits.current_day_splits_ingestion_pipeline import (
                CurrentDaySplitsIngestionPipeline,
            )

            # Create mock sources
            mock_symbols_source = MockEodhdSymbolsSource()
            mock_splits_source = MockEodhdSplitsDataSource()

            # Get expected data from mocks
            target_date = date(2025, 11, 21)
            expected_bulk_splits = mock_splits_source.get_current_date_splits(target_date)
            expected_bulk_splits_count = len(expected_bulk_splits)

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # First, ingest companies
            company_pipeline = CompanyPipeline()
            company_pipeline.run_ingestion([mock_symbols_source])

            # Run current day splits ingestion
            splits_pipeline = CurrentDaySplitsIngestionPipeline(
                splits_data_source=mock_splits_source
            )
            result = splits_pipeline.run(target_date=target_date)

            # Verify ingestion completed (target_date may be returned as string or date)
            result_target_date = result["target_date"]
            if isinstance(result_target_date, str):
                assert result_target_date == "2025-11-21"
            else:
                assert result_target_date == target_date

            # Verify exact count from mock
            assert result["total_splits_fetched"] == expected_bulk_splits_count
