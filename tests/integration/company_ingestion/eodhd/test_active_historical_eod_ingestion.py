"""Integration tests for EODHD active historical EOD ingestion pipeline."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

# IMPORTANT: Set environment variables BEFORE importing any src modules
from tests.integration.common_setup import setup_test_environment

setup_test_environment()

# NOW safe to import src modules
from tests.data_source_mocks.eodhd.mock_eod_data import MockEodhdDataSource
from tests.data_source_mocks.eodhd.mock_symbols import MockEodhdSymbolsSource
from tests.integration.common_setup import create_test_session, integration_test_container
from tests.integration.db.db_assertions import (
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

    def test_happy_path(self):
        """Test that ingestion creates companies and inserts historical pricing data with exhaustive field validation.

        Validates:
        - All active symbols from fixture are ingested
        - Historical EOD pricing data is ingested for each company
        - Company, Ticker, and TickerHistory records are created
        - HistoricalEndOfDayPricing records are properly linked to ticker_history
        - ALL fields are validated for at least one complete record:
          * Company: id, company_name, exchange, sector, industry, country, market_cap,
                     description, active, is_valid_data, source
          * Ticker: id, symbol, company_id, ticker_history_id
          * TickerHistory: id, symbol, company_id, valid_from, valid_to
          * HistoricalEndOfDayPricing: ticker_history_id, date, open, high, low, close,
                                        adjusted_close, volume
        - OHLC relationships: high >= low, etc.
        - Ingestion completes without errors

        EODHD Pricing Data Source Fields:
        - ticker_history_id: Links to ticker_history record
        - date: Trading date
        - open: Opening price
        - high: Highest price during trading day
        - low: Lowest price during trading day
        - close: Closing price
        - adjusted_close: Close price adjusted for splits/dividends
        - volume: Number of shares traded
        """
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

            # === EXHAUSTIVE FIELD VALIDATION for one complete record ===
            # Get first company for detailed validation
            first_company = expected_companies[0]
            assert first_company.ticker is not None
            first_symbol = first_company.ticker.symbol

            # Validate Company fields (same as test_active_company_ingestion)
            company = assert_company_exists(session, first_company.company_name)
            assert company.id is not None
            assert isinstance(company.id, int)
            assert company.exchange == first_company.exchange
            assert company.source == "EODHD"
            assert company.active is True
            assert company.is_valid_data is True

            # Validate TickerHistory fields
            ticker_histories = get_ticker_histories_for_symbol(session, first_symbol)
            assert len(ticker_histories) > 0
            ticker_history = ticker_histories[0]
            assert ticker_history.id is not None
            assert isinstance(ticker_history.id, int)
            assert ticker_history.symbol == first_symbol
            assert ticker_history.company_id == company.id
            assert ticker_history.valid_from is not None
            assert ticker_history.valid_to is None

            # Validate HistoricalEndOfDayPricing fields
            from src.repos.equities.pricing.historical_eod_pricing_repository import (
                HistoricalEodPricingRepository,
            )

            pricing_repo = HistoricalEodPricingRepository()
            pricing_records = pricing_repo.get_pricing_by_ticker(ticker_history.id)
            assert len(pricing_records) > 0, "Should have pricing records"

            # Validate first pricing record
            pricing = pricing_records[0]
            assert pricing.ticker_history_id is not None
            assert pricing.ticker_history_id == ticker_history.id
            assert pricing.date is not None
            assert isinstance(pricing.date, date)
            assert pricing.open is not None
            assert isinstance(pricing.open, Decimal)
            assert pricing.high is not None
            assert isinstance(pricing.high, Decimal)
            assert pricing.low is not None
            assert isinstance(pricing.low, Decimal)
            assert pricing.close is not None
            assert isinstance(pricing.close, Decimal)
            assert pricing.adjusted_close is not None
            assert isinstance(pricing.adjusted_close, Decimal)
            assert pricing.volume is not None
            assert isinstance(pricing.volume, int)

            # Validate OHLC relationships
            assert pricing.high >= pricing.low, "High must be >= Low"
            assert pricing.high >= pricing.open, "High must be >= Open"
            assert pricing.high >= pricing.close, "High must be >= Close"
            assert pricing.low <= pricing.open, "Low must be <= Open"
            assert pricing.low <= pricing.close, "Low must be <= Close"

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
