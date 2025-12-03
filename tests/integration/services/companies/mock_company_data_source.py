"""Mock data source for company integration tests."""

from __future__ import annotations

from tests.integration.services.companies.company_scenarios import CompanyTestScenario


class MockCompanyDataSource:
    """Mock data source providing test company scenarios."""

    def __init__(self):
        self._scenarios = [
            CompanyTestScenario(
                company_name="TechCorp Solutions",
                exchange="NASDAQ",
                sector="Technology",
                industry="Software",
                country="USA",
                active=True,
                symbol="TECH",
            ),
            CompanyTestScenario(
                company_name="Finance Holdings Inc",
                exchange="NYSE",
                sector="Finance",
                industry="Banking",
                country="USA",
                active=True,
                symbol="FINC",
            ),
            CompanyTestScenario(
                company_name="Legacy Industries",
                exchange="NYSE",
                sector="Manufacturing",
                industry="Industrial Equipment",
                country="USA",
                active=False,
                symbol="LGCY",
            ),
        ]

    def get_active_scenario(self) -> CompanyTestScenario:
        """Get first active company scenario."""
        return next(s for s in self._scenarios if s.active)

    def get_inactive_scenario(self) -> CompanyTestScenario:
        """Get first inactive company scenario."""
        return next(s for s in self._scenarios if not s.active)

    def get_scenario_by_symbol(self, symbol: str) -> CompanyTestScenario:
        """Get scenario by symbol."""
        return next(s for s in self._scenarios if s.symbol == symbol)

    def get_all_active(self) -> list[CompanyTestScenario]:
        """Get all active scenarios."""
        return [s for s in self._scenarios if s.active]

    def get_all_inactive(self) -> list[CompanyTestScenario]:
        """Get all inactive scenarios."""
        return [s for s in self._scenarios if not s.active]
