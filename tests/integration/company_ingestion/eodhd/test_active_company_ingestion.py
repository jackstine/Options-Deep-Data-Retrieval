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

    def test_initial_ingestion_creates_companies_with_valid_data(self):
        """Comprehensive test for initial EODHD active company ingestion.

        Validates:
        - Database starts empty
        - All active symbols from fixture are ingested
        - Companies have correct source (EODHD) and exchange
        - All active symbols are marked as active
        - Tickers are created for all companies
        - Ticker histories are created and currently valid (no end date)
        - Specific fixture companies exist with correct data
        - Ingestion completes without errors
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

            # Verify Agilent Technologies Inc has correct source and exchange
            agilent = assert_company_exists(
                session,
                "Agilent Technologies Inc",
                expected_fields={"exchange": "NYSE"},
            )
            assert agilent is not None
            assert agilent.source == "EODHD"

            # Verify Alcoa Corp exists
            alcoa = assert_company_exists(
                session,
                "Alcoa Corp",
                expected_fields={"exchange": "NYSE"},
            )
            assert alcoa is not None

            # Verify ticker history for Agilent is currently valid
            ticker_histories = get_ticker_histories_for_symbol(session, "A")
            assert len(ticker_histories) > 0

            ticker_history = ticker_histories[0]
            assert ticker_history.valid_to is None  # No end date for active symbols
            assert ticker_history.company_id == agilent.id
            assert ticker_history.is_currently_valid()
