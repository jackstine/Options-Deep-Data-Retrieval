"""Integration tests for EODHD daily EOD ingestion pipeline."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

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

    def test_happy_path(self):
        """Comprehensive test for bulk EOD data ingestion with exhaustive field validation.

        Validates:
        - Database starts with companies and ticker histories
        - Bulk EOD data is routed to correct tables:
          * Known tickers → historical_eod_pricing
          * Unknown tickers → misplaced_eod_pricing
        - ALL fields are validated for at least one complete record:
          * MisplacedEndOfDayPricing: symbol, date, open, high, low, close,
                                       adjusted_close, volume, source
        - OHLC relationships: high >= low, etc.
        - Ingestion completes without errors

        Note: HistoricalEndOfDayPricing fields were validated in
        test_active_historical_eod_ingestion.py
        """
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.eod.current_day_eod_pricings import (
                DailyEodIngestionPipeline,
            )
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline
            from src.repos.equities.pricing.misplaced_eod_pricing_repository import (
                MisplacedEodPricingRepository,
            )

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

            # === EXHAUSTIVE FIELD VALIDATION for MisplacedEndOfDayPricing ===
            # Validate exhaustive fields only if there are misplaced pricing records
            if expected_misplaced > 0:
                # Get misplaced pricing records for validation
                misplaced_repo = MisplacedEodPricingRepository()
                misplaced_records = misplaced_repo.get_all()
                assert len(misplaced_records) > 0, "Should have misplaced pricing records"

                # Validate first misplaced pricing record
                misplaced = misplaced_records[0]
                assert misplaced.symbol is not None, "Symbol should be set"
                assert isinstance(misplaced.symbol, str), "Symbol should be a string"
                assert misplaced.date is not None, "Date should be set"
                assert isinstance(misplaced.date, date), "Date should be a date object"
                assert misplaced.open is not None, "Open price should be set"
                assert isinstance(misplaced.open, Decimal), "Open should be a Decimal"
                assert misplaced.high is not None, "High price should be set"
                assert isinstance(misplaced.high, Decimal), "High should be a Decimal"
                assert misplaced.low is not None, "Low price should be set"
                assert isinstance(misplaced.low, Decimal), "Low should be a Decimal"
                assert misplaced.close is not None, "Close price should be set"
                assert isinstance(misplaced.close, Decimal), "Close should be a Decimal"
                assert misplaced.adjusted_close is not None, "Adjusted close should be set"
                assert isinstance(misplaced.adjusted_close, Decimal), "Adjusted close should be a Decimal"
                assert misplaced.volume is not None, "Volume should be set"
                assert isinstance(misplaced.volume, int), "Volume should be an integer"
                assert misplaced.source is not None, "Source should be set"

                # Validate OHLC relationships
                assert misplaced.high >= misplaced.low, "High must be >= Low"
                assert misplaced.high >= misplaced.open, "High must be >= Open"
                assert misplaced.high >= misplaced.close, "High must be >= Close"
                assert misplaced.low <= misplaced.open, "Low must be <= Open"
                assert misplaced.low <= misplaced.close, "Low must be <= Close"

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
