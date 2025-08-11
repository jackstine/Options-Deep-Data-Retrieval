"""Mock implementation of NASDAQ company data source for testing."""

from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional
from faker import Faker

from src.data_sources.models.company import Company
from src.data_sources.models.test_providers import StockMarketProvider


logger = logging.getLogger(__name__)


class Headers:
    COMPANY_NAME = "company_name"
    TICKER = "ticker"
    EXCHANGE = "exchange"


class NasdaqCompanyAPIMock:
    """Mock implementation of NASDAQ Company API for testing."""
    
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
            {"ticker": "GOOGL", "company_name": "Alphabet Inc. Class A", "exchange": "NASDAQ"},
            {"ticker": "MSFT", "company_name": "Microsoft Corporation", "exchange": "NASDAQ"},
            {"ticker": "AMZN", "company_name": "Amazon.com Inc.", "exchange": "NASDAQ"},
            {"ticker": "TSLA", "company_name": "Tesla Inc.", "exchange": "NASDAQ"},
            {"ticker": "META", "company_name": "Meta Platforms Inc.", "exchange": "NASDAQ"},
            {"ticker": "NVDA", "company_name": "NVIDIA Corporation", "exchange": "NASDAQ"},
            {"ticker": "AMD", "company_name": "Advanced Micro Devices Inc.", "exchange": "NASDAQ"},
            {"ticker": "NFLX", "company_name": "Netflix Inc.", "exchange": "NASDAQ"},
            {"ticker": "UBER", "company_name": "Uber Technologies Inc.", "exchange": "NYSE"},
        ]
    
    def get_companies(self) -> List[Company]:
        """
        Mock get_companies function that simulates the NASDAQ API call.
        
        Returns:
            List of mock Company objects
            
        Raises:
            Exception: If configured to simulate API errors
        """
        if self._should_fail:
            raise Exception(self._error_message)
        
        raw_data = self.get_dict_of_stocks()
        return self._convert_dict_to_stocks(raw_data)
    
    def get_dict_of_stocks(self) -> List[Dict[str, str]]:
        """
        Mock get_dict_of_stocks function that simulates NASDAQ API response.
        
        Returns:
            List of dictionaries with stock data
            
        Raises:
            Exception: If configured to simulate API errors
        """
        if self._should_fail:
            if self._response_status != 200:
                raise Exception(f'Failed to retrieve nasdaq companies. Status code: {self._response_status}')
            else:
                raise Exception("get companies did not get the expected response")
        
        logger.info(f"Mock: Fetching {self._company_count} companies from NASDAQ API")
        
        companies_data = []
        
        # Add predefined companies first
        companies_data.extend(self._predefined_companies[:min(len(self._predefined_companies), self._company_count)])
        
        # Generate additional companies if needed
        remaining_count = self._company_count - len(companies_data)
        for _ in range(remaining_count):
            company_data = {
                Headers.TICKER: self.fake.stock_ticker(),
                Headers.COMPANY_NAME: self.fake.company(),
                Headers.EXCHANGE: self.fake.stock_exchange()
            }
            companies_data.append(company_data)
        
        logger.info(f"Mock: Successfully generated {len(companies_data)} company records")
        return companies_data
    
    def _convert_dict_to_stocks(self, data: List[Dict[str, str]]) -> List[Company]:
        """
        Convert dictionary data to Company objects.
        
        Args:
            data: List of dictionaries with company data
            
        Returns:
            List of Company objects
        """
        return [
            Company(
                ticker=item[Headers.TICKER],
                company_name=item[Headers.COMPANY_NAME],
                exchange=item[Headers.EXCHANGE],
                source="NASDAQ"
            )
            for item in data
        ]
    
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
        self.simulate_api_error("Connection timeout - unable to connect to NASDAQ API", 503)
    
    def simulate_invalid_response(self) -> None:
        """Simulate invalid API response structure."""
        self.simulate_api_error("get companies did not get the expected response", 200)
    
    def reset_error(self) -> None:
        """Reset mock to normal operation."""
        self._should_fail = False
        self._error_message = ""
        self._response_status = 200
    
    def add_predefined_company(self, ticker: str, company_name: str, exchange: str = "NASDAQ") -> None:
        """Add a predefined company to the mock data."""
        company_data = {
            "ticker": ticker.upper(),
            "company_name": company_name,
            "exchange": exchange.upper()
        }
        self._predefined_companies.append(company_data)
    
    def clear_predefined_companies(self) -> None:
        """Clear all predefined companies."""
        self._predefined_companies.clear()
    
    def get_predefined_companies_count(self) -> int:
        """Get count of predefined companies."""
        return len(self._predefined_companies)


# Global mock instance for function mocking
_global_mock = NasdaqCompanyAPIMock()

def mock_get_companies() -> List[Company]:
    """Mock version of get_companies function."""
    return _global_mock.get_companies()

def mock_get_dict_of_stocks() -> List[Dict[str, str]]:
    """Mock version of get_dict_of_stocks function."""
    return _global_mock.get_dict_of_stocks()

# Factory function for easy mock creation
def create_nasdaq_company_api_mock(seed: int = 12345) -> NasdaqCompanyAPIMock:
    """Factory function to create a NasdaqCompanyAPIMock instance."""
    return NasdaqCompanyAPIMock(seed=seed)


# Example usage for testing
if __name__ == "__main__":
    # Create mock API
    mock_api = create_nasdaq_company_api_mock()
    
    print(f"Mock API initialized with {mock_api.get_predefined_companies_count()} predefined companies")
    print(f"Configured to generate {mock_api._company_count} total companies")
    
    # Test normal operation
    print("\n--- Testing Normal Operation ---")
    companies = mock_api.get_companies()
    print(f"Generated {len(companies)} companies")
    
    # Show first few companies
    for i, company in enumerate(companies[:5]):
        print(f"{i+1}. {company.ticker} - {company.company_name} ({company.exchange})")
    
    # Test error simulation
    print("\n--- Testing Error Simulation ---")
    mock_api.simulate_auth_error()
    
    try:
        companies = mock_api.get_companies()
    except Exception as e:
        print(f"Caught expected auth error: {e}")
    
    # Test rate limit error
    mock_api.simulate_rate_limit_error()
    
    try:
        companies = mock_api.get_companies()
    except Exception as e:
        print(f"Caught expected rate limit error: {e}")
    
    # Reset and test again
    mock_api.reset_error()
    companies = mock_api.get_companies()
    print(f"After reset: Generated {len(companies)} companies successfully")
    
    # Test company count configuration
    print("\n--- Testing Company Count Configuration ---")
    original_count = len(companies)
    mock_api.set_company_count(25)
    companies = mock_api.get_companies()
    print(f"Changed company count: {original_count} -> {len(companies)}")
    
    # Test adding predefined companies
    print("\n--- Testing Predefined Company Management ---")
    mock_api.add_predefined_company("TEST", "Test Company Inc.", "NASDAQ")
    companies = mock_api.get_companies()
    test_company = next((c for c in companies if c.ticker == "TEST"), None)
    print(f"Added TEST company: {'Found' if test_company else 'Not found'}")
    if test_company:
        print(f"  {test_company.ticker} - {test_company.company_name} ({test_company.exchange})")
    
    # Test global mock functions
    print("\n--- Testing Global Mock Functions ---")
    global_companies = mock_get_companies()
    print(f"Global mock generated {len(global_companies)} companies")
    
    global_dict_data = mock_get_dict_of_stocks()
    print(f"Global mock dict data contains {len(global_dict_data)} records")
    
    # Test network error simulation
    print("\n--- Testing Network Error ---")
    mock_api.simulate_network_error()
    
    try:
        companies = mock_api.get_companies()
    except Exception as e:
        print(f"Caught expected network error: {e}")
    
    # Test invalid response simulation
    mock_api.simulate_invalid_response()
    
    try:
        companies = mock_api.get_companies()
    except Exception as e:
        print(f"Caught expected invalid response error: {e}")
    
    mock_api.reset_error()
    print("Mock reset to normal operation")