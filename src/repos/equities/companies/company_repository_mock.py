"""Mock implementation of CompanyRepository for testing."""

from __future__ import annotations

import logging
from typing import Any

from src.data_sources.models.company import Company as CompanyDataModel
from src.data_sources.models.test_providers import StockMarketProvider
from src.data_sources.models.ticker import Ticker

from faker import Faker

logger = logging.getLogger(__name__)


class CompanyRepositoryMock:
    """Mock implementation of CompanyRepository for testing purposes."""

    def __init__(self, seed: int = 12345):
        """Initialize mock repository with Faker for realistic data."""
        self.fake = Faker()
        self.fake.add_provider(StockMarketProvider)
        Faker.seed(seed)

        # In-memory storage for mock data
        self._companies: dict[int, CompanyDataModel] = {}
        self._next_id = 1
        self._ticker_to_company: dict[str, int] = {}

        # Initialize with some sample data
        self._initialize_sample_data()

    def _initialize_sample_data(self) -> None:
        """Initialize with realistic sample companies."""
        sample_companies = [
            {
                "company_name": "Apple Inc.",
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "market_cap": 3000000000000,
                "ticker_symbol": "AAPL",
            },
            {
                "company_name": "Microsoft Corporation",
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Software",
                "market_cap": 2800000000000,
                "ticker_symbol": "MSFT",
            },
            {
                "company_name": "Amazon.com Inc.",
                "exchange": "NASDAQ",
                "sector": "Consumer Discretionary",
                "industry": "Internet Retail",
                "market_cap": 1500000000000,
                "ticker_symbol": "AMZN",
            },
        ]

        for company_data in sample_companies:
            ticker_symbol = str(company_data.pop("ticker_symbol"))
            ticker = Ticker(symbol=ticker_symbol, company_id=self._next_id)

            company = CompanyDataModel(
                id=self._next_id,
                ticker=ticker,
                country="United States",
                active=True,
                source="MOCK_DATA",
                company_name=str(company_data["company_name"]),
                exchange=str(company_data["exchange"]),
                sector=str(company_data.get("sector")),
                industry=str(company_data.get("industry")),
                market_cap=int(str(company_data["market_cap"])) if company_data.get("market_cap") is not None and company_data["market_cap"] != "" else None,
            )

            self._companies[self._next_id] = company
            self._ticker_to_company[str(ticker_symbol)] = self._next_id
            self._next_id += 1

    def _create_fake_company(self, **overrides: Any) -> CompanyDataModel:
        """Create a realistic Company with Faker data."""
        ticker_symbol = self.fake.stock_ticker()

        default_data = {
            "id": self._next_id,
            "company_name": self.fake.company(),
            "exchange": self.fake.stock_exchange(),
            "sector": self.fake.stock_sector(),
            "industry": self.fake.stock_industry(),
            "country": "United States",
            "market_cap": self.fake.market_cap(),
            "description": self.fake.company_description(),
            "active": True,
            "source": "MOCK_DATA",
            "ticker": Ticker(symbol=ticker_symbol, company_id=self._next_id),
        }

        default_data.update(overrides)
        return CompanyDataModel(**default_data)

    # Base repository methods
    def get(
        self, filter_model: CompanyDataModel | None = None
    ) -> list[CompanyDataModel]:
        """Get companies based on filter."""
        companies = list(self._companies.values())

        if filter_model is None:
            return companies

        filtered = []
        for company in companies:
            match = True

            if filter_model.id is not None and company.id != filter_model.id:
                match = False
            if (
                filter_model.active is not None
                and company.active != filter_model.active
            ):
                match = False
            if (
                filter_model.sector is not None
                and filter_model.sector != ""
                and company.sector != filter_model.sector
            ):
                match = False
            if (
                filter_model.exchange is not None
                and filter_model.exchange != ""
                and company.exchange != filter_model.exchange
            ):
                match = False
            if (
                hasattr(filter_model, "ticker")
                and filter_model.ticker is not None
                and company.ticker
                and company.ticker.symbol != filter_model.ticker
            ):
                match = False

            if match:
                filtered.append(company)

        return filtered

    def get_one(self, filter_model: CompanyDataModel) -> CompanyDataModel | None:
        """Get single company matching filter."""
        results = self.get(filter_model)
        return results[0] if results else None

    def get_by_id(self, id: int) -> CompanyDataModel | None:
        """Get company by ID."""
        return self._companies.get(id)

    def count(self, filter_model: CompanyDataModel | None = None) -> int:
        """Count companies matching filter."""
        return len(self.get(filter_model))

    def insert(self, data_model: CompanyDataModel) -> CompanyDataModel:
        """Insert single company."""
        if data_model.id is None:
            data_model.id = self._next_id
            self._next_id += 1

        if data_model.ticker:
            data_model.ticker.company_id = data_model.id
            self._ticker_to_company[data_model.ticker.symbol] = data_model.id

        self._companies[data_model.id] = data_model
        logger.info(f"Mock: Inserted company with ID {data_model.id}")
        return data_model

    def insert_many(self, data_models: list[CompanyDataModel]) -> int:
        """Insert multiple companies."""
        count = 0
        for company in data_models:
            self.insert(company)
            count += 1

        logger.info(f"Mock: Bulk inserted {count} companies")
        return count

    def update(
        self, filter_model: CompanyDataModel, update_data: CompanyDataModel
    ) -> int:
        """Update companies matching filter."""
        companies_to_update = self.get(filter_model)
        count = 0

        for company in companies_to_update:
            # Update non-empty fields from update_data
            if update_data.company_name and update_data.company_name != "":
                company.company_name = update_data.company_name
            if update_data.sector and update_data.sector != "":
                company.sector = update_data.sector
            if update_data.industry and update_data.industry != "":
                company.industry = update_data.industry
            if update_data.market_cap is not None:
                company.market_cap = update_data.market_cap
            if update_data.active is not None:
                company.active = update_data.active
            if update_data.description and update_data.description != "":
                company.description = update_data.description

            count += 1

        logger.info(f"Mock: Updated {count} companies")
        return count

    def update_by_id(self, id: int, update_data: CompanyDataModel) -> bool:
        """Update company by ID."""
        filter_model = CompanyDataModel(id=id, company_name="", exchange="")
        return self.update(filter_model, update_data) > 0

    # Domain-specific methods
    def get_active_company_symbols(self) -> set[str]:
        """Get set of active company ticker symbols by joining with ticker data."""
        # Simulate the database join: CompanyTable JOIN TickerTable
        # In our mock, we get symbols from the ticker information of active companies
        symbols = set()

        for company in self._companies.values():
            if company.active and company.ticker:
                symbols.add(company.ticker.symbol)

        logger.info(
            f"Mock: Retrieved {len(symbols)} active company symbols (simulating join)"
        )
        return symbols

    def get_all_companies(self) -> list[CompanyDataModel]:
        """Retrieve all companies."""
        return self.get()

    def get_active_companies(self) -> list[CompanyDataModel]:
        """Retrieve all active companies."""
        active_filter = CompanyDataModel(active=True, company_name="", exchange="")
        return self.get(active_filter)

    def get_company_by_ticker(self, ticker: str) -> CompanyDataModel | None:
        """Get company by ticker symbol."""
        company_id = self._ticker_to_company.get(ticker.upper())
        if company_id:
            return self._companies.get(company_id)
        return None

    def bulk_insert_companies(self, companies: list[CompanyDataModel]) -> int:
        """Bulk insert companies."""
        return self.insert_many(companies)

    def update_company(self, ticker: str, company_data: CompanyDataModel) -> bool:
        """Update company by ticker."""
        company = self.get_company_by_ticker(ticker.upper())
        if company:
            filter_model = CompanyDataModel(id=company.id, company_name="", exchange="")
            return self.update(filter_model, company_data) > 0
        return False

    def deactivate_company(self, ticker: str) -> bool:
        """Deactivate company."""
        deactivate_data = CompanyDataModel(active=False, company_name="", exchange="")
        return self.update_company(ticker, deactivate_data)

    # Utility methods for testing
    def reset(self) -> None:
        """Reset mock data to initial state."""
        self._companies.clear()
        self._ticker_to_company.clear()
        self._next_id = 1
        self._initialize_sample_data()

    def add_fake_companies(self, count: int = 5) -> list[CompanyDataModel]:
        """Add fake companies for testing."""
        companies = []
        for _ in range(count):
            company = self._create_fake_company()
            self.insert(company)
            companies.append(company)

        return companies

    def get_company_count(self) -> int:
        """Get total number of companies."""
        return len(self._companies)

    def simulate_database_error(
        self, method_name: str, error_message: str = "Database error"
    ) -> None:
        """Simulate database error for testing error handling."""
        # This would typically be implemented with a flag system
        # For now, just log the simulation
        logger.warning(
            f"Mock: Simulating database error for {method_name}: {error_message}"
        )
        raise Exception(error_message)


# Factory function for easy mock creation
def create_company_repository_mock(seed: int = 12345) -> CompanyRepositoryMock:
    """Factory function to create a CompanyRepositoryMock instance."""
    return CompanyRepositoryMock(seed=seed)


# Example usage for testing
if __name__ == "__main__":
    # Create mock repository
    mock_repo = create_company_repository_mock()

    # Display sample data
    print(
        f"Mock repository initialized with {mock_repo.get_company_count()} companies:"
    )
    for company in mock_repo.get_all_companies():
        print(
            f"  - {company.company_name} ({company.ticker.symbol if company.ticker else 'N/A'})"
        )

    # Add some fake companies
    fake_companies = mock_repo.add_fake_companies(3)
    print(f"\nAdded {len(fake_companies)} fake companies:")
    for company in fake_companies:
        print(
            f"  - {company.company_name} ({company.ticker.symbol if company.ticker else 'N/A'})"
        )

    # Test filtering by getting technology companies manually
    all_companies = mock_repo.get_all_companies()
    tech_companies = [c for c in all_companies if c.sector == "Technology"]
    print(f"\nFound {len(tech_companies)} technology companies")
