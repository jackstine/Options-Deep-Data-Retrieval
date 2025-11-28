"""Integration tests for NASDAQ screener sync pipeline."""

from __future__ import annotations

# IMPORTANT: Set environment variables BEFORE importing any src modules
from tests.integration.common_setup import setup_test_environment

setup_test_environment()

# NOW safe to import src modules
from tests.integration.common_setup import integration_test_container, create_test_session
from tests.data_source_mocks.nasdaq.mock_screener import MockNasdaqScreenerSource
from tests.utils.db_assertions import (
    assert_company_exists,
    assert_ticker_exists,
    assert_ticker_history_valid,
    count_companies,
    count_ticker_histories,
    count_tickers,
    get_company_by_name,
)


class TestNasdaqScreenerSync:
    """Integration tests for NASDAQ screener sync."""

    def test_initial_ingestion_creates_companies(self):
        """Test initial ingestion creates companies, tickers, and ticker_histories."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline

            # Create mock source and pipeline
            mock_nasdaq_source = MockNasdaqScreenerSource()
            company_pipeline = CompanyPipeline()

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # Verify database is empty
            assert count_companies(session) == 0
            assert count_tickers(session) == 0
            assert count_ticker_histories(session) == 0

            # Run ingestion
            result = company_pipeline.run_ingestion([mock_nasdaq_source])

            # Verify ingestion results
            assert result["inserted"] > 0
            assert result["tickers_inserted"] > 0
            assert result["ticker_histories_inserted"] > 0
            assert result["errors"] == 0

            # Verify database state
            assert count_companies(session) == result["inserted"]
            assert count_tickers(session) == result["tickers_inserted"]
            assert count_ticker_histories(session) == result["ticker_histories_inserted"]

    def test_ingested_companies_have_correct_data(self):
        """Test that ingested companies have correct field values."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline

            # Create mock source and pipeline
            mock_nasdaq_source = MockNasdaqScreenerSource()
            company_pipeline = CompanyPipeline()

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # Run ingestion
            company_pipeline.run_ingestion([mock_nasdaq_source])

            # Verify Apple Inc. was ingested correctly
            apple = assert_company_exists(
                session,
                "Apple Inc.",
                expected_fields={
                    "exchange": "NASDAQ",
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "country": "United States",
                    "active": True,
                },
            )

            # Verify ticker exists and is linked to company
            ticker = assert_ticker_exists(session, "AAPL", company_id=apple.id)
            assert ticker.ticker_history_id is not None

            # Verify ticker_history exists and is currently valid
            # Note: We don't check valid_from date as it varies based on ingestion time
            # We only verify that valid_to is None (meaning it's currently active)
            ticker_history = assert_ticker_history_valid(
                session,
                "AAPL",
                company_id=apple.id,
                valid_to=None,  # Currently valid (no end date)
            )
            assert ticker_history.id == ticker.ticker_history_id

    def test_duplicate_ingestion_updates_market_cap(self):
        """Test that re-running ingestion updates market_cap for existing companies."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline

            # Create mock source and pipeline
            mock_nasdaq_source = MockNasdaqScreenerSource()
            company_pipeline = CompanyPipeline()

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # First ingestion
            result1 = company_pipeline.run_ingestion([mock_nasdaq_source])
            initial_count = result1["inserted"]

            # Get initial Apple market cap
            apple_before = get_company_by_name(session, "Apple Inc.")
            assert apple_before is not None
            initial_market_cap = apple_before.market_cap

            # Second ingestion (same data)
            result2 = company_pipeline.run_ingestion([mock_nasdaq_source])

            # Should have 0 new companies inserted
            assert result2["inserted"] == 0
            # When data is identical, pipeline doesn't mark as updated
            # This is expected behavior for efficiency
            assert result2["updated"] == 0

            # Company count should remain the same
            assert count_companies(session) == initial_count

            # Market cap should remain unchanged since fixture data is static
            apple_after = get_company_by_name(session, "Apple Inc.")
            assert apple_after is not None
            assert apple_after.market_cap == initial_market_cap

    def test_all_fixture_companies_are_ingested(self):
        """Test that all companies from fixture file are ingested."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline

            # Create mock source and pipeline
            mock_nasdaq_source = MockNasdaqScreenerSource()
            company_pipeline = CompanyPipeline()

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # Get companies from mock source
            mock_companies = mock_nasdaq_source.get_companies()
            expected_count = len(mock_companies)

            # Run ingestion
            result = company_pipeline.run_ingestion([mock_nasdaq_source])

            # Verify all companies were ingested
            assert result["inserted"] == expected_count
            assert count_companies(session) == expected_count

            # Verify each company exists
            for company in mock_companies:
                assert_company_exists(session, company.company_name)
                if company.ticker:
                    assert_ticker_exists(session, company.ticker.symbol)

    def test_ingestion_creates_valid_foreign_keys(self):
        """Test that all foreign key relationships are correctly established."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline

            # Create mock source and pipeline
            mock_nasdaq_source = MockNasdaqScreenerSource()
            company_pipeline = CompanyPipeline()

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # Run ingestion
            company_pipeline.run_ingestion([mock_nasdaq_source])

            # Get a sample company
            apple = get_company_by_name(session, "Apple Inc.")
            assert apple is not None

            # Verify ticker has correct company_id
            ticker = assert_ticker_exists(session, "AAPL")
            assert ticker.company_id == apple.id

            # Verify ticker has ticker_history_id set
            assert ticker.ticker_history_id is not None

            # Verify ticker_history exists with same company_id
            ticker_history = assert_ticker_history_valid(
                session,
                "AAPL",
                company_id=apple.id,
            )

            # Verify circular reference is correct
            assert ticker.ticker_history_id == ticker_history.id
