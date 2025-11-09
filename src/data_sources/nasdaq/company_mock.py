"""Mock implementation of NASDAQ company data source for testing."""

from __future__ import annotations

import logging

from faker import Faker

from src.data_sources.base.company_data_source import CompanyDataSource
from src.models.company import Company
from src.models.test_providers import StockMarketProvider
from src.models.ticker import Ticker

logger = logging.getLogger(__name__)


class Headers:
    COMPANY_NAME = "company_name"
    TICKER = "ticker"
    EXCHANGE = "exchange"


class NasdaqCompanySourceMock(CompanyDataSource):
    """Mock implementation of NasdaqCompanySource for testing."""

    def __init__(self, seed: int = 12345):
        """Initialize mock NASDAQ API with Faker for realistic data."""
        self.fake = Faker()
        self.fake.add_provider(StockMarketProvider)
        Faker.seed(seed)

        # Mock configuration
        self._should_fail = False
        self._error_message = "Mock API error"
        self._response_status = 200
        self._company_count = 100

        # Predefined realistic companies
        self._predefined_companies = [
            {"ticker": "AAPL", "company_name": "Apple Inc.", "exchange": "NASDAQ"},
            {
                "ticker": "GOOGL",
                "company_name": "Alphabet Inc. Class A",
                "exchange": "NASDAQ",
            },
            {
                "ticker": "MSFT",
                "company_name": "Microsoft Corporation",
                "exchange": "NASDAQ",
            },
            {"ticker": "AMZN", "company_name": "Amazon.com Inc.", "exchange": "NASDAQ"},
            {"ticker": "TSLA", "company_name": "Tesla Inc.", "exchange": "NASDAQ"},
            {
                "ticker": "META",
                "company_name": "Meta Platforms Inc.",
                "exchange": "NASDAQ",
            },
            {
                "ticker": "NVDA",
                "company_name": "NVIDIA Corporation",
                "exchange": "NASDAQ",
            },
            {
                "ticker": "AMD",
                "company_name": "Advanced Micro Devices Inc.",
                "exchange": "NASDAQ",
            },
            {"ticker": "NFLX", "company_name": "Netflix Inc.", "exchange": "NASDAQ"},
            {
                "ticker": "UBER",
                "company_name": "Uber Technologies Inc.",
                "exchange": "NYSE",
            },
        ]

    @property
    def name(self) -> str:
        """Name of the data source."""
        return "NASDAQ API (Mock)"

    def is_available(self) -> bool:
        """Check if the mock NASDAQ API is available."""
        if self._should_fail:
            return False
        return True

    def get_companies(self) -> list[Company]:
        """Mock get_companies function that simulates the NASDAQ API call.

        Returns:
            List of mock Company objects

        Raises:
            Exception: If configured to simulate API errors
        """
        if self._should_fail:
            raise Exception(self._error_message)

        raw_data = self._get_dict_of_stocks()
        if raw_data is None:
            return []
        return _convert_dict_to_stocks(raw_data)

    def _get_dict_of_stocks(self) -> list[dict[str, str]] | None:
        """Mock get_dict_of_stocks function that simulates NASDAQ API response.

        Returns:
            List of dictionaries with stock data

        Raises:
            Exception: If configured to simulate API errors
        """
        if self._should_fail:
            if self._response_status != 200:
                raise Exception(
                    f"Failed to retrieve nasdaq companies. Status code: {self._response_status}"
                )
            else:
                raise Exception("get companies did not get the expected response")

        logger.info(f"Mock: Fetching {self._company_count} companies from NASDAQ API")

        companies_data = []

        # Add predefined companies first
        companies_data.extend(
            self._predefined_companies[
                : min(len(self._predefined_companies), self._company_count)
            ]
        )

        # Generate additional companies if needed
        remaining_count = self._company_count - len(companies_data)
        for _ in range(remaining_count):
            company_data = {
                Headers.TICKER: self.fake.stock_ticker(),
                Headers.COMPANY_NAME: self.fake.company(),
                Headers.EXCHANGE: self.fake.stock_exchange(),
            }
            companies_data.append(company_data)

        logger.info(
            f"Mock: Successfully generated {len(companies_data)} company records"
        )
        return companies_data

    def _convert_dict_to_stocks(self, data: list[dict[str, str]]) -> list[Company]:
        """Convert dictionary data to Company objects.

        Args:
            data: List of dictionaries with company data

        Returns:
            List of Company objects
        """
        if data is None:
            return []
        return _convert_dict_to_stocks(data)

    # Mock-specific utility methods
    def set_company_count(self, count: int) -> None:
        """Set number of companies to generate."""
        self._company_count = count

    def simulate_api_error(self, error_message: str, status_code: int = 500) -> None:
        """Configure mock to simulate API error."""
        self._should_fail = True
        self._error_message = error_message
        self._response_status = status_code

    def simulate_auth_error(self) -> None:
        """Simulate authentication/API key error."""
        self.simulate_api_error("Invalid API key or authentication failed", 401)

    def simulate_rate_limit_error(self) -> None:
        """Simulate rate limiting error."""
        self.simulate_api_error("Rate limit exceeded. Please try again later.", 429)

    def simulate_network_error(self) -> None:
        """Simulate network connectivity error."""
        self.simulate_api_error(
            "Connection timeout - unable to connect to NASDAQ API", 503
        )

    def simulate_invalid_response(self) -> None:
        """Simulate invalid API response structure."""
        self.simulate_api_error("get companies did not get the expected response", 200)

    def reset_error(self) -> None:
        """Reset mock to normal operation."""
        self._should_fail = False
        self._error_message = ""
        self._response_status = 200

    def add_predefined_company(
        self, ticker: str, company_name: str, exchange: str = "NASDAQ"
    ) -> None:
        """Add a predefined company to the mock data."""
        company_data = {
            "ticker": ticker.upper(),
            "company_name": company_name,
            "exchange": exchange.upper(),
        }
        self._predefined_companies.append(company_data)

    def clear_predefined_companies(self) -> None:
        """Clear all predefined companies."""
        self._predefined_companies.clear()

    def get_predefined_companies_count(self) -> int:
        """Get count of predefined companies."""
        return len(self._predefined_companies)


# Module-level function that matches original
def _convert_dict_to_stocks(ds: list[dict[str, str]]) -> list[Company]:
    """Convert dictionary data to Company objects."""
    companies = []
    for k in ds:
        ticker = Ticker(symbol=k[Headers.TICKER], company_id=None)
        company = Company(
            company_name=k[Headers.COMPANY_NAME],
            exchange=k[Headers.EXCHANGE],
            ticker=ticker,
            source="NASDAQ",
        )
        companies.append(company)
    return companies


# Global mock instance for function mocking
_global_mock = NasdaqCompanySourceMock()


def mock_get_companies() -> list[Company]:
    """Mock version of get_companies function."""
    return _global_mock.get_companies()


def mock_get_dict_of_stocks() -> list[dict[str, str]] | None:
    """Mock version of get_dict_of_stocks function."""
    return _global_mock._get_dict_of_stocks()


# Factory function for easy mock creation
def create_nasdaq_company_source_mock(seed: int = 12345) -> NasdaqCompanySourceMock:
    """Factory function to create a NasdaqCompanySourceMock instance."""
    return NasdaqCompanySourceMock(seed=seed)


# Backward compatibility
def create_nasdaq_company_api_mock(seed: int = 12345) -> NasdaqCompanySourceMock:
    """DEPRECATED: Use create_nasdaq_company_source_mock instead."""
    return NasdaqCompanySourceMock(seed=seed)


# Example usage for testing
if __name__ == "__main__":
    # Create mock source
    mock_source = create_nasdaq_company_source_mock()

    print(
        f"Mock source initialized with {mock_source.get_predefined_companies_count()} predefined companies"
    )
    print(f"Configured to generate {mock_source._company_count} total companies")
    print(f"Data source name: {mock_source.name}")
    print(f"Is available: {mock_source.is_available()}")

    # Test normal operation
    print("\n--- Testing Normal Operation ---")
    companies = mock_source.get_companies()
    print(f"Generated {len(companies)} companies")

    # Show first few companies
    for i, company in enumerate(companies[:5]):
        print(
            f"{i + 1}. {company.ticker} - {company.company_name} ({company.exchange})"
        )

    # Test error simulation
    print("\n--- Testing Error Simulation ---")
    mock_source.simulate_auth_error()

    try:
        companies = mock_source.get_companies()
    except Exception as e:
        print(f"Caught expected auth error: {e}")

    # Test rate limit error
    mock_source.simulate_rate_limit_error()

    try:
        companies = mock_source.get_companies()
    except Exception as e:
        print(f"Caught expected rate limit error: {e}")

    # Reset and test again
    mock_source.reset_error()
    companies = mock_source.get_companies()
    print(f"After reset: Generated {len(companies)} companies successfully")

    # Test company count configuration
    print("\n--- Testing Company Count Configuration ---")
    original_count = len(companies)
    mock_source.set_company_count(25)
    companies = mock_source.get_companies()
    print(f"Changed company count: {original_count} -> {len(companies)}")

    # Test adding predefined companies
    print("\n--- Testing Predefined Company Management ---")
    mock_source.add_predefined_company("TEST", "Test Company Inc.", "NASDAQ")
    companies = mock_source.get_companies()
    test_company = next(
        (c for c in companies if c.ticker and c.ticker.symbol == "TEST"), None
    )
    print(f"Added TEST company: {'Found' if test_company else 'Not found'}")
    if test_company:
        if test_company.ticker:
            print(
                f"  {test_company.ticker.symbol} - {test_company.company_name} ({test_company.exchange})"
            )

    # Test global mock functions
    print("\n--- Testing Global Mock Functions ---")
    global_companies = mock_get_companies()
    print(f"Global mock generated {len(global_companies)} companies")

    global_dict_data = mock_get_dict_of_stocks()
    if global_dict_data:
        print(f"Global mock dict data contains {len(global_dict_data)} records")
    else:
        print("Global mock dict data is None")

    # Test network error simulation
    print("\n--- Testing Network Error ---")
    mock_source.simulate_network_error()

    try:
        companies = mock_source.get_companies()
    except Exception as e:
        print(f"Caught expected network error: {e}")

    # Test invalid response simulation
    mock_source.simulate_invalid_response()

    try:
        companies = mock_source.get_companies()
    except Exception as e:
        print(f"Caught expected invalid response error: {e}")

    mock_source.reset_error()
    print("Mock reset to normal operation")
