"""Mock data source for ticker history integration tests."""

from __future__ import annotations

from datetime import date, timedelta

from tests.integration.services.tickers.ticker_history_scenarios import (
    CompanyTestScenario,
    TickerHistoryTestScenario,
)


class MockTickerHistoryDataSource:
    """Mock data source providing test ticker history scenarios."""

    def get_date_filtering_scenarios(
        self,
    ) -> tuple[CompanyTestScenario, list[TickerHistoryTestScenario], dict[str, list[str]]]:
        """Return scenarios for date filtering tests.

        Returns:
            Tuple of (company scenario, ticker history scenarios, expected results dict)
        """
        today = date.today()
        company = CompanyTestScenario(
            company_name="DateFilter Corp",
            exchange="NASDAQ",
            active=True,
        )

        ticker_histories = [
            # Currently valid (started in past, no end date)
            TickerHistoryTestScenario(
                symbol="CURR",
                valid_from=today - timedelta(days=365),
                valid_to=None,
            ),
            # Currently valid (started in past, ends in future)
            TickerHistoryTestScenario(
                symbol="VALID",
                valid_from=today - timedelta(days=365),
                valid_to=today + timedelta(days=365),
            ),
            # Expired (ended yesterday)
            TickerHistoryTestScenario(
                symbol="EXPIRED",
                valid_from=today - timedelta(days=365),
                valid_to=today - timedelta(days=1),
            ),
            # Future (starts tomorrow)
            TickerHistoryTestScenario(
                symbol="FUTURE",
                valid_from=today + timedelta(days=1),
                valid_to=today + timedelta(days=365),
            ),
        ]

        expected = {
            "active": ["CURR", "VALID"],
            "expired": ["EXPIRED"],
            "future": ["FUTURE"],
        }

        return company, ticker_histories, expected

    def get_active_inactive_scenarios(
        self,
    ) -> tuple[list[CompanyTestScenario], dict[str, list[str]]]:
        """Return scenarios for active/inactive company filtering.

        Returns:
            Tuple of (company scenarios with ticker symbols, expected results dict)
        """
        companies = [
            CompanyTestScenario(
                company_name="Active Corp A",
                exchange="NASDAQ",
                active=True,
            ),
            CompanyTestScenario(
                company_name="Active Corp B",
                exchange="NYSE",
                active=True,
            ),
            CompanyTestScenario(
                company_name="Inactive Corp",
                exchange="NASDAQ",
                active=False,
            ),
        ]

        expected = {
            "active": ["ACTVA", "ACTVB"],
            "inactive": ["INAC"],
        }

        return companies, expected

    def get_enrichment_scenario(self) -> CompanyTestScenario:
        """Return rich company data for enrichment testing."""
        return CompanyTestScenario(
            company_name="TechGiant Inc",
            exchange="NASDAQ",
            sector="Technology",
            industry="Software Development",
            country="USA",
            active=True,
        )
