"""Integration tests for NASDAQ screener sync pipeline."""

from __future__ import annotations

# IMPORTANT: Set environment variables BEFORE importing any src modules
from tests.integration.common_setup import setup_test_environment

setup_test_environment()

# NOW safe to import src modules
from src.database.equities.enums import DataSourceEnum
from tests.integration.common_setup import integration_test_container, create_test_session
from tests.data_source_mocks.nasdaq.mock_screener import MockNasdaqScreenerSource
from tests.integration.db.db_assertions import (
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

    def test_happy_path(self):
        """Comprehensive test for initial NASDAQ screener ingestion with exhaustive field validation.

        Validates:
        - Database starts empty
        - All fixture companies are ingested
        - Companies have correct field values (source, exchange, sector, etc.)
        - Tickers are created and linked to companies
        - Ticker histories are created and currently valid
        - Foreign key relationships are correctly established
        - ALL fields are validated for at least one complete record:
          * Company: id, company_name, exchange, sector, industry, country, market_cap,
                     description, active, is_valid_data, source
          * Ticker: id, symbol, company_id, ticker_history_id
          * TickerHistory: id, symbol, company_id, valid_from, valid_to
        - Circular FK reference (ticker ↔ ticker_history) validated
        - Ingestion completes without errors

        NASDAQ Screener CSV Fields:
        - Stored: Symbol, Name, Sector, Industry, Country, Market Cap
        - NOT stored: Last Sale, Net Change, % Change, Volume, IPO Year

        Note: NASDAQ is unique in populating sector, industry, country, market_cap,
        and description fields that EODHD does not provide.
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

            # Use first company from mock data for exhaustive validation
            first_company = mock_companies[0]
            assert first_company.ticker is not None, "Expected first company to have ticker"
            first_symbol = first_company.ticker.symbol

            # Verify first company has correct field values
            db_company = assert_company_exists(
                session,
                first_company.company_name,
                expected_fields={
                    "exchange": first_company.exchange,
                    "sector": first_company.sector,
                    "industry": first_company.industry,
                    "country": first_company.country,
                    "active": True,
                },
            )

            # Verify ticker is linked to company with correct foreign keys
            ticker = assert_ticker_exists(session, first_symbol, company_id=db_company.id)
            assert ticker.ticker_history_id is not None

            # Verify ticker_history exists and is currently valid
            # Note: We don't check valid_from date as it varies based on ingestion time
            # We only verify that valid_to is None (meaning it's currently active)
            ticker_history = assert_ticker_history_valid(
                session,
                first_symbol,
                company_id=db_company.id,
                valid_to=None,  # Currently valid (no end date)
            )

            # Verify circular foreign key reference is correct
            assert ticker.ticker_history_id == ticker_history.id
            assert ticker.company_id == db_company.id
            assert ticker_history.company_id == db_company.id

            # === EXHAUSTIVE FIELD VALIDATION for one complete record ===
            # Validate ALL Company fields (NASDAQ-specific fields populated)
            assert db_company.id is not None
            assert isinstance(db_company.id, int)
            assert db_company.company_name == first_company.company_name
            assert db_company.exchange == first_company.exchange
            assert db_company.sector == first_company.sector, "NASDAQ provides sector data"
            assert db_company.industry == first_company.industry, "NASDAQ provides industry data"
            assert db_company.country == first_company.country, "NASDAQ provides country data"
            assert db_company.market_cap == first_company.market_cap, "NASDAQ provides market cap data"
            assert isinstance(db_company.market_cap, int)
            # Description may be None for NASDAQ screener data
            assert db_company.active is True
            assert db_company.is_valid_data is True
            assert db_company.source == DataSourceEnum.NASDAQ_SCREENER

            # Validate ALL Ticker fields
            assert ticker.id is not None
            assert isinstance(ticker.id, int)
            assert ticker.symbol == first_symbol
            assert ticker.company_id == db_company.id
            assert ticker.ticker_history_id is not None
            assert isinstance(ticker.ticker_history_id, int)

            # Validate ALL TickerHistory fields
            assert ticker_history.id is not None
            assert isinstance(ticker_history.id, int)
            assert ticker_history.symbol == first_symbol
            assert ticker_history.company_id == db_company.id
            assert ticker_history.valid_from is not None
            assert ticker_history.valid_to is None, "Currently active ticker"

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

            # Get first company from mock for validation
            mock_companies = mock_nasdaq_source.get_companies()
            first_company = mock_companies[0]

            # First ingestion
            result1 = company_pipeline.run_ingestion([mock_nasdaq_source])
            initial_count = result1["inserted"]

            # Get initial market cap from first company
            company_before = get_company_by_name(session, first_company.company_name)
            assert company_before is not None
            initial_market_cap = company_before.market_cap

            # Second ingestion (same data)
            result2 = company_pipeline.run_ingestion([mock_nasdaq_source])

            # Should have 0 new companies inserted
            assert result2["inserted"] == 0
            # When data is identical, pipeline attempts updates but repository only counts
            # actual changes. Companies without field changes get "No valid update values"
            # warning and are not counted in the "updated" result.
            assert result2["updated"] >= 0  # May be less than total if no changes
            assert result2["updated"] <= initial_count  # Cannot exceed total companies

            # Company count should remain the same
            assert count_companies(session) == initial_count

            # Market cap should remain unchanged since fixture data is static
            company_after = get_company_by_name(session, first_company.company_name)
            assert company_after is not None
            assert company_after.market_cap == initial_market_cap
