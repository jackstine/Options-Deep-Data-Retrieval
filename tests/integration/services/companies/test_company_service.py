"""Integration tests for CompanyService.

Tests the service layer operations that join companies with ticker_history.
"""

from __future__ import annotations

from datetime import date

# IMPORTANT: Set environment variables BEFORE importing any src modules
from tests.integration.common_setup import setup_test_environment

setup_test_environment()

import pytest

from src.database.equities.enums import DataSourceEnum
from src.models.company import Company
from src.models.ticker import Ticker
from src.models.ticker_history import TickerHistory
from tests.integration.common_setup import integration_test_container
from tests.integration.services.companies.company_scenarios import CompanyTestScenario
from tests.integration.services.companies.mock_company_data_source import (
    MockCompanyDataSource,
)


@pytest.mark.integration
class TestCompanyService:
    """Integration tests for CompanyService cross-repository operations."""

    def test_get_active_company_symbols_comprehensive(self):
        """Test get_active_company_symbols with active/inactive companies.

        Validates:
        - Only active company symbols are returned
        - Inactive company symbols are excluded
        - Correct count of active symbols
        - Symbol values match expected from mock data
        """
        with integration_test_container() as (postgres, company_repo, port):
            from src.repos.equities.tickers.ticker_history_repository import (
                TickerHistoryRepository,
            )
            from src.repos.equities.tickers.ticker_repository import TickerRepository
            from src.services.companies.company_service import CompanyService

            mock_data = MockCompanyDataSource()
            ticker_history_repo = TickerHistoryRepository()
            ticker_repo = TickerRepository()
            service = CompanyService(company_repo, ticker_history_repo)

            # Seed data from mock source
            active_scenarios = mock_data.get_all_active()
            inactive_scenarios = mock_data.get_all_inactive()
            all_scenarios = active_scenarios + inactive_scenarios

            inserted_companies = {}
            for scenario in all_scenarios:
                company = Company(
                    company_name=scenario.company_name,
                    exchange=scenario.exchange,
                    active=scenario.active,
                    source=DataSourceEnum.EODHD,
                )
                inserted = company_repo.insert(company)
                inserted_companies[scenario.symbol] = inserted

                # Create ticker history and ticker
                th = TickerHistory(
                    symbol=scenario.symbol,
                    company_id=inserted.id,
                    valid_from=date(2020, 1, 1),
                )
                th_inserted = ticker_history_repo.insert(th)

                ticker = Ticker(
                    symbol=scenario.symbol,
                    company_id=inserted.id,
                    ticker_history_id=th_inserted.id,
                )
                ticker_repo.insert(ticker)

            # Test service method
            active_symbols = service.get_active_company_symbols()

            # Assertions using mock data
            expected_active_count = len(active_scenarios)
            expected_active_symbols = {s.symbol for s in active_scenarios}
            expected_inactive_symbols = {s.symbol for s in inactive_scenarios}

            assert len(active_symbols) == expected_active_count
            assert active_symbols == expected_active_symbols
            assert active_symbols.isdisjoint(expected_inactive_symbols)

    def test_get_company_by_ticker_comprehensive(self):
        """Test getting company by ticker with various scenarios.

        Validates:
        - Finding active company by ticker
        - Finding delisted company by ticker
        - Case-insensitive ticker lookup
        - Correct company data returned
        - Returns None for non-existent ticker
        """
        with integration_test_container() as (postgres, company_repo, port):
            from src.repos.equities.tickers.ticker_history_repository import (
                TickerHistoryRepository,
            )
            from src.services.companies.company_service import CompanyService

            mock_data = MockCompanyDataSource()
            ticker_history_repo = TickerHistoryRepository()
            service = CompanyService(company_repo, ticker_history_repo)

            # Seed active and delisted companies
            active_scenario = mock_data.get_active_scenario()
            delisted_scenario = CompanyTestScenario(
                company_name="Delisted Corporation",
                exchange="NYSE",
                active=False,
                symbol="DLIST",
            )

            # Insert active company
            active_company = Company(
                company_name=active_scenario.company_name,
                exchange=active_scenario.exchange,
                sector=active_scenario.sector,
                industry=active_scenario.industry,
                active=active_scenario.active,
                source=DataSourceEnum.EODHD,
            )
            inserted_active = company_repo.insert(active_company)

            active_th = TickerHistory(
                symbol=active_scenario.symbol,
                company_id=inserted_active.id,
                valid_from=date(2000, 1, 1),
            )
            ticker_history_repo.insert(active_th)

            # Insert delisted company
            delisted_company = Company(
                company_name=delisted_scenario.company_name,
                exchange=delisted_scenario.exchange,
                active=delisted_scenario.active,
                source=DataSourceEnum.EODHD,
            )
            inserted_delisted = company_repo.insert(delisted_company)

            delisted_th = TickerHistory(
                symbol=delisted_scenario.symbol,
                company_id=inserted_delisted.id,
                valid_from=date(2015, 1, 1),
                valid_to=date(2020, 12, 31),
            )
            ticker_history_repo.insert(delisted_th)

            # Test 1: Find active company by ticker
            result_active = service.get_company_by_ticker(active_scenario.symbol)
            assert result_active is not None
            assert result_active.company.company_name == active_scenario.company_name
            assert result_active.company.exchange == active_scenario.exchange
            assert result_active.company.sector == active_scenario.sector
            assert result_active.ticker_history.symbol == active_scenario.symbol

            # Test 2: Find delisted company by ticker
            result_delisted = service.get_company_by_ticker(delisted_scenario.symbol)
            assert result_delisted is not None
            assert result_delisted.company.company_name == delisted_scenario.company_name
            assert result_delisted.ticker_history.symbol == delisted_scenario.symbol
            assert result_delisted.ticker_history.valid_to == date(2020, 12, 31)

            # Test 3: Case-insensitive lookup
            result_lower = service.get_company_by_ticker(active_scenario.symbol.lower())
            result_upper = service.get_company_by_ticker(active_scenario.symbol.upper())
            result_mixed = service.get_company_by_ticker(
                active_scenario.symbol[0].lower() + active_scenario.symbol[1:].upper()
            )
            assert result_lower is not None
            assert result_upper is not None
            assert result_mixed is not None
            assert result_lower.company.company_name == active_scenario.company_name
            assert result_upper.company.company_name == active_scenario.company_name
            assert result_mixed.company.company_name == active_scenario.company_name

            # Test 4: Non-existent ticker returns None
            result_none = service.get_company_by_ticker("NONEXISTENT")
            assert result_none is None

    def test_update_company_by_ticker_comprehensive(self):
        """Test updating company via ticker symbol lookup.

        Validates:
        - Successful update returns True
        - Company fields are updated correctly
        - Update with non-existent ticker returns False
        - Updated fields match expected values from mock data
        """
        with integration_test_container() as (postgres, company_repo, port):
            from src.repos.equities.tickers.ticker_history_repository import (
                TickerHistoryRepository,
            )
            from src.services.companies.company_service import CompanyService

            mock_data = MockCompanyDataSource()
            ticker_history_repo = TickerHistoryRepository()
            service = CompanyService(company_repo, ticker_history_repo)

            # Get scenarios for original and updated data
            original_scenario = mock_data.get_scenario_by_symbol("TECH")
            update_scenario = mock_data.get_scenario_by_symbol("FINC")

            # Insert company with original data
            company = Company(
                company_name=original_scenario.company_name,
                exchange=original_scenario.exchange,
                sector=original_scenario.sector,
                active=original_scenario.active,
                source=DataSourceEnum.EODHD,
            )
            inserted_company = company_repo.insert(company)

            ticker_history = TickerHistory(
                symbol=original_scenario.symbol,
                company_id=inserted_company.id,
                valid_from=date(2020, 1, 1),
            )
            ticker_history_repo.insert(ticker_history)

            # Create update data from different scenario
            update_data = Company(
                company_name=update_scenario.company_name,
                exchange=update_scenario.exchange,
                sector=update_scenario.sector,
                source=DataSourceEnum.EODHD,
            )

            # Test 1: Successful update
            success = service.update_company(original_scenario.symbol, update_data)
            assert success is True

            # Verify update using exact values from mock
            updated_company = company_repo.get_by_id(inserted_company.id)
            assert updated_company.company_name == update_scenario.company_name
            assert updated_company.exchange == update_scenario.exchange
            assert updated_company.sector == update_scenario.sector

            # Test 2: Update with non-existent ticker
            success_none = service.update_company("NONEXISTENT", update_data)
            assert success_none is False

    def test_deactivate_company_by_ticker_comprehensive(self):
        """Test deactivating company via ticker symbol lookup.

        Validates:
        - Successful deactivation returns True
        - Company active flag is set to False
        - Deactivation with non-existent ticker returns False
        - Company data is preserved after deactivation
        """
        with integration_test_container() as (postgres, company_repo, port):
            from src.repos.equities.tickers.ticker_history_repository import (
                TickerHistoryRepository,
            )
            from src.services.companies.company_service import CompanyService

            mock_data = MockCompanyDataSource()
            ticker_history_repo = TickerHistoryRepository()
            service = CompanyService(company_repo, ticker_history_repo)

            # Get scenario for company to deactivate
            scenario = mock_data.get_active_scenario()

            # Insert active company
            company = Company(
                company_name=scenario.company_name,
                exchange=scenario.exchange,
                active=True,
                source=DataSourceEnum.EODHD,
            )
            inserted_company = company_repo.insert(company)

            ticker_history = TickerHistory(
                symbol=scenario.symbol,
                company_id=inserted_company.id,
                valid_from=date(2020, 1, 1),
            )
            ticker_history_repo.insert(ticker_history)

            # Test 1: Successful deactivation
            success = service.deactivate_company(scenario.symbol)
            assert success is True

            # Verify deactivation
            deactivated_company = company_repo.get_by_id(inserted_company.id)
            assert deactivated_company.active is False
            assert deactivated_company.company_name == scenario.company_name
            assert deactivated_company.exchange == scenario.exchange

            # Test 2: Deactivate non-existent ticker
            success_none = service.deactivate_company("NONEXISTENT")
            assert success_none is False
