"""Integration tests for EODHD daily EOD ingestion pipeline."""

from __future__ import annotations

# IMPORTANT: Set environment variables BEFORE importing any src modules
from tests.integration.common_setup import setup_test_environment

setup_test_environment()

# NOW safe to import src modules
from tests.data_source_mocks.eodhd.mock_bulk_eod_data import MockEodhdDailyBulkEodData
from tests.data_source_mocks.eodhd.mock_symbols import MockEodhdSymbolsSource
from tests.integration.common_setup import create_test_session, integration_test_container
from tests.utils.db_assertions import (
    count_companies,
    count_historical_eod_pricing,
    count_misplaced_eod_pricing,
    count_ticker_histories,
    count_tickers,
)


class TestEodhdDailyEodIngestion:
    """Integration tests for EODHD daily EOD ingestion."""

    def test_bulk_eod_data_routes_to_correct_tables(self):
        """Test that bulk EOD data is routed to historical or misplaced pricing tables."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.eod.current_day_eod_pricings import (
                DailyEodIngestionPipeline,
            )
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline

            # Create mock sources
            mock_symbols_source = MockEodhdSymbolsSource()
            mock_bulk_source = MockEodhdDailyBulkEodData()

            # Get expected data from mocks
            expected_companies = mock_symbols_source.get_active_symbols()
            expected_company_count = len(expected_companies)

            # Get bulk EOD data to know what to expect
            bulk_eod_data = mock_bulk_source.get_bulk_latest_eod(
                exchange="US", filter_common_stock=True
            )
            expected_bulk_symbols = len(bulk_eod_data)

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # First, ingest companies so we have ticker_history records
            company_pipeline = CompanyPipeline()
            company_pipeline.run_ingestion([mock_symbols_source])

            # Verify companies exist
            assert count_companies(session) == expected_company_count
            assert count_tickers(session) == expected_company_count
            assert count_ticker_histories(session) == expected_company_count

            # Now run EOD ingestion
            eod_pipeline = DailyEodIngestionPipeline(bulk_eod_source=mock_bulk_source)
            result = eod_pipeline.run(
                exchange="US", filter_common_stock=True, test_limit=None
            )

            # Verify data was routed correctly with exact counts
            assert result["total_symbols_from_api"] == expected_bulk_symbols
            assert result["tickers_in_db"] == expected_company_count

            # All symbols in bulk that match our companies should go to historical
            assert result["historical_pricing_inserted"] == expected_company_count

            # Symbols in bulk that don't match should go to misplaced
            # (bulk_symbols - matched_symbols)
            expected_misplaced = expected_bulk_symbols - expected_company_count
            assert result["misplaced_pricing_inserted"] == expected_misplaced

    def test_known_tickers_go_to_historical_pricing(self):
        """Test that EOD data for known tickers goes to historical_eod_pricing."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline
            from src.pipelines.eod.current_day_eod_pricings import (
                DailyEodIngestionPipeline,
            )

            # Create mock sources
            mock_symbols_source = MockEodhdSymbolsSource()
            mock_bulk_source = MockEodhdDailyBulkEodData()

            # Get expected data from mocks
            expected_companies = mock_symbols_source.get_active_symbols()
            expected_company_count = len(expected_companies)

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # First, ingest companies
            company_pipeline = CompanyPipeline()
            company_pipeline.run_ingestion([mock_symbols_source])

            # Get count of companies
            companies_count = count_companies(session)
            assert companies_count == expected_company_count

            # Run EOD ingestion
            eod_pipeline = DailyEodIngestionPipeline(bulk_eod_source=mock_bulk_source)
            result = eod_pipeline.run(
                exchange="US", filter_common_stock=True, test_limit=None
            )

            # Verify historical pricing was inserted with exact count
            assert result["historical_pricing_inserted"] == expected_company_count
            assert count_historical_eod_pricing(session) == expected_company_count

    def test_unknown_tickers_go_to_misplaced_pricing(self):
        """Test that EOD data for unknown tickers goes to misplaced_eod_pricing."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.eod.current_day_eod_pricings import (
                DailyEodIngestionPipeline,
            )

            # Create mock sources (don't ingest companies first)
            mock_bulk_source = MockEodhdDailyBulkEodData()

            # Get bulk data without filtering to know total count
            bulk_eod_data_unfiltered = mock_bulk_source.get_bulk_latest_eod(
                exchange="US", filter_common_stock=False
            )
            expected_total_symbols = len(bulk_eod_data_unfiltered)

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # Verify database is empty
            assert count_companies(session) == 0
            assert count_ticker_histories(session) == 0

            # Run EOD ingestion without any companies in database
            eod_pipeline = DailyEodIngestionPipeline(bulk_eod_source=mock_bulk_source)
            result = eod_pipeline.run(
                exchange="US", filter_common_stock=False, test_limit=None
            )

            # All data should go to misplaced pricing with exact count
            assert result["misplaced_pricing_inserted"] == expected_total_symbols
            assert count_misplaced_eod_pricing(session) == expected_total_symbols

            # No historical pricing should be inserted
            assert result["historical_pricing_inserted"] == 0
            assert count_historical_eod_pricing(session) == 0

    def test_ingestion_completes_without_errors(self):
        """Test that bulk EOD ingestion completes without errors."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.eod.current_day_eod_pricings import (
                DailyEodIngestionPipeline,
            )

            # Create mock source
            mock_bulk_source = MockEodhdDailyBulkEodData()

            # Get expected data from mock
            bulk_eod_data = mock_bulk_source.get_bulk_latest_eod(
                exchange="US", filter_common_stock=True
            )
            expected_symbols = len(bulk_eod_data)

            # Run EOD ingestion
            eod_pipeline = DailyEodIngestionPipeline(bulk_eod_source=mock_bulk_source)
            result = eod_pipeline.run(
                exchange="US", filter_common_stock=True, test_limit=None
            )

            # Verify no errors and exact counts
            assert result["errors"] == 0
            assert result["total_symbols_from_api"] == expected_symbols
