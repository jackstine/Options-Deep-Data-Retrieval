"""Integration tests for EODHD all companies splits ingestion pipeline."""

from __future__ import annotations

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
    count_tickers,
    get_splits_by_symbol,
    get_ticker_histories_for_symbol,
)


class TestEodhdAllCompaniesSplitsIngestion:
    """Integration tests for EODHD all companies splits ingestion."""

    def test_splits_ingestion_for_active_companies(self):
        """Test that splits are ingested for all active companies with ticker_history."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline
            from src.pipelines.splits.all_stocks_splits_ingestion_pipeline import (
                AllStocksSplitsIngestionPipeline,
            )

            # Create mock sources
            mock_symbols_source = MockEodhdSymbolsSource()
            mock_splits_source = MockEodhdSplitsDataSource()

            # Get expected data from mocks
            expected_companies = mock_symbols_source.get_active_symbols()
            expected_company_count = len(expected_companies)

            # Get expected splits data for first company
            first_company = expected_companies[0]
            first_symbol = first_company.ticker.symbol
            expected_splits = mock_splits_source.get_splits(first_symbol)
            expected_splits_count = len(expected_splits)

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

            # Run splits ingestion
            splits_pipeline = AllStocksSplitsIngestionPipeline(
                splits_data_source=mock_splits_source
            )
            result = splits_pipeline.run()

            # Verify results with exact counts
            assert result["total_ticker_histories"] == expected_company_count
            assert result["processed"] == expected_company_count

            # All companies get same fixture data, so total = company_count * splits_per_company
            expected_total_splits = expected_company_count * expected_splits_count
            assert result["total_splits_inserted"] == expected_total_splits
            assert count_splits(session) == expected_total_splits

    def test_splits_associated_with_ticker_history(self):
        """Test that splits are properly associated with ticker_history records."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline
            from src.pipelines.splits.all_stocks_splits_ingestion_pipeline import (
                AllStocksSplitsIngestionPipeline,
            )

            # Create mock sources
            mock_symbols_source = MockEodhdSymbolsSource()
            mock_splits_source = MockEodhdSplitsDataSource()

            # Get expected data from mocks
            expected_companies = mock_symbols_source.get_active_symbols()
            first_company = expected_companies[0]
            first_symbol = first_company.ticker.symbol

            # Get expected splits data
            expected_splits = mock_splits_source.get_splits(first_symbol)
            expected_splits_count = len(expected_splits)

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # First, ingest companies
            company_pipeline = CompanyPipeline()
            company_pipeline.run_ingestion([mock_symbols_source])

            # Run splits ingestion
            splits_pipeline = AllStocksSplitsIngestionPipeline(
                splits_data_source=mock_splits_source
            )
            splits_pipeline.run()

            # Get ticker histories for the first symbol
            ticker_histories = get_ticker_histories_for_symbol(session, first_symbol)
            assert len(ticker_histories) == 1

            ticker_history = ticker_histories[0]

            # Verify splits exist for this ticker_history with exact count
            split_count = count_splits(session, ticker_history_id=ticker_history.id)
            assert split_count == expected_splits_count

    def test_splits_ingestion_completes_without_errors(self):
        """Test that splits ingestion completes without critical errors."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline
            from src.pipelines.splits.all_stocks_splits_ingestion_pipeline import (
                AllStocksSplitsIngestionPipeline,
            )

            # Create mock sources
            mock_symbols_source = MockEodhdSymbolsSource()
            mock_splits_source = MockEodhdSplitsDataSource()

            # Get expected data from mocks
            expected_companies = mock_symbols_source.get_active_symbols()
            expected_company_count = len(expected_companies)

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # First, ingest companies
            company_pipeline = CompanyPipeline()
            company_pipeline.run_ingestion([mock_symbols_source])

            # Run splits ingestion
            splits_pipeline = AllStocksSplitsIngestionPipeline(
                splits_data_source=mock_splits_source
            )
            result = splits_pipeline.run()

            # Verify ingestion completed with exact counts
            assert result["processed"] == expected_company_count
            assert result["total_ticker_histories"] == expected_company_count
            assert result["successful"] == expected_company_count
            assert result["failed"] == 0

    def test_no_splits_ingested_for_empty_database(self):
        """Test that no splits are ingested when database has no ticker_history records."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.splits.all_stocks_splits_ingestion_pipeline import (
                AllStocksSplitsIngestionPipeline,
            )

            # Create mock source
            mock_splits_source = MockEodhdSplitsDataSource()

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # Verify database is empty
            assert count_ticker_histories(session) == 0
            assert count_splits(session) == 0

            # Run splits ingestion on empty database
            splits_pipeline = AllStocksSplitsIngestionPipeline(
                splits_data_source=mock_splits_source
            )
            result = splits_pipeline.run()

            # No ticker_histories means no splits can be inserted - exact counts
            assert result["total_ticker_histories"] == 0
            assert result["processed"] == 0
            assert result["total_splits_inserted"] == 0
            assert count_splits(session) == 0
