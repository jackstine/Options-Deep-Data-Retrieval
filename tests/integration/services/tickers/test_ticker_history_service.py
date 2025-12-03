"""Integration tests for TickerHistoryService.

Tests the service layer operations for ticker history with company enrichment.
"""

from __future__ import annotations

from datetime import date

# IMPORTANT: Set environment variables BEFORE importing any src modules
from tests.integration.common_setup import setup_test_environment

setup_test_environment()

import pytest

from src.database.equities.enums import DataSourceEnum
from src.models.company import Company
from src.models.ticker_history import TickerHistory
from tests.integration.common_setup import integration_test_container
from tests.integration.services.tickers.mock_ticker_history_data_source import (
    MockTickerHistoryDataSource,
)


@pytest.mark.integration
class TestTickerHistoryService:
    """Integration tests for TickerHistoryService cross-repository operations."""

    def test_get_active_ticker_history_symbols_comprehensive(self):
        """Test get_active_ticker_history_symbols with various filtering scenarios.

        Validates:
        - Date filtering: only currently valid tickers returned
        - Active status filtering: only active company tickers returned
        - Combined filtering: both date and active status applied
        - Expired tickers excluded
        - Future tickers excluded
        - Inactive company tickers excluded
        """
        with integration_test_container() as (postgres, company_repo, port):
            from src.repos.equities.tickers.ticker_history_repository import (
                TickerHistoryRepository,
            )
            from src.services.tickers.ticker_history_service import TickerHistoryService

            mock_data = MockTickerHistoryDataSource()
            ticker_history_repo = TickerHistoryRepository()
            service = TickerHistoryService(ticker_history_repo, company_repo)

            # Test 1: Date filtering
            company_scenario, th_scenarios, expected_dates = mock_data.get_date_filtering_scenarios()

            company1 = Company(
                company_name=company_scenario.company_name,
                exchange=company_scenario.exchange,
                active=company_scenario.active,
                source=DataSourceEnum.EODHD,
            )
            inserted_company1 = company_repo.insert(company1)

            # Insert all ticker histories
            for th_scenario in th_scenarios:
                th = TickerHistory(
                    symbol=th_scenario.symbol,
                    company_id=inserted_company1.id,
                    valid_from=th_scenario.valid_from,
                    valid_to=th_scenario.valid_to,
                )
                ticker_history_repo.insert(th)

            # Test service method
            active_symbols_1 = service.get_active_ticker_history_symbols()

            # Assertions using expected values
            expected_active_count = len(expected_dates["active"])
            assert len(active_symbols_1) == expected_active_count
            for symbol in expected_dates["active"]:
                assert symbol in active_symbols_1
            for symbol in expected_dates["expired"]:
                assert symbol not in active_symbols_1
            for symbol in expected_dates["future"]:
                assert symbol not in active_symbols_1

            # Test 2: Active status filtering
            companies_scenarios, expected_active = mock_data.get_active_inactive_scenarios()

            # Create active and inactive companies with tickers
            symbols_by_status = {"active": [], "inactive": []}

            for i, company_scenario in enumerate(companies_scenarios):
                company = Company(
                    company_name=company_scenario.company_name,
                    exchange=company_scenario.exchange,
                    active=company_scenario.active,
                    source=DataSourceEnum.EODHD,
                )
                inserted_company = company_repo.insert(company)

                # Use expected symbol based on active status
                if company_scenario.active:
                    symbol = expected_active["active"][len(symbols_by_status["active"])]
                    symbols_by_status["active"].append(symbol)
                else:
                    symbol = expected_active["inactive"][len(symbols_by_status["inactive"])]
                    symbols_by_status["inactive"].append(symbol)

                th = TickerHistory(
                    symbol=symbol,
                    company_id=inserted_company.id,
                    valid_from=date(2020, 1, 1),
                )
                ticker_history_repo.insert(th)

            # Get active symbols (should include both date and active filtering)
            active_symbols_2 = service.get_active_ticker_history_symbols()

            # Assertions: Should include date-filtered symbols AND newly added active symbols
            # But exclude inactive company symbols
            total_expected_active = set(expected_dates["active"]) | set(expected_active["active"])
            assert len(active_symbols_2) == len(total_expected_active)
            for symbol in expected_active["active"]:
                assert symbol in active_symbols_2
            for symbol in expected_active["inactive"]:
                assert symbol not in active_symbols_2

    def test_happy_path(self):
        """Comprehensive test for get_active_ticker_histories with exhaustive field validation.

        Validates:
        - Company data properly enriched in ticker history results
        - All ticker histories for active company included
        - Inactive company ticker histories excluded
        - ALL fields are validated for at least one complete record:
          * Company: id, company_name, exchange, sector, industry, country, market_cap,
                     description, active, is_valid_data, source
          * TickerHistory: id, symbol, company_id, valid_from, valid_to
        - Service properly joins TickerHistory and Company data
        - Multiple ticker histories for same company (symbol changes)
        """
        with integration_test_container() as (postgres, company_repo, port):
            from src.repos.equities.tickers.ticker_history_repository import (
                TickerHistoryRepository,
            )
            from src.services.tickers.ticker_history_service import TickerHistoryService

            mock_data = MockTickerHistoryDataSource()
            ticker_history_repo = TickerHistoryRepository()
            service = TickerHistoryService(ticker_history_repo, company_repo)

            # Get enrichment scenario with rich company data
            enrichment_scenario = mock_data.get_enrichment_scenario()

            company = Company(
                company_name=enrichment_scenario.company_name,
                exchange=enrichment_scenario.exchange,
                sector=enrichment_scenario.sector,
                industry=enrichment_scenario.industry,
                country=enrichment_scenario.country,
                active=enrichment_scenario.active,
                source=DataSourceEnum.EODHD,
            )
            inserted_company = company_repo.insert(company)

            # Create two ticker histories for the same company
            ticker_histories_data = [
                {"symbol": "TECH", "valid_from": date(2000, 1, 1), "valid_to": None},
                {
                    "symbol": "TECH-OLD",
                    "valid_from": date(1990, 1, 1),
                    "valid_to": date(1999, 12, 31),
                },
            ]

            for th_data in ticker_histories_data:
                th = TickerHistory(
                    symbol=th_data["symbol"],
                    company_id=inserted_company.id,
                    valid_from=th_data["valid_from"],
                    valid_to=th_data["valid_to"],
                )
                ticker_history_repo.insert(th)

            # Test service method
            enriched_histories = service.get_active_ticker_histories()

            # Assertions using expected values from mock
            assert len(enriched_histories) == len(ticker_histories_data)

            # Verify enrichment for each ticker history
            for enriched in enriched_histories:
                assert enriched.company.company_name == enrichment_scenario.company_name
                assert enriched.company.exchange == enrichment_scenario.exchange
                assert enriched.company.sector == enrichment_scenario.sector
                assert enriched.company.industry == enrichment_scenario.industry
                assert enriched.company.country == enrichment_scenario.country
                assert enriched.company.active == enrichment_scenario.active

                # Verify ticker history data
                th_data = next(
                    t for t in ticker_histories_data if t["symbol"] == enriched.ticker_history.symbol
                )
                assert enriched.ticker_history.symbol == th_data["symbol"]
                assert enriched.ticker_history.valid_from == th_data["valid_from"]
                assert enriched.ticker_history.valid_to == th_data["valid_to"]

            # === EXHAUSTIVE FIELD VALIDATION for Company ===
            # Use first enriched result for validation
            first_enriched = enriched_histories[0]
            company = first_enriched.company
            assert company.id is not None, "Company id should be set"
            assert isinstance(company.id, int), "Company id should be an integer"
            assert company.company_name == enrichment_scenario.company_name, "Company name should match"
            assert company.exchange == enrichment_scenario.exchange, "Exchange should match"
            assert company.sector == enrichment_scenario.sector, "Sector should match"
            assert company.industry == enrichment_scenario.industry, "Industry should match"
            assert company.country == enrichment_scenario.country, "Country should match"
            # market_cap, description may be None for test data
            assert company.active == enrichment_scenario.active, "Active flag should match"
            assert company.is_valid_data is True, "is_valid_data should be True for valid records"
            assert company.source == DataSourceEnum.EODHD, "Source should match"

            # === EXHAUSTIVE FIELD VALIDATION for TickerHistory ===
            ticker_history = first_enriched.ticker_history
            assert ticker_history.id is not None, "TickerHistory id should be set"
            assert isinstance(ticker_history.id, int), "TickerHistory id should be an integer"
            assert ticker_history.symbol is not None, "Symbol should be set"
            assert isinstance(ticker_history.symbol, str), "Symbol should be a string"
            assert ticker_history.company_id == company.id, "company_id should reference correct company"
            assert ticker_history.valid_from is not None, "valid_from should be set"
            assert isinstance(ticker_history.valid_from, date), "valid_from should be a date"
            # valid_to may be None for currently active tickers
            if ticker_history.valid_to is not None:
                assert isinstance(ticker_history.valid_to, date), "valid_to should be a date"

            # Verify both active and delisted ticker histories are present
            symbols_found = {enriched.ticker_history.symbol for enriched in enriched_histories}
            assert "TECH" in symbols_found, "Current symbol should be present"
            assert "TECH-OLD" in symbols_found, "Old symbol should be present"

    def test_get_active_ticker_histories_multi_company(self):
        """Test ticker histories for multiple active companies.

        Validates:
        - All active companies represented in results
        - Correct count of total ticker histories
        - Company names and symbols match expected from mock
        - Inactive companies excluded
        """
        with integration_test_container() as (postgres, company_repo, port):
            from src.repos.equities.tickers.ticker_history_repository import (
                TickerHistoryRepository,
            )
            from src.services.tickers.ticker_history_service import TickerHistoryService

            mock_data = MockTickerHistoryDataSource()
            ticker_history_repo = TickerHistoryRepository()
            service = TickerHistoryService(ticker_history_repo, company_repo)

            # Get active/inactive scenarios
            companies_scenarios, expected_active = mock_data.get_active_inactive_scenarios()

            # Create companies and ticker histories
            expected_company_names = []
            expected_symbols = []

            for i, company_scenario in enumerate(companies_scenarios):
                company = Company(
                    company_name=company_scenario.company_name,
                    exchange=company_scenario.exchange,
                    active=company_scenario.active,
                    source=DataSourceEnum.EODHD,
                )
                inserted_company = company_repo.insert(company)

                # Track expected values for active companies only
                if company_scenario.active:
                    expected_company_names.append(company_scenario.company_name)
                    symbol = expected_active["active"][len(expected_symbols)]
                    expected_symbols.append(symbol)
                else:
                    symbol = expected_active["inactive"][0]

                th = TickerHistory(
                    symbol=symbol,
                    company_id=inserted_company.id,
                    valid_from=date(2020, 1, 1),
                )
                ticker_history_repo.insert(th)

            # Test service method
            enriched_histories = service.get_active_ticker_histories()

            # Assertions using expected values
            expected_count = len(expected_company_names)
            assert len(enriched_histories) == expected_count

            # Verify all expected companies and symbols present
            result_company_names = {h.company.company_name for h in enriched_histories}
            result_symbols = {h.ticker_history.symbol for h in enriched_histories}

            assert result_company_names == set(expected_company_names)
            assert result_symbols == set(expected_symbols)

    def test_empty_result_scenarios(self):
        """Test that empty results are returned when no data exists.

        Validates:
        - Empty list for get_active_ticker_histories
        - Empty set for get_active_ticker_history_symbols
        """
        with integration_test_container() as (postgres, company_repo, port):
            from src.repos.equities.tickers.ticker_history_repository import (
                TickerHistoryRepository,
            )
            from src.services.tickers.ticker_history_service import TickerHistoryService

            ticker_history_repo = TickerHistoryRepository()
            service = TickerHistoryService(ticker_history_repo, company_repo)

            # Test with empty database
            enriched_histories = service.get_active_ticker_histories()
            active_symbols = service.get_active_ticker_history_symbols()

            # Assertions
            assert enriched_histories == []
            assert len(enriched_histories) == 0
            assert active_symbols == set()
            assert len(active_symbols) == 0
