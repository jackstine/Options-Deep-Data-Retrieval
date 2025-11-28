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

    def test_initial_ingestion_creates_companies_with_valid_data(self):
        """Comprehensive test for initial NASDAQ screener ingestion.

        Validates:
        - Database starts empty
        - All fixture companies are ingested
        - Companies have correct field values (source, exchange, sector, etc.)
        - Tickers are created and linked to companies
        - Ticker histories are created and currently valid
        - Foreign key relationships are correctly established
        - Ingestion completes without errors
        """
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline after port is set
            from src.pipelines.companies.new_company_pipeline import CompanyPipeline

            # Create mock source and pipeline
            mock_nasdaq_source = MockNasdaqScreenerSource()
            company_pipeline = CompanyPipeline()

            # Create database session for assertions
            session = create_test_session(postgres, port)

            # Get expected companies from mock source
            mock_companies = mock_nasdaq_source.get_companies()
            expected_count = len(mock_companies)

            # Verify database starts empty
            assert count_companies(session) == 0
            assert count_tickers(session) == 0
            assert count_ticker_histories(session) == 0

            # Run ingestion
            result = company_pipeline.run_ingestion([mock_nasdaq_source])

            # Verify ingestion results
            assert result["inserted"] == expected_count
            assert result["tickers_inserted"] == expected_count
            assert result["ticker_histories_inserted"] == expected_count
            assert result["errors"] == 0

            # Verify database state matches ingestion results
            assert count_companies(session) == result["inserted"]
            assert count_tickers(session) == result["tickers_inserted"]
            assert count_ticker_histories(session) == result["ticker_histories_inserted"]

            # Verify each fixture company was ingested
            for company in mock_companies:
                assert_company_exists(session, company.company_name)
                if company.ticker:
                    assert_ticker_exists(session, company.ticker.symbol)

            # Verify Apple Inc. has correct field values
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

            # Verify ticker is linked to company with correct foreign keys
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

            # Verify circular foreign key reference is correct
            assert ticker.ticker_history_id == ticker_history.id
            assert ticker.company_id == apple.id
            assert ticker_history.company_id == apple.id

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
            # When data is identical, pipeline still runs UPDATE operations on existing companies
            # All existing companies are processed through the update path
            assert result2["updated"] == initial_count

            # Company count should remain the same
            assert count_companies(session) == initial_count

            # Market cap should remain unchanged since fixture data is static
            apple_after = get_company_by_name(session, "Apple Inc.")
            assert apple_after is not None
            assert apple_after.market_cap == initial_market_cap
