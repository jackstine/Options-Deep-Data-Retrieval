"""Integration tests for EODHD active company ingestion pipeline."""

from __future__ import annotations

# IMPORTANT: Set environment variables BEFORE importing any src modules
from tests.integration.common_setup import setup_test_environment

setup_test_environment()

# NOW safe to import src modules
from tests.integration.common_setup import integration_test_container, create_test_session
from tests.data_source_mocks.eodhd.mock_symbols import MockEodhdSymbolsSource
from tests.utils.db_assertions import (
    assert_company_exists,
    assert_ticker_exists,
    assert_ticker_history_valid,
    count_companies,
    count_ticker_histories,
    count_tickers,
    get_company_by_name,
    get_ticker_histories_for_symbol,
)


class TestEodhdActiveCompanyIngestion:
    """Integration tests for EODHD active company ingestion."""

    def test_happy_path(self):
        """Comprehensive test for initial EODHD active company ingestion with exhaustive field validation.

        Validates:
        - Database starts empty
        - All active symbols from fixture are ingested
        - Companies have correct source (EODHD) and exchange
        - All active symbols are marked as active
        - Tickers are created for all companies
        - Ticker histories are created and currently valid (no end date)
        - Specific fixture companies exist with correct data
        - ALL fields are validated for at least one complete record:
          * Company: id, company_name, exchange, sector, industry, country, market_cap,
                     description, active, is_valid_data, source
          * Ticker: id, symbol, company_id, ticker_history_id
          * TickerHistory: id, symbol, company_id, valid_from, valid_to
        - Foreign key relationships are validated
        - Ingestion completes without errors

        Note: The following EODHD CSV fields are intentionally NOT stored in the database:
        - Currency: Not required for current data model
        - Type: Filtered to "Common Stock" only, not stored
        - Isin: Not required for current data model
        """
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline

            # Create mock source and pipeline
            mock_eodhd_source = MockEodhdSymbolsSource()
            company_pipeline = CompanyPipeline()

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # Get active symbols from mock source
            active_companies = mock_eodhd_source.get_active_symbols()
            expected_count = len(active_companies)

            # Verify database starts empty
            assert count_companies(session) == 0
            assert count_tickers(session) == 0
            assert count_ticker_histories(session) == 0

            # Run ingestion
            result = company_pipeline.run_ingestion([mock_eodhd_source])

            # Verify ingestion results
            assert result["inserted"] == expected_count
            assert result["errors"] == 0

            # Verify database state matches ingestion results
            assert count_companies(session) == expected_count
            assert count_tickers(session) == expected_count
            assert count_ticker_histories(session) == expected_count

            # Verify all active symbols are marked as active
            active_count = count_companies(session, active_only=True)
            total_count = count_companies(session, active_only=False)
            assert active_count == total_count  # All should be active

            # Verify each fixture company was ingested with tickers
            for company in active_companies:
                assert_company_exists(session, company.company_name)
                if company.ticker:
                    ticker = assert_ticker_exists(session, company.ticker.symbol)
                    assert ticker is not None

            # Use first company from mock data for exhaustive validation
            first_company = active_companies[0]
            assert first_company.ticker is not None, "Expected first company to have ticker"
            first_symbol = first_company.ticker.symbol

            # Verify first company has correct source and exchange
            db_company = assert_company_exists(
                session,
                first_company.company_name,
                expected_fields={"exchange": first_company.exchange},
            )
            assert db_company is not None
            assert db_company.source == "EODHD"

            # Verify ticker history is currently valid
            ticker_histories = get_ticker_histories_for_symbol(session, first_symbol)
            assert len(ticker_histories) > 0

            ticker_history = ticker_histories[0]
            assert ticker_history.valid_to is None  # No end date for active symbols
            assert ticker_history.company_id == db_company.id
            assert ticker_history.is_currently_valid()

            # === EXHAUSTIVE FIELD VALIDATION for one complete record ===
            # Validate ALL Company fields
            assert db_company.id is not None, "Company id should be set"
            assert isinstance(db_company.id, int), "Company id should be an integer"
            assert db_company.company_name == first_company.company_name, "Company name should match"
            assert db_company.exchange == first_company.exchange, "Exchange should match"
            assert db_company.sector is None, "EODHD does not provide sector data"
            assert db_company.industry is None, "EODHD does not provide industry data"
            assert db_company.country == first_company.country, "Country should match mock data"
            assert db_company.market_cap is None, "Market cap not provided in initial ingestion"
            assert db_company.description is None, "Description not provided in initial ingestion"
            assert db_company.active is True, "Active companies should have active=True"
            assert db_company.is_valid_data is True, "Valid data from source should be marked as such"
            assert db_company.source == "EODHD", "Source should be EODHD"

            # Validate ALL Ticker fields
            db_ticker = assert_ticker_exists(session, first_symbol)
            assert db_ticker is not None, "Ticker should exist"
            assert db_ticker.id is not None, "Ticker id should be set"
            assert isinstance(db_ticker.id, int), "Ticker id should be an integer"
            assert db_ticker.symbol == first_symbol, "Ticker symbol should match"
            assert db_ticker.company_id == db_company.id, "Ticker company_id should reference correct company"
            assert db_ticker.ticker_history_id is not None, "Ticker should reference ticker_history"
            assert isinstance(db_ticker.ticker_history_id, int), "ticker_history_id should be an integer"

            # Validate ALL TickerHistory fields
            assert ticker_history.id is not None, "TickerHistory id should be set"
            assert isinstance(ticker_history.id, int), "TickerHistory id should be an integer"
            assert ticker_history.symbol == first_symbol, "TickerHistory symbol should match"
            assert ticker_history.company_id == db_company.id, "TickerHistory company_id should reference correct company"
            assert ticker_history.valid_from is not None, "TickerHistory valid_from should be set"
            assert ticker_history.valid_to is None, "Active ticker should have valid_to=None"

            # Validate Foreign Key relationships
            assert db_ticker.company_id == db_company.id, "Ticker.company_id should match Company.id"
            assert db_ticker.ticker_history_id == ticker_history.id, "Ticker.ticker_history_id should match TickerHistory.id"
            assert ticker_history.company_id == db_company.id, "TickerHistory.company_id should match Company.id"
