"""Mock implementation of NASDAQ screener data sources for testing."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.data_sources.base.company_data_source import CompanyDataSource
from src.data_sources.models.company import Company
from src.data_sources.models.test_providers import StockMarketProvider
from src.data_sources.models.ticker import Ticker

from faker import Faker

logger = logging.getLogger(__name__)


class NasdaqScreenerLoaderMock:
    """Mock implementation of NasdaqScreenerLoader for testing."""

    def __init__(self, seed: int = 12345):
        """Initialize mock loader with Faker for realistic data."""
        self.fake = Faker()
        self.fake.add_provider(StockMarketProvider)
        Faker.seed(seed)
        self.logger = logging.getLogger(__name__)

        # Configuration for mock behavior
        self.companies_per_file = 50
        self.should_fail = False
        self.error_message = "Mock loader error"

    def _create_fake_company(self, **overrides: Any) -> Company:
        """Create a realistic Company with Faker data for NASDAQ."""
        ticker_symbol = self.fake.stock_ticker()

        default_data = {
            "id": None,
            "company_name": self.fake.company(),
            "exchange": "NASDAQ",  # Always NASDAQ for screener data
            "sector": self.fake.stock_sector(),
            "industry": self.fake.stock_industry(),
            "country": "United States",
            "market_cap": self.fake.market_cap(),
            "description": None,
            "active": True,
            "source": "NASDAQ_SCREENER",
            "ticker": Ticker(symbol=ticker_symbol, company_id=None),
        }

        default_data.update(overrides)
        return Company(**default_data)

    def load_file(self, file_path: str | Path) -> list[Company]:
        """Mock load NASDAQ screener data from CSV file.

        Args:
            file_path: Path to the CSV file (ignored in mock)

        Returns:
            List of mock Company objects with screener data

        Raises:
            FileNotFoundError: If configured to simulate file not found
            ValueError: If configured to simulate invalid file format
        """
        if self.should_fail:
            if "not found" in self.error_message.lower():
                raise FileNotFoundError(self.error_message)
            else:
                raise ValueError(self.error_message)

        file_path = Path(file_path)
        self.logger.info(f"Mock: Loading NASDAQ screener data from {file_path}")

        # Generate realistic companies
        companies = []
        for _ in range(self.companies_per_file):
            company = self._create_fake_company()
            companies.append(company)

        self.logger.info(
            f"Mock: Successfully loaded {len(companies)} companies from screener file"
        )
        return companies

    def load_directory(self, directory_path: str | Path) -> list[Company]:
        """Mock load all NASDAQ screener files from a directory.

        Args:
            directory_path: Path to directory containing screener CSV files

        Returns:
            List of mock Company objects from all screener files
        """
        if self.should_fail:
            if "not found" in self.error_message.lower():
                raise FileNotFoundError(self.error_message)
            else:
                raise ValueError(self.error_message)

        directory_path = (
            Path(directory_path) if directory_path else Path("mock_directory")
        )

        # Simulate finding multiple screener files
        mock_files = [
            "nasdaq_screener_08_01_2025.csv",
            "nasdaq_screener_08_02_2025.csv",
            "nasdaq_screener_08_03_2025.csv",
        ]

        all_companies = []

        self.logger.info(
            f"Mock: Found {len(mock_files)} screener files in {directory_path}"
        )

        for filename in mock_files:
            try:
                # Generate different number of companies per file for realism
                file_company_count = self.fake.random_int(20, 100)
                companies = [
                    self._create_fake_company() for _ in range(file_company_count)
                ]
                all_companies.extend(companies)
                self.logger.info(
                    f"Mock: Loaded {len(companies)} companies from {filename}"
                )
            except Exception as e:
                self.logger.error(f"Mock: Error loading file {filename}: {e}")
                continue

        self.logger.info(
            f"Mock: Total companies loaded from all screener files: {len(all_companies)}"
        )
        return all_companies

    def set_companies_per_file(self, count: int) -> None:
        """Set number of companies to generate per file."""
        self.companies_per_file = count

    def simulate_error(self, error_message: str) -> None:
        """Configure mock to simulate an error."""
        self.should_fail = True
        self.error_message = error_message

    def reset_error(self) -> None:
        """Reset mock to normal operation."""
        self.should_fail = False
        self.error_message = ""


class NasdaqScreenerSourceMock(CompanyDataSource):
    """Mock implementation of NasdaqScreenerSource for testing."""

    def __init__(self, screener_dir: str | None = None, seed: int = 12345):
        """Initialize mock NASDAQ screener source.

        Args:
            screener_dir: Path to directory containing screener CSV files (ignored in mock)
            seed: Seed for consistent fake data generation
        """
        self.screener_dir = screener_dir
        self.loader = NasdaqScreenerLoaderMock(seed=seed)
        self._is_available = True

    @property
    def name(self) -> str:
        """Name of the data source."""
        return "NASDAQ Screener Files (Mock)"

    def get_companies(self) -> list[Company]:
        """Mock load companies from NASDAQ screener files.

        Returns:
            List of mock Company objects from screener files
        """
        if not self._is_available:
            raise ConnectionError("Mock: NASDAQ screener source is not available")

        # Use current directory as default if None provided for mock
        directory = self.screener_dir or "."
        return self.loader.load_directory(directory)

    def is_available(self) -> bool:
        """Check if the mock data source is available."""
        return self._is_available

    # Mock-specific utility methods
    def set_available(self, available: bool) -> None:
        """Set availability status for testing."""
        self._is_available = available

    def set_companies_per_file(self, count: int) -> None:
        """Set number of companies to generate per file."""
        self.loader.set_companies_per_file(count)

    def simulate_loader_error(self, error_message: str) -> None:
        """Configure mock to simulate a loader error."""
        self.loader.simulate_error(error_message)

    def reset_loader_error(self) -> None:
        """Reset mock loader to normal operation."""
        self.loader.reset_error()

    def get_mock_file_count(self) -> int:
        """Get number of mock files that would be processed."""
        return 3  # Hardcoded in load_directory mock


# Factory functions for easy mock creation
def create_nasdaq_screener_loader_mock(seed: int = 12345) -> NasdaqScreenerLoaderMock:
    """Factory function to create a NasdaqScreenerLoaderMock instance."""
    return NasdaqScreenerLoaderMock(seed=seed)


def create_nasdaq_screener_source_mock(
    screener_dir: str | None = None, seed: int = 12345
) -> NasdaqScreenerSourceMock:
    """Factory function to create a NasdaqScreenerSourceMock instance."""
    return NasdaqScreenerSourceMock(screener_dir=screener_dir, seed=seed)


# Mock implementations for backward compatibility functions
class ScreenerFunctionsMock:
    """Mock implementations for the standalone screener functions."""

    def __init__(self, seed: int = 12345):
        self.loader = NasdaqScreenerLoaderMock(seed=seed)

    def load_screener_file(self, file_path: str | Path) -> list[Company]:
        """Mock implementation of load_screener_file function."""
        return self.loader.load_file(file_path)

    def load_screener_files_from_directory(
        self, directory_path: str | Path
    ) -> list[Company]:
        """Mock implementation of load_screener_files_from_directory function."""
        return self.loader.load_directory(directory_path)


# Global mock instance for standalone function mocking
_mock_functions = ScreenerFunctionsMock()


def mock_load_screener_file(file_path: str | Path) -> list[Company]:
    """Mock version of load_screener_file function."""
    return _mock_functions.load_screener_file(file_path)


def mock_load_screener_files_from_directory(
    directory_path: str | Path,
) -> list[Company]:
    """Mock version of load_screener_files_from_directory function."""
    return _mock_functions.load_screener_files_from_directory(directory_path)


# Example usage for testing
if __name__ == "__main__":
    # Create mock screener source
    mock_source = create_nasdaq_screener_source_mock()

    print(f"Mock source name: {mock_source.name}")
    print(f"Mock source available: {mock_source.is_available()}")

    # Get mock companies
    companies = mock_source.get_companies()
    print(f"Generated {len(companies)} mock companies")

    # Show first few companies
    for i, company in enumerate(companies[:3]):
        print(f"\nCompany {i + 1}:")
        print(f"  Name: {company.company_name}")
        print(f"  Ticker: {company.ticker.symbol if company.ticker else 'N/A'}")
        print(f"  Sector: {company.sector}")
        print(
            f"  Market Cap: ${company.market_cap:,}"
            if company.market_cap
            else "  Market Cap: N/A"
        )

    # Test error simulation
    print("\n--- Testing Error Simulation ---")
    mock_source.simulate_loader_error("Mock file not found error")

    try:
        companies = mock_source.get_companies()
    except Exception as e:
        print(f"Caught expected error: {e}")

    # Reset and test again
    mock_source.reset_loader_error()
    companies = mock_source.get_companies()
    print(f"After reset: Generated {len(companies)} companies successfully")

    # Test availability
    print("\n--- Testing Availability ---")
    mock_source.set_available(False)
    print(f"Availability set to: {mock_source.is_available()}")

    try:
        companies = mock_source.get_companies()
    except ConnectionError as e:
        print(f"Caught expected connection error: {e}")

    mock_source.set_available(True)
    print(f"Availability reset to: {mock_source.is_available()}")
