# unittest.mock + Faker Integration Guide for Options-Deep

## Core Concepts

Combining unittest.mock with Faker creates a powerful testing approach where you mock external dependencies while generating realistic test data. This pattern is ideal for testing business logic with varied, realistic inputs without relying on external services or databases.

### When to Use This Combination

✅ **Perfect For:**
- **Unit testing** business logic with realistic data variations
- **Testing data processing** pipelines without external dependencies
- **API testing** with varied response data
- **Error handling** with realistic but controlled data scenarios
- **Performance testing** logic with large, realistic datasets

### Installation
```bash
pip install Faker>=37.5.3  # Already in your requirements.txt
# unittest.mock is built-in with Python
```

## Pattern 1: Mock External APIs with Fake Responses

### Example: Testing NASDAQ Screener with Realistic Mock Data

```python
import unittest
from unittest.mock import patch, mock_open, MagicMock
from faker import Faker
from faker.providers import BaseProvider
import csv
import io

from src.data_sources.nasdaq.screener import load_screener_file
from src.pipelines.companies.simple_pipeline import CompanyPipeline

# Custom provider for financial data (from faker_guide.md)
class StockMarketProvider(BaseProvider):
    exchanges = ['NASDAQ', 'NYSE', 'AMEX']
    sectors = ['Technology', 'Healthcare', 'Financial', 'Consumer Discretionary']
    
    def stock_ticker(self):
        return ''.join(self.random_choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', length=4))
    
    def stock_sector(self):
        return self.random_element(self.sectors)
    
    def stock_exchange(self):
        return self.random_element(self.exchanges)

class TestNASDAQScreenerWithFakeData(unittest.TestCase):
    
    def setUp(self):
        """Set up Faker with custom providers."""
        self.fake = Faker()
        self.fake.add_provider(StockMarketProvider)
        Faker.seed(12345)  # Consistent test data
    
    def generate_fake_screener_csv(self, num_companies=5):
        """Generate realistic CSV data using Faker."""
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        
        # Write header
        writer.writerow([
            'Symbol', 'Name', 'Last Sale', 'Net Change', '% Change',
            'Market Cap', 'Country', 'IPO Year', 'Volume', 'Sector', 'Industry'
        ])
        
        # Generate realistic company rows
        for _ in range(num_companies):
            writer.writerow([
                self.fake.stock_ticker(),
                self.fake.company(),
                f"{self.fake.pyfloat(left_digits=2, right_digits=2, positive=True, min_value=1, max_value=500):.2f}",
                f"{self.fake.pyfloat(left_digits=1, right_digits=2, min_value=-10, max_value=10):.2f}",
                f"{self.fake.pyfloat(left_digits=1, right_digits=2, min_value=-5, max_value=5):.2f}%",
                str(self.fake.random_int(min=1_000_000_000, max=3_000_000_000_000)),
                'United States',
                str(self.fake.random_int(min=1980, max=2020)),
                str(self.fake.random_int(min=100_000, max=50_000_000)),
                self.fake.stock_sector(),
                self.fake.bs().title()
            ])
        
        return csv_buffer.getvalue()
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    def test_screener_loading_with_realistic_data(self, mock_file, mock_exists):
        """Test screener loading with Faker-generated realistic data."""
        # Mock file system
        mock_exists.return_value = True
        
        # Generate realistic CSV data
        fake_csv_data = self.generate_fake_screener_csv(10)
        mock_file.return_value = mock_open(read_data=fake_csv_data).return_value
        
        # Load companies
        companies = load_screener_file("fake_screener.csv")
        
        # Verify realistic data was processed
        self.assertEqual(len(companies), 10)
        
        for company in companies:
            # All companies should have realistic attributes
            self.assertIsNotNone(company.company_name)
            self.assertIn(company.exchange, ['NASDAQ', 'NYSE', 'AMEX'])
            self.assertIsNotNone(company.sector)
            self.assertGreater(company.market_cap, 0)
            self.assertEqual(len(company.ticker.symbol), 4)
    
    @patch('src.config.configuration.CONFIG')
    @patch('src.repos.equities.companies.company_repository.CompanyRepository')
    def test_pipeline_with_varied_fake_data(self, mock_repo_class, mock_config):
        """Test pipeline processing with varied realistic data."""
        # Mock configuration
        mock_config.get_equities_config.return_value = MagicMock()
        
        # Mock repository with realistic responses
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        
        # Generate realistic test companies
        test_companies = []
        for i in range(20):
            # Create variety in the data
            sector = self.fake.stock_sector()
            market_cap = self.fake.random_int(min=100_000_000, max=1_000_000_000_000)
            
            company_data = MagicMock()
            company_data.ticker.symbol = self.fake.stock_ticker()
            company_data.company_name = self.fake.company()
            company_data.sector = sector
            company_data.market_cap = market_cap
            company_data.exchange = self.fake.stock_exchange()
            
            test_companies.append(company_data)
        
        # Mock repository to return None (company doesn't exist) for varied scenarios
        def mock_find_by_symbol(symbol):
            # Simulate 20% of companies already exist
            return MagicMock(id=self.fake.random_int(1, 1000)) if self.fake.boolean(chance_of_getting_true=20) else None
        
        mock_repo.find_by_symbol.side_effect = mock_find_by_symbol
        mock_repo.create_company.side_effect = lambda c: MagicMock(id=self.fake.random_int(1, 1000))
        mock_repo.update_company.side_effect = lambda c: MagicMock(id=c.id)
        
        # Test pipeline
        pipeline = CompanyPipeline(mock_config.get_equities_config.return_value)
        result = pipeline.process_companies(test_companies)
        
        # Verify processing with realistic expectations
        total_processed = len(result.successful) + len(result.failed)
        self.assertEqual(total_processed, 20)
        
        # Should have called find_by_symbol for each company
        self.assertEqual(mock_repo.find_by_symbol.call_count, 20)
        
        # Should have some creates and some updates based on fake boolean logic
        self.assertGreater(mock_repo.create_company.call_count + mock_repo.update_company.call_count, 0)
```

## Pattern 2: Mock Database Operations with Fake Data

### Example: Testing Company Repository with Realistic Mock Responses

```python
import unittest
from unittest.mock import MagicMock, patch
from faker import Faker

from src.repos.equities.companies.company_repository import CompanyRepository

class TestCompanyRepositoryWithFakeData(unittest.TestCase):
    
    def setUp(self):
        self.fake = Faker()
        self.fake.add_provider(StockMarketProvider)
        Faker.seed(54321)  # Different seed for variety
    
    def create_fake_company_result(self):
        """Create a realistic company database result using Faker."""
        return MagicMock(
            id=self.fake.random_int(1, 10000),
            company_name=self.fake.company(),
            exchange=self.fake.stock_exchange(),
            sector=self.fake.stock_sector(),
            industry=self.fake.bs().title(),
            market_cap=self.fake.random_int(min=500_000_000, max=2_000_000_000_000),
            country='United States',
            active=True,
            tickers=[MagicMock(symbol=self.fake.stock_ticker())]
        )
    
    @patch('src.config.database.create_engine')
    @patch('sqlalchemy.orm.sessionmaker')
    def test_find_by_sector_with_realistic_results(self, mock_sessionmaker, mock_create_engine):
        """Test finding companies by sector with realistic mock data."""
        # Create mock session
        mock_session = MagicMock()
        mock_sessionmaker.return_value.return_value = mock_session
        
        # Generate realistic companies for Technology sector
        tech_companies = [self.create_fake_company_result() for _ in range(5)]
        for company in tech_companies:
            company.sector = "Technology"
        
        # Mock query chain
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = tech_companies
        
        # Test repository
        repo = CompanyRepository()
        repo.session = mock_session
        
        result = repo.find_by_sector("Technology")
        
        # Verify realistic results
        self.assertEqual(len(result), 5)
        for company in result:
            self.assertEqual(company.sector, "Technology")
            self.assertIsInstance(company.company_name, str)
            self.assertGreater(company.market_cap, 0)
            self.assertTrue(len(company.tickers) > 0)
    
    def test_company_statistics_with_varied_data(self):
        """Test company statistics with varied fake data."""
        mock_session = MagicMock()
        
        # Generate realistic sector statistics
        sectors = ['Technology', 'Healthcare', 'Financial', 'Energy']
        mock_stats = []
        
        for sector in sectors:
            stats = {
                'sector': sector,
                'company_count': self.fake.random_int(10, 200),
                'avg_market_cap': self.fake.random_int(5_000_000_000, 500_000_000_000),
                'total_volume': self.fake.random_int(1_000_000, 100_000_000)
            }
            mock_stats.append(MagicMock(**stats))
        
        # Mock query execution
        mock_session.execute.return_value.fetchall.return_value = mock_stats
        
        # Test repository method
        repo = CompanyRepository()
        repo.session = mock_session
        
        stats = repo.get_sector_statistics()
        
        # Verify realistic statistics
        self.assertEqual(len(stats), 4)
        for stat in stats:
            self.assertIn(stat.sector, sectors)
            self.assertGreater(stat.company_count, 0)
            self.assertGreater(stat.avg_market_cap, 0)
```

## Pattern 3: Mock Configuration with Fake Environment Data

### Example: Testing Configuration Manager with Realistic Settings

```python
import unittest
from unittest.mock import patch, mock_open, MagicMock
from faker import Faker
import json

from src.config.configuration import ConfigurationManager

class TestConfigurationWithFakeData(unittest.TestCase):
    
    def setUp(self):
        self.fake = Faker()
        Faker.seed(98765)
    
    def generate_fake_database_config(self):
        """Generate realistic database configuration using Faker."""
        return {
            "databases": {
                "equities": {
                    "host": self.fake.hostname(),
                    "port": self.fake.random_int(5432, 5439),
                    "database": f"options_deep_equities_{self.fake.word()}",
                    "username": self.fake.user_name()
                },
                "algorithm": {
                    "host": self.fake.hostname(),
                    "port": self.fake.random_int(5432, 5439),
                    "database": f"options_deep_algorithm_{self.fake.word()}",
                    "username": self.fake.user_name()
                }
            },
            "api_settings": {
                "timeout": self.fake.random_int(5, 30),
                "retry_count": self.fake.random_int(1, 5),
                "rate_limit": self.fake.random_int(100, 1000)
            }
        }
    
    @patch.dict('os.environ', {
        'ENVIRONMENT': 'test',
        'OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD': 'test_password_123'
    })
    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    def test_configuration_loading_with_fake_settings(self, mock_file, mock_exists):
        """Test configuration loading with realistic fake settings."""
        # Mock file system
        mock_exists.return_value = True
        
        # Generate realistic configuration
        fake_config = self.generate_fake_database_config()
        mock_file.return_value = mock_open(read_data=json.dumps(fake_config)).return_value
        
        # Test configuration manager
        config_manager = ConfigurationManager()
        db_config = config_manager.get_equities_config()
        
        # Verify realistic configuration
        self.assertEqual(db_config.password, 'test_password_123')
        self.assertIsInstance(db_config.host, str)
        self.assertIsInstance(db_config.port, int)
        self.assertIn('options_deep_equities', db_config.database)
        self.assertIsInstance(db_config.username, str)
    
    @patch.dict('os.environ', {})  # Empty environment
    @patch('pathlib.Path.exists')
    def test_missing_password_with_realistic_config(self, mock_exists):
        """Test error handling with realistic but incomplete configuration."""
        mock_exists.return_value = True
        
        with patch('builtins.open', mock_open(read_data='{"databases": {}}')):
            config_manager = ConfigurationManager()
            
            # Should raise ValueError for missing password
            with self.assertRaises(ValueError) as context:
                config_manager.get_equities_config()
            
            self.assertIn("password", str(context.exception))
```

## Pattern 4: Mock File Operations with Realistic File Content

### Example: Testing CSV Processing with Generated Content

```python
import unittest
from unittest.mock import patch, mock_open
from faker import Faker
import tempfile
import csv
import io

from src.data_sources.nasdaq.screener import load_screener_files_from_directory

class TestFileProcessingWithFakeContent(unittest.TestCase):
    
    def setUp(self):
        self.fake = Faker()
        self.fake.add_provider(StockMarketProvider)
        Faker.seed(11111)
    
    def generate_realistic_screener_files(self, num_files=3, companies_per_file=10):
        """Generate multiple realistic screener files."""
        files_data = {}
        
        for file_num in range(num_files):
            date_str = self.fake.date_this_year().strftime("%m_%d_%Y")
            filename = f"nasdaq_screener_{date_str}.csv"
            
            # Generate CSV content
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            
            # Header
            writer.writerow([
                'Symbol', 'Name', 'Last Sale', 'Net Change', '% Change',
                'Market Cap', 'Country', 'IPO Year', 'Volume', 'Sector', 'Industry'
            ])
            
            # Generate companies with some overlap and variation
            for _ in range(companies_per_file):
                writer.writerow([
                    self.fake.stock_ticker(),
                    self.fake.company(),
                    f"{self.fake.pyfloat(left_digits=2, right_digits=2, positive=True, min_value=1, max_value=1000):.2f}",
                    f"{self.fake.pyfloat(left_digits=1, right_digits=2, min_value=-20, max_value=20):.2f}",
                    f"{self.fake.pyfloat(left_digits=1, right_digits=2, min_value=-10, max_value=10):.2f}%",
                    str(self.fake.random_int(min=100_000_000, max=5_000_000_000_000)),
                    'United States',
                    str(self.fake.random_int(min=1950, max=2023)),
                    str(self.fake.random_int(min=10_000, max=200_000_000)),
                    self.fake.stock_sector(),
                    self.fake.bs().title()
                ])
            
            files_data[filename] = csv_buffer.getvalue()
        
        return files_data
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    @patch('builtins.open')
    def test_multiple_screener_files_processing(self, mock_file, mock_glob, mock_exists):
        """Test processing multiple screener files with realistic content."""
        # Mock directory exists
        mock_exists.return_value = True
        
        # Generate realistic file data
        files_data = self.generate_realistic_screener_files(num_files=3, companies_per_file=15)
        filenames = list(files_data.keys())
        
        # Mock glob to return file paths
        mock_paths = [MagicMock(name=filename) for filename in filenames]
        mock_glob.return_value = mock_paths
        
        # Mock file opening - return different content for each file
        def mock_open_side_effect(filepath, *args, **kwargs):
            filename = filepath.name
            if filename in files_data:
                return mock_open(read_data=files_data[filename]).return_value
            return mock_open(read_data="").return_value
        
        mock_file.side_effect = mock_open_side_effect
        
        # Test processing
        companies = load_screener_files_from_directory("/fake/directory")
        
        # Verify realistic results
        self.assertEqual(len(companies), 45)  # 3 files × 15 companies each
        
        # Verify data variety and realism
        sectors_found = set(company.sector for company in companies if company.sector)
        exchanges_found = set(company.exchange for company in companies)
        
        self.assertGreater(len(sectors_found), 1)  # Should have variety
        self.assertTrue(all(exchange in ['NASDAQ', 'NYSE', 'AMEX'] for exchange in exchanges_found))
        
        # All companies should have realistic market caps
        market_caps = [company.market_cap for company in companies if company.market_cap]
        self.assertTrue(all(cap >= 100_000_000 for cap in market_caps))  # At least 100M
        self.assertTrue(all(cap <= 5_000_000_000_000 for cap in market_caps))  # At most 5T
```

## Pattern 5: Mock API Responses with Realistic Data Variations

### Example: Testing Error Handling with Realistic Failure Scenarios

```python
import unittest
from unittest.mock import patch, MagicMock
from faker import Faker
import requests

class TestErrorHandlingWithRealisticScenarios(unittest.TestCase):
    
    def setUp(self):
        self.fake = Faker()
        Faker.seed(77777)
    
    def generate_realistic_api_errors(self):
        """Generate realistic API error scenarios."""
        error_scenarios = [
            {
                'status_code': 429,
                'error_type': 'RateLimitExceeded',
                'message': f'Rate limit exceeded. Try again in {self.fake.random_int(1, 60)} seconds.',
                'retry_after': self.fake.random_int(1, 300)
            },
            {
                'status_code': 500,
                'error_type': 'InternalServerError', 
                'message': 'Internal server error occurred',
                'incident_id': self.fake.uuid4()
            },
            {
                'status_code': 503,
                'error_type': 'ServiceUnavailable',
                'message': 'Service temporarily unavailable',
                'estimated_recovery': self.fake.date_time_between(start_date='+1h', end_date='+24h').isoformat()
            },
            {
                'status_code': 401,
                'error_type': 'Unauthorized',
                'message': 'Invalid API key or expired token',
                'expires_at': self.fake.date_time_between(start_date='-1d', end_date='+30d').isoformat()
            }
        ]
        return self.fake.random_element(error_scenarios)
    
    @patch('requests.get')
    def test_api_error_handling_with_varied_failures(self, mock_get):
        """Test API error handling with realistic failure scenarios."""
        
        # Generate multiple realistic error scenarios
        error_scenarios = [self.generate_realistic_api_errors() for _ in range(5)]
        
        for scenario in error_scenarios:
            with self.subTest(error_type=scenario['error_type']):
                # Mock response
                mock_response = MagicMock()
                mock_response.status_code = scenario['status_code']
                mock_response.json.return_value = {
                    'error': scenario['error_type'],
                    'message': scenario['message']
                }
                mock_response.raise_for_status.side_effect = requests.HTTPError(scenario['message'])
                mock_get.return_value = mock_response
                
                # Test your API client error handling
                # (This would test your actual API client implementation)
                
                # Verify appropriate error handling
                mock_get.assert_called()
                self.assertEqual(mock_response.status_code, scenario['status_code'])
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    @patch('requests.get')
    def test_retry_logic_with_realistic_patterns(self, mock_get, mock_sleep):
        """Test retry logic with realistic success/failure patterns."""
        
        # Realistic retry scenario: fail twice, then succeed
        responses = [
            # First call: rate limited
            MagicMock(
                status_code=429,
                headers={'Retry-After': str(self.fake.random_int(1, 10))},
                raise_for_status=MagicMock(side_effect=requests.HTTPError("Rate limited"))
            ),
            # Second call: server error
            MagicMock(
                status_code=500,
                raise_for_status=MagicMock(side_effect=requests.HTTPError("Server error"))
            ),
            # Third call: success
            MagicMock(
                status_code=200,
                json=MagicMock(return_value={
                    'companies': [
                        {
                            'symbol': self.fake.stock_ticker(),
                            'name': self.fake.company(),
                            'price': float(self.fake.pydecimal(left_digits=3, right_digits=2, positive=True)),
                            'sector': self.fake.stock_sector()
                        }
                        for _ in range(10)
                    ]
                })
            )
        ]
        
        mock_get.side_effect = responses
        
        # Test your retry logic here
        # (This would test your actual API client with retry logic)
        
        # Verify retry behavior
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # Should sleep between retries
```

## Type-Safe Mocking with unittest.mock + Faker

### Using `spec` and `autospec` for Type Enforcement

When working with typed Python code, you can enforce type safety in your mocks using `spec` and `autospec`:

```python
from unittest.mock import MagicMock, create_autospec
from typing import List, Optional
from src.repos.equities.companies.company_repository import CompanyRepository
from src.data_sources.models.company import Company

class TestWithTypeSafety(unittest.TestCase):
    
    def setUp(self):
        self.fake = Faker()
        self.fake.add_provider(StockMarketProvider)
    
    def test_repository_with_autospec(self):
        """Use autospec to enforce repository interface."""
        
        # Create type-safe mock that respects CompanyRepository interface
        mock_repo = create_autospec(CompanyRepository, spec_set=True)
        
        # Generate realistic company with Faker
        company_data = {
            'symbol': self.fake.stock_ticker(),
            'company_name': self.fake.company(),
            'sector': self.fake.stock_sector(),
            'market_cap': self.fake.market_cap()
        }
        
        # Mock must match the actual method signature
        mock_company = MagicMock(spec=Company)
        mock_company.company_name = company_data['company_name']
        mock_company.sector = company_data['sector']
        
        # This enforces the correct method signature
        mock_repo.find_by_symbol.return_value = mock_company
        
        # Test your service
        result = mock_repo.find_by_symbol("AAPL")
        
        # Verify type-safe interaction
        self.assertEqual(result.company_name, company_data['company_name'])
        
        # This would raise AttributeError if method doesn't exist
        mock_repo.find_by_symbol.assert_called_once_with("AAPL")
    
    def test_typed_mock_with_faker_responses(self):
        """Create typed mocks with Faker-generated responses."""
        
        from src.database.equities.tables.company import Company as CompanyDB
        
        # Create spec'd mock for database model
        mock_db_company = MagicMock(spec=CompanyDB)
        
        # Use Faker to populate realistic attributes
        mock_db_company.id = self.fake.random_int(min=1, max=10000)
        mock_db_company.company_name = self.fake.company()
        mock_db_company.sector = self.fake.stock_sector()
        mock_db_company.market_cap = self.fake.market_cap()
        mock_db_company.active = True
        mock_db_company.created_at = self.fake.date_time_this_year()
        
        # Mock session with autospec
        mock_session = create_autospec('sqlalchemy.orm.Session')
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_db_company
        
        # Test with type-safe mocks
        repo = CompanyRepository()
        repo.session = mock_session
        
        result = repo.find_by_symbol("AAPL")
        
        # Verify typed attributes
        self.assertIsInstance(result.id, int)
        self.assertIsInstance(result.company_name, str)
        self.assertIsInstance(result.active, bool)

### Type Hints for Mock Setup

```python
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock

if TYPE_CHECKING:
    from src.repos.equities.companies.company_repository import CompanyRepository

def create_typed_company_repo_mock() -> 'CompanyRepository':
    """Create a properly typed mock repository."""
    
    mock_repo = create_autospec(CompanyRepository, spec_set=True)
    
    # Type checkers will understand this is a CompanyRepository
    return cast('CompanyRepository', mock_repo)

class TestWithTypedMocks(unittest.TestCase):
    
    def setUp(self):
        self.fake = Faker()
        self.fake.add_provider(StockMarketProvider)
        self.mock_repo = create_typed_company_repo_mock()
    
    def test_with_proper_typing(self):
        """Test with properly typed mocks and Faker data."""
        
        # Generate realistic data with Faker
        fake_companies = [
            MagicMock(
                spec=Company,
                company_name=self.fake.company(),
                sector=self.fake.stock_sector(),
                market_cap=self.fake.market_cap()
            )
            for _ in range(5)
        ]
        
        # Configure typed mock
        self.mock_repo.find_by_sector.return_value = fake_companies
        
        # Type checkers understand the return type
        result = self.mock_repo.find_by_sector("Technology")
        
        # Type-safe assertions
        self.assertEqual(len(result), 5)
        for company in result:
            self.assertIsInstance(company.company_name, str)
            self.assertGreater(company.market_cap, 0)
```

### Handling Optional Types with Mocks

```python
def test_optional_types_with_faker(self):
    """Handle Optional return types in mocked methods."""
    
    from typing import Optional
    from src.data_sources.models.company import Company
    
    # Mock method that returns Optional[Company]
    mock_repo = create_autospec(CompanyRepository)
    
    # Use Faker to decide if company exists (80% chance)
    company_exists = self.fake.boolean(chance_of_getting_true=80)
    
    if company_exists:
        # Return realistic company
        mock_company = MagicMock(spec=Company)
        mock_company.company_name = self.fake.company()
        mock_company.sector = self.fake.stock_sector()
        mock_repo.find_by_symbol.return_value = mock_company
    else:
        # Return None (company doesn't exist)
        mock_repo.find_by_symbol.return_value = None
    
    # Test code that handles Optional[Company]
    result = mock_repo.find_by_symbol("TEST")
    
    if result is not None:
        self.assertIsInstance(result.company_name, str)
    else:
        self.assertIsNone(result)
```

### Type-Safe Error Simulation

```python
def test_typed_exceptions_with_faker(self):
    """Generate type-safe exceptions with Faker content."""
    
    from src.utils.exceptions import DataSourceError, ValidationError
    
    mock_api = create_autospec('src.external_api.MarketDataAPI')
    
    # Use Faker to generate realistic error scenarios
    error_scenarios = [
        DataSourceError(f"API rate limit exceeded: {self.fake.sentence()}"),
        ValidationError(f"Invalid ticker format: {self.fake.stock_ticker()}"),
        ConnectionError(f"Connection timeout after {self.fake.random_int(1, 30)}s")
    ]
    
    # Mock raises realistic, type-safe exceptions
    mock_api.get_company_data.side_effect = self.fake.random_element(error_scenarios)
    
    # Test exception handling
    with self.assertRaises((DataSourceError, ValidationError, ConnectionError)):
        mock_api.get_company_data("AAPL")
```

## Best Practices for unittest.mock + Faker

### 1. Consistent Seeding for Reproducible Tests

```python
class TestWithConsistentData(unittest.TestCase):
    
    def setUp(self):
        # Always seed Faker for consistent test data
        Faker.seed(12345)
        self.fake = Faker()
        self.fake.add_provider(StockMarketProvider)
    
    def test_consistent_behavior(self):
        # This will generate the same data every test run
        company_name = self.fake.company()
        ticker = self.fake.stock_ticker()
        
        # Test logic here...
```

### 2. Separate Data Generation from Test Logic

```python
class CompanyTestDataGenerator:
    """Separate class for generating test data."""
    
    def __init__(self, seed=12345):
        self.fake = Faker()
        self.fake.add_provider(StockMarketProvider)
        Faker.seed(seed)
    
    def create_company_batch(self, count=10, sector=None):
        """Generate a batch of realistic companies."""
        companies = []
        for _ in range(count):
            company = MagicMock(
                ticker=MagicMock(symbol=self.fake.stock_ticker()),
                company_name=self.fake.company(),
                sector=sector or self.fake.stock_sector(),
                market_cap=self.fake.random_int(min=100_000_000, max=1_000_000_000_000)
            )
            companies.append(company)
        return companies

# Use in tests
class TestCompanyProcessing(unittest.TestCase):
    
    def setUp(self):
        self.data_generator = CompanyTestDataGenerator()
    
    def test_sector_filtering(self):
        tech_companies = self.data_generator.create_company_batch(
            count=20, 
            sector="Technology"
        )
        # Test logic with consistent, realistic data
```

### 3. Mock External Dependencies, Generate Internal Data

```python
@patch('external_api.fetch_data')  # Mock external dependency
@patch('src.config.CONFIG.get_database_config')  # Mock configuration
def test_data_processing_pipeline(self, mock_config, mock_api):
    """Test processing pipeline with mocked externals and fake internals."""
    
    # Mock external API response structure, but use Faker for content
    fake_api_response = {
        'companies': [
            {
                'symbol': self.fake.stock_ticker(),
                'name': self.fake.company(),
                'sector': self.fake.stock_sector(),
                'market_cap': self.fake.random_int(min=1_000_000_000, max=100_000_000_000)
            }
            for _ in range(50)  # Realistic batch size
        ],
        'timestamp': self.fake.date_time_this_year().isoformat(),
        'total_count': 50
    }
    
    mock_api.return_value = fake_api_response
    mock_config.return_value = MagicMock()  # Mock config, but not the data
    
    # Test your pipeline
    # The external calls are mocked, but the data is realistic
```

## When to Use unittest.mock + Faker

✅ **Perfect For:**
- **Unit testing** business logic with realistic data variations
- **Testing data validation** with diverse, realistic inputs
- **API testing** without external dependencies
- **Error handling** with realistic failure scenarios
- **Performance testing** logic with large, varied datasets

✅ **Benefits:**
- **Isolation**: Tests don't depend on external services
- **Speed**: Fast execution with realistic data
- **Reliability**: Consistent, reproducible test results
- **Coverage**: Easy to test edge cases with varied data
- **Realism**: More realistic than static test data

❌ **Don't Use For:**
- **Integration testing** (use pytest-postgresql instead)
- **Testing actual database operations** 
- **When you need exact, specific data values**
- **Testing external API contracts** (use contract testing)

## Running Tests

```bash
# Run unittest.mock + Faker tests
python -m unittest discover tests/unit/ -v

# Run specific test file
python -m unittest tests.unit.test_mock_faker_integration -v

# Run with coverage
coverage run -m unittest discover tests/unit/
coverage report
```

This combination provides powerful, flexible testing with realistic data while maintaining complete control over external dependencies.