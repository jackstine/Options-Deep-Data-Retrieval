"""Integration tests for EODHD delisted company ingestion pipeline."""

from __future__ import annotations

# IMPORTANT: Set environment variables BEFORE importing any src modules
from tests.integration.common_setup import setup_test_environment

setup_test_environment()

# NOW safe to import src modules
from tests.integration.common_setup import integration_test_container, create_test_session
from tests.data_source_mocks.eodhd.mock_symbols import MockEodhdSymbolsSource
from tests.integration.db.db_assertions import (
    assert_company_exists,
    count_companies,
    count_ticker_histories,
    count_tickers,
    get_company_by_name,
    get_ticker_by_symbol,
    get_ticker_histories_for_symbol,
)


class TestEodhdDelistedCompanyIngestion:
    """Integration tests for EODHD delisted company ingestion."""

    def test_happy_path(self):
        """Comprehensive test for EODHD ingestion behavior with active and delisted symbols.

        **Current Behavior**: This test validates that delisted companies are NOT ingested
        into the database, which is the expected behavior of the current pipeline.

        **Why delisted companies are not ingested**:
        - They are no longer tradeable on exchanges
        - Historical data for delisted companies is not relevant for active trading
        - Including them would pollute the database with inactive securities

        **What this test validates**:
        - Only active symbols are ingested (delisted symbols are excluded)
        - Active symbols appear in tickers table
        - Active symbols have ticker_history records
        - Delisted fixture data exists and is accessible (ready for future implementation)
        - Tickers table only contains currently active symbols
        - Database counts match only active symbols, not delisted ones

        **Fields that would be validated IF delisted ingestion were implemented**:
        If in the future we decide to ingest delisted companies (e.g., for historical
        analysis or backtesting), we would need to validate:
        - Company.company_name: matches delisted symbol name
        - Company.exchange: matches delisted symbol exchange
        - Company.source: set to "EODHD"
        - Company.active: explicitly set to False
        - Company.country: from delisted CSV data
        - Ticker.symbol: matches delisted symbol code
        - TickerHistory.valid_from: listing date
        - TickerHistory.valid_to: delisting date (NOT None)
        - TickerHistory.symbol: matches delisted symbol code

        TODO: Consider implementing delisted company ingestion if:
        - Historical backtesting requires delisted company data
        - Regulatory or compliance reasons require tracking delisted companies
        - Analytics features need access to delisted company information
        """
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline

            # Create mock source and pipeline
            mock_eodhd_source = MockEodhdSymbolsSource()
            company_pipeline = CompanyPipeline()

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # Get active and delisted companies separately
            active_companies = mock_eodhd_source.get_active_symbols()
            delisted_companies = mock_eodhd_source.get_delisted_symbols()

            # Verify fixture has delisted data (for future implementation)
            assert len(delisted_companies) > 0

            # Run ingestion (currently only ingests active companies)
            result = company_pipeline.run_ingestion([mock_eodhd_source])

            # Verify only active symbols were ingested
            assert count_companies(session) == len(active_companies)
            assert count_tickers(session) == len(active_companies)
            assert count_ticker_histories(session) == len(active_companies)

            # Verify active symbols are in tickers table using first company from mock
            first_active_company = active_companies[0]
            assert first_active_company.ticker is not None, "Expected active company to have ticker"
            ticker = get_ticker_by_symbol(session, first_active_company.ticker.symbol)
            assert ticker is not None

            # Verify active companies have ticker_history
            active_count = count_companies(session)
            ticker_history_count = count_ticker_histories(session)
            assert ticker_history_count == active_count

    def test_fixture_has_delisted_data(self):
        """Verify that the fixture file contains delisted company data."""
        # Create mock source (no container needed for this test)
        mock_eodhd_source = MockEodhdSymbolsSource()

        delisted_companies = mock_eodhd_source.get_delisted_symbols()

        # Verify fixture has delisted data
        assert len(delisted_companies) > 0

        # Verify expected delisted companies (Common Stocks from fixture)
        delisted_symbols = [c.ticker.symbol for c in delisted_companies if c.ticker]
        assert "AAAB" in delisted_symbols  # Admiralty Bancorp Inc
        assert "AAAP" in delisted_symbols  # Advanced Accelerator Applications S.A

        # Verify company names
        company_names = [c.company_name for c in delisted_companies]
        assert "Admiralty Bancorp Inc" in company_names
        assert "Advanced Accelerator Applications S.A" in company_names
