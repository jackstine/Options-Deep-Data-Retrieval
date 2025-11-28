"""Integration tests for EODHD active historical EOD ingestion pipeline."""

from __future__ import annotations

# IMPORTANT: Set environment variables BEFORE importing any src modules
from tests.integration.common_setup import setup_test_environment

setup_test_environment()

# NOW safe to import src modules
from tests.data_source_mocks.eodhd.mock_eod_data import MockEodhdDataSource
from tests.data_source_mocks.eodhd.mock_symbols import MockEodhdSymbolsSource
from tests.integration.common_setup import create_test_session, integration_test_container
from tests.utils.db_assertions import (
    assert_company_exists,
    count_companies,
    count_historical_eod_pricing,
    count_ticker_histories,
    count_tickers,
    get_company_by_name,
    get_ticker_histories_for_symbol,
)


class TestEodhdActiveHistoricalEodIngestion:
    """Integration tests for EODHD active historical EOD ingestion."""

    def test_ingestion_creates_companies_with_pricing_data(self):
        """Test that ingestion creates companies and inserts historical pricing data."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.eod.active_new_listing_pipeline import (
                ActiveNewListingPipeline,
            )

            # Create mock sources
            mock_symbols_source = MockEodhdSymbolsSource()
            mock_historical_source = MockEodhdDataSource()

            # Get expected data from mocks
            expected_companies = mock_symbols_source.get_active_symbols()
            expected_company_count = len(expected_companies)

            # Get sample EOD data to know how many records per symbol
            ticker = expected_companies[0].ticker
            assert ticker is not None, "Expected company to have ticker"
            sample_symbol = ticker.symbol
            sample_eod_data = mock_historical_source.get_eod_data(sample_symbol)
            expected_pricing_per_symbol = len(sample_eod_data)

            # Create pipeline
            pipeline = ActiveNewListingPipeline(
                company_source=mock_symbols_source,
                historical_source=mock_historical_source,
            )

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # Verify database is empty
            assert count_companies(session) == 0
            assert count_historical_eod_pricing(session) == 0

            # Run ingestion
            result = pipeline.run_ingestion(test_limit=None)

            # Verify companies were created using exact counts
            assert result["companies_inserted"] == expected_company_count
            assert result["tickers_inserted"] == expected_company_count
            assert result["ticker_histories_inserted"] == expected_company_count

            # Verify pricing data was inserted
            expected_total_pricing = expected_company_count * expected_pricing_per_symbol
            assert result["pricing_records_inserted"] == expected_total_pricing
            assert count_historical_eod_pricing(session) == expected_total_pricing

    def test_pricing_data_associated_with_ticker_history(self):
        """Test that pricing data is properly associated with ticker_history records."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.eod.active_new_listing_pipeline import (
                ActiveNewListingPipeline,
            )

            # Create mock sources
            mock_symbols_source = MockEodhdSymbolsSource()
            mock_historical_source = MockEodhdDataSource()

            # Get expected data from mocks
            expected_companies = mock_symbols_source.get_active_symbols()
            first_company = expected_companies[0]
            assert first_company.ticker is not None, "Expected company to have ticker"
            first_symbol = first_company.ticker.symbol

            # Get expected EOD data
            expected_eod_data = mock_historical_source.get_eod_data(first_symbol)
            expected_pricing_count = len(expected_eod_data)

            # Create pipeline
            pipeline = ActiveNewListingPipeline(
                company_source=mock_symbols_source,
                historical_source=mock_historical_source,
            )

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # Run ingestion with limit of 1
            pipeline.run_ingestion(test_limit=1)

            # Verify company exists using data from mock
            company = assert_company_exists(
                session,
                first_company.company_name,
                expected_fields={
                    "exchange": first_company.exchange,
                    "sector": first_company.sector,
                },
            )

            # Get ticker history for the company
            ticker_histories = get_ticker_histories_for_symbol(session, first_symbol)
            assert len(ticker_histories) == 1

            ticker_history = ticker_histories[0]
            assert ticker_history.company_id == company.id

            # Verify pricing data exists for this ticker_history with exact count
            pricing_count = count_historical_eod_pricing(
                session, ticker_history_id=ticker_history.id
            )
            assert pricing_count == expected_pricing_count

    def test_no_errors_during_ingestion(self):
        """Test that ingestion completes without errors."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.eod.active_new_listing_pipeline import (
                ActiveNewListingPipeline,
            )

            # Create mock sources
            mock_symbols_source = MockEodhdSymbolsSource()
            mock_historical_source = MockEodhdDataSource()

            # Get expected data from mocks
            expected_companies = mock_symbols_source.get_active_symbols()
            expected_company_count = len(expected_companies)

            # Create pipeline
            pipeline = ActiveNewListingPipeline(
                company_source=mock_symbols_source,
                historical_source=mock_historical_source,
            )

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # Run ingestion
            result = pipeline.run_ingestion(test_limit=None)

            # Verify no errors and exact counts
            assert len(result.get("errors", [])) == 0
            assert result.get("processed", 0) == expected_company_count
