# unittest.mock + Factory Boy Integration Guide for Options-Deep

## Core Concepts

Combining unittest.mock with Factory Boy creates a powerful testing strategy where you mock external dependencies while using Factory Boy to generate complex, related test objects. This approach excels at testing business logic with realistic, structured data relationships.

### When to Use This Combination

✅ **Perfect For:**
- **Unit testing** business logic with complex object relationships
- **Testing data processing** pipelines with realistic object hierarchies
- **Repository pattern testing** without actual database calls
- **Service layer testing** with mocked dependencies but realistic domain objects
- **Integration testing** of components with controlled external dependencies

### Installation
```bash
pip install factory_boy
# unittest.mock is built-in with Python
```

## Pattern 1: Mock Database Layer with Factory Boy Objects

### Example: Testing Company Repository with Factory-Generated Objects

```python
import unittest
from unittest.mock import MagicMock, patch
import factory
from factory.alchemy import SQLAlchemyModelFactory

from src.repos.equities.companies.company_repository import CompanyRepository
from src.database.equities.tables.company import Company
from src.database.equities.tables.ticker import Ticker

# Factory definitions (can be in separate test_factories.py file)
class MockCompanyFactory(SQLAlchemyModelFactory):
    """Factory for creating Company objects for testing."""
    
    class Meta:
        model = Company
        sqlalchemy_session = None  # We'll mock the session
    
    id = factory.Sequence(lambda n: n + 1)
    company_name = factory.Faker('company')
    exchange = factory.Iterator(['NASDAQ', 'NYSE', 'AMEX'])
    sector = factory.Iterator([
        'Technology', 'Healthcare', 'Financial', 'Consumer Discretionary'
    ])
    industry = factory.Faker('bs')
    market_cap = factory.Faker('random_int', min=1_000_000_000, max=1_000_000_000_000)
    country = 'United States'
    active = True
    source = 'TEST'

class MockTickerFactory(SQLAlchemyModelFactory):
    """Factory for creating Ticker objects for testing."""
    
    class Meta:
        model = Ticker
        sqlalchemy_session = None
    
    id = factory.Sequence(lambda n: n + 1)
    symbol = factory.Faker('lexify', text='????', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    company = factory.SubFactory(MockCompanyFactory)
    primary_ticker = True

class TestCompanyRepositoryWithFactoryObjects(unittest.TestCase):
    
    def setUp(self):
        """Set up consistent factory data."""
        factory.Faker.seed(12345)
    
    @patch('src.repos.equities.companies.company_repository.create_engine')
    @patch('src.repos.equities.companies.company_repository.sessionmaker')
    def test_find_by_sector_with_factory_objects(self, mock_sessionmaker, mock_create_engine):
        """Test repository method with Factory Boy generated objects."""
        
        # Create realistic companies using Factory Boy
        tech_companies = MockCompanyFactory.build_batch(5, sector="Technology")
        healthcare_companies = MockCompanyFactory.build_batch(3, sector="Healthcare")
        all_companies = tech_companies + healthcare_companies
        
        # Mock database session
        mock_session = MagicMock()
        mock_sessionmaker.return_value.return_value = mock_session
        
        # Mock query chain to return Factory Boy objects
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = tech_companies  # Return only tech companies
        
        # Test repository
        repo = CompanyRepository()
        repo.session = mock_session
        
        result = repo.find_by_sector("Technology")
        
        # Verify Factory Boy objects were returned correctly
        self.assertEqual(len(result), 5)
        for company in result:
            self.assertEqual(company.sector, "Technology")
            self.assertIsInstance(company, Company)
            self.assertTrue(hasattr(company, 'company_name'))
            self.assertGreater(company.market_cap, 0)
        
        # Verify database interaction
        mock_session.query.assert_called_once_with(Company)
        mock_query.filter.assert_called_once()
    
    def test_repository_create_with_factory_input(self):
        """Test repository create method with Factory Boy input."""
        
        # Create company data using Factory Boy
        company_data = MockCompanyFactory.build()
        
        # Mock session and database response
        mock_session = MagicMock()
        
        # Mock the database returning the created company with an ID
        created_company = MockCompanyFactory.build(
            id=123,
            company_name=company_data.company_name,
            sector=company_data.sector
        )
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.side_effect = lambda obj: setattr(obj, 'id', 123)
        
        # Test repository
        repo = CompanyRepository()
        repo.session = mock_session
        
        # Convert to data model for repository input
        from src.data_sources.models.company import Company as CompanyDataModel
        from src.data_sources.models.ticker import Ticker as TickerDataModel
        
        ticker_data = TickerDataModel(
            symbol=company_data.tickers[0].symbol if company_data.tickers else "TEST",
            company_id=None
        )
        
        company_data_model = CompanyDataModel(
            id=None,
            ticker=ticker_data,
            company_name=company_data.company_name,
            exchange=company_data.exchange,
            sector=company_data.sector,
            industry=company_data.industry,
            country=company_data.country,
            market_cap=company_data.market_cap,
            source=company_data.source
        )
        
        result = repo.create_company(company_data_model)
        
        # Verify repository interactions
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Verify result has expected attributes from Factory
        self.assertIsNotNone(result)
        self.assertEqual(result.company_name, company_data.company_name)
```

## Pattern 2: Mock External APIs with Factory Boy Response Objects

### Example: Testing Data Pipeline with Complex Object Relationships

```python
import unittest
from unittest.mock import patch, MagicMock
import factory
from datetime import datetime, timedelta

from src.pipelines.companies.simple_pipeline import CompanyPipeline
from src.data_sources.models.company import Company as CompanyDataModel
from src.data_sources.models.ticker import Ticker as TickerDataModel

# Enhanced factories with relationships
class CompanyDataModelFactory(factory.Factory):
    """Factory for Company data models with realistic relationships."""
    
    class Meta:
        model = CompanyDataModel
    
    id = None
    company_name = factory.Faker('company')
    exchange = factory.Iterator(['NASDAQ', 'NYSE', 'AMEX'])
    sector = factory.Iterator([
        'Technology', 'Healthcare', 'Financial', 'Consumer Discretionary',
        'Consumer Staples', 'Energy', 'Industrials'
    ])
    industry = factory.LazyAttribute(lambda obj: f"{obj.sector} - {factory.Faker('bs').generate()}")
    country = 'United States'
    market_cap = factory.Faker('random_int', min=500_000_000, max=2_000_000_000_000)
    description = factory.Faker('text', max_nb_chars=500)
    active = True
    source = 'PIPELINE_TEST'
    
    # Related ticker
    ticker = factory.SubFactory('tests.factories.TickerDataModelFactory')

class TickerDataModelFactory(factory.Factory):
    """Factory for Ticker data models."""
    
    class Meta:
        model = TickerDataModel
    
    symbol = factory.Faker('lexify', text='????', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    company_id = None

class CompanyPipelineTestCase(unittest.TestCase):
    
    def setUp(self):
        factory.Faker.seed(54321)
    
    @patch('src.config.configuration.CONFIG')
    @patch('src.repos.equities.companies.company_repository.CompanyRepository')
    def test_pipeline_with_mixed_scenarios(self, mock_repo_class, mock_config):
        """Test pipeline with varied scenarios using Factory Boy objects."""
        
        # Mock configuration
        mock_db_config = MagicMock()
        mock_config.get_equities_config.return_value = mock_db_config
        
        # Create repository mock
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        
        # Generate realistic test data using Factory Boy
        # Mix of new companies, existing companies, and companies with issues
        new_companies = CompanyDataModelFactory.build_batch(10)  # Should be created
        existing_companies = CompanyDataModelFactory.build_batch(5)  # Should be updated
        duplicate_companies = CompanyDataModelFactory.build_batch(2)  # Should cause conflicts
        
        all_test_companies = new_companies + existing_companies + duplicate_companies
        
        # Mock repository responses based on company type
        def mock_find_by_symbol(symbol):
            # Return existing company for "existing" companies
            for company in existing_companies:
                if company.ticker.symbol == symbol:
                    return MockCompanyFactory.build(
                        id=factory.Faker('random_int', min=1, max=1000).generate(),
                        company_name=company.company_name,
                        sector=company.sector
                    )
            return None  # New companies don't exist
        
        def mock_create_company(company_data):
            # Simulate successful creation for new companies
            if company_data in new_companies:
                return MockCompanyFactory.build(
                    id=factory.Faker('random_int', min=1001, max=2000).generate(),
                    company_name=company_data.company_name,
                    sector=company_data.sector
                )
            else:
                # Simulate creation failure for duplicates
                raise Exception(f"Duplicate key violation for {company_data.ticker.symbol}")
        
        def mock_update_company(company_data):
            # Simulate successful updates
            return MockCompanyFactory.build(
                id=factory.Faker('random_int', min=1, max=1000).generate(),
                company_name=company_data.company_name,
                sector=company_data.sector,
                market_cap=company_data.market_cap
            )
        
        # Configure mocks
        mock_repo.find_by_symbol.side_effect = mock_find_by_symbol
        mock_repo.create_company.side_effect = mock_create_company
        mock_repo.update_company.side_effect = mock_update_company
        
        # Test pipeline
        pipeline = CompanyPipeline(mock_db_config)
        result = pipeline.process_companies(all_test_companies)
        
        # Verify realistic processing results
        self.assertEqual(len(result.successful), 15)  # 10 new + 5 existing
        self.assertEqual(len(result.failed), 2)       # 2 duplicates failed
        
        # Verify repository calls match our Factory-generated data
        self.assertEqual(mock_repo.find_by_symbol.call_count, 17)  # Called for each company
        self.assertEqual(mock_repo.create_company.call_count, 12)  # 10 new + 2 failed attempts
        self.assertEqual(mock_repo.update_company.call_count, 5)   # 5 existing
        
        # Verify successful results have expected attributes from Factory
        for successful_company in result.successful:
            self.assertIsInstance(successful_company, Company)
            self.assertIsNotNone(successful_company.company_name)
            self.assertIn(successful_company.sector, [
                'Technology', 'Healthcare', 'Financial', 'Consumer Discretionary',
                'Consumer Staples', 'Energy', 'Industrials'
            ])
```

## Pattern 3: Mock Configuration with Factory Boy Settings Objects

### Example: Testing Configuration-Dependent Services

```python
import unittest
from unittest.mock import patch, MagicMock
import factory

from src.config.models.database import DatabaseConfig
from src.config.models.equities import EquitiesConfig

class DatabaseConfigFactory(factory.Factory):
    """Factory for database configuration objects."""
    
    class Meta:
        model = DatabaseConfig
    
    host = factory.Faker('hostname')
    port = factory.Iterator([5432, 5433, 5434, 5435])
    database = factory.LazyAttribute(lambda obj: f"options_deep_{factory.Faker('word').generate()}")
    username = factory.Faker('user_name')
    password = factory.Faker('password')
    environment = factory.Iterator(['local', 'dev', 'staging', 'prod'])

class EquitiesConfigFactory(factory.Factory):
    """Factory for equities configuration objects."""
    
    class Meta:
        model = EquitiesConfig
    
    # Use subfactory for database config
    database = factory.SubFactory(DatabaseConfigFactory)
    
    # Add equities-specific settings
    batch_size = factory.Faker('random_int', min=100, max=1000)
    timeout_seconds = factory.Faker('random_int', min=30, max=300)
    retry_attempts = factory.Faker('random_int', min=1, max=5)

class TestServiceWithFactoryConfigurations(unittest.TestCase):
    
    def setUp(self):
        factory.Faker.seed(99999)
    
    @patch('src.config.configuration.CONFIG.get_equities_config')
    def test_service_with_various_configurations(self, mock_config):
        """Test service behavior with different configuration scenarios."""
        
        # Generate different configuration scenarios
        configs = [
            EquitiesConfigFactory.build(environment='local', batch_size=100),
            EquitiesConfigFactory.build(environment='prod', batch_size=1000),
            EquitiesConfigFactory.build(environment='dev', timeout_seconds=60)
        ]
        
        for config in configs:
            with self.subTest(environment=config.environment):
                mock_config.return_value = config
                
                # Test your service with this configuration
                from src.pipelines.companies.simple_pipeline import CompanyPipeline
                
                pipeline = CompanyPipeline(config)
                
                # Verify service uses configuration correctly
                # This would depend on your actual service implementation
                self.assertIsNotNone(pipeline)
                
                # Verify configuration attributes are realistic
                self.assertIsInstance(config.batch_size, int)
                self.assertGreater(config.batch_size, 0)
                self.assertIsInstance(config.database.host, str)
                self.assertIn(config.environment, ['local', 'dev', 'staging', 'prod'])
```

## Pattern 4: Mock File Operations with Factory Boy File Content Objects

### Example: Testing File Processing with Structured Data

```python
import unittest
from unittest.mock import patch, mock_open, MagicMock
import factory
import json
import csv
import io

# Factory for file content structures
class NASDAQCompanyDataFactory(factory.DictFactory):
    """Factory for NASDAQ company data dictionaries."""
    
    Symbol = factory.Faker('lexify', text='????', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    Name = factory.Faker('company')
    LastSale = factory.LazyFunction(lambda: f"{factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True).generate():.2f}")
    NetChange = factory.LazyFunction(lambda: f"{factory.Faker('pydecimal', left_digits=2, right_digits=2).generate():.2f}")
    PercentChange = factory.LazyFunction(lambda: f"{factory.Faker('pydecimal', left_digits=1, right_digits=2, min_value=-10, max_value=10).generate():.2f}%")
    MarketCap = factory.Faker('random_int', min=1_000_000_000, max=3_000_000_000_000)
    Country = 'United States'
    IPOYear = factory.Faker('random_int', min=1980, max=2023)
    Volume = factory.Faker('random_int', min=100_000, max=100_000_000)
    Sector = factory.Iterator([
        'Technology', 'Healthcare', 'Financial Services', 'Consumer Discretionary'
    ])
    Industry = factory.Faker('bs')

class CompanyFileDataFactory(factory.Factory):
    """Factory for complete company file structures."""
    
    class Meta:
        model = dict
    
    companies = factory.LazyFunction(lambda: NASDAQCompanyDataFactory.build_batch(50))
    metadata = factory.LazyFunction(lambda: {
        'generated_at': factory.Faker('iso8601').generate(),
        'source': 'NASDAQ',
        'total_count': 50,
        'file_version': '1.0'
    })

class TestFileProcessingWithFactoryContent(unittest.TestCase):
    
    def setUp(self):
        factory.Faker.seed(88888)
    
    def create_csv_content_from_factory_data(self, companies_data):
        """Convert Factory Boy data to CSV format."""
        if not companies_data:
            return ""
        
        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=companies_data[0].keys())
        writer.writeheader()
        writer.writerows(companies_data)
        return csv_buffer.getvalue()
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    def test_csv_processing_with_factory_content(self, mock_file, mock_exists):
        """Test CSV processing with Factory Boy generated content."""
        
        # Generate realistic NASDAQ data using Factory Boy
        nasdaq_data = NASDAQCompanyDataFactory.build_batch(25)
        csv_content = self.create_csv_content_from_factory_data(nasdaq_data)
        
        # Mock file system
        mock_exists.return_value = True
        mock_file.return_value = mock_open(read_data=csv_content).return_value
        
        # Test file loading
        from src.data_sources.nasdaq.screener import load_screener_file
        
        companies = load_screener_file("test_file.csv")
        
        # Verify Factory-generated data was processed correctly
        self.assertEqual(len(companies), 25)
        
        for i, company in enumerate(companies):
            original_data = nasdaq_data[i]
            
            self.assertEqual(company.ticker.symbol, original_data['Symbol'])
            self.assertEqual(company.company_name, original_data['Name'])
            self.assertEqual(company.sector, original_data['Sector'])
            self.assertEqual(company.market_cap, int(original_data['MarketCap']))
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    def test_json_processing_with_nested_factory_objects(self, mock_file, mock_exists):
        """Test JSON processing with complex Factory Boy objects."""
        
        # Generate complete file structure using Factory Boy
        file_data = CompanyFileDataFactory.build()
        json_content = json.dumps(file_data, default=str)
        
        # Mock file system
        mock_exists.return_value = True
        mock_file.return_value = mock_open(read_data=json_content).return_value
        
        # Test your JSON processing logic
        with open("test_file.json", "r") as f:
            loaded_data = json.load(f)
        
        # Verify Factory-generated structure
        self.assertIn('companies', loaded_data)
        self.assertIn('metadata', loaded_data)
        self.assertEqual(len(loaded_data['companies']), 50)
        
        # Verify each company has expected Factory-generated attributes
        for company_data in loaded_data['companies']:
            self.assertIn('Symbol', company_data)
            self.assertIn('Name', company_data)
            self.assertIn('Sector', company_data)
            self.assertIn('MarketCap', company_data)
            self.assertIsInstance(company_data['MarketCap'], int)
            self.assertGreater(company_data['MarketCap'], 1_000_000_000)
```

## Pattern 5: Mock Services with Factory Boy Domain Objects

### Example: Testing Business Logic with Complex Object Graphs

```python
import unittest
from unittest.mock import MagicMock, patch
import factory
from datetime import datetime, timedelta

from src.database.equities.tables.ticker_history import TickerHistory

class TickerHistoryFactory(factory.Factory):
    """Factory for ticker price history objects."""
    
    class Meta:
        model = dict  # Using dict for simplicity, could be actual model
    
    ticker_id = factory.Sequence(lambda n: n + 1)
    company_id = factory.LazyAttribute(lambda obj: obj.ticker_id)  # Simple relationship
    price_date = factory.Faker('date_between', start_date='-1y', end_date='today')
    
    # Generate realistic OHLC data
    close_price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True, 
                               min_value=10, max_value=500)
    open_price = factory.LazyAttribute(lambda obj: float(obj.close_price) * factory.Faker('pydecimal', 
                                     left_digits=1, right_digits=3, positive=True, 
                                     min_value=0.95, max_value=1.05).generate())
    high_price = factory.LazyAttribute(lambda obj: max(obj.open_price, float(obj.close_price)) * 
                                     factory.Faker('pydecimal', left_digits=1, right_digits=3, 
                                     positive=True, min_value=1.0, max_value=1.1).generate())
    low_price = factory.LazyAttribute(lambda obj: min(obj.open_price, float(obj.close_price)) * 
                                    factory.Faker('pydecimal', left_digits=1, right_digits=3, 
                                    positive=True, min_value=0.9, max_value=1.0).generate())
    
    volume = factory.Faker('random_int', min=100_000, max=100_000_000)
    source = 'FACTORY_TEST'

class CompanyWithHistoryFactory(factory.Factory):
    """Factory for companies with price history."""
    
    class Meta:
        model = dict
    
    # Company information
    company = factory.SubFactory(MockCompanyFactory)
    
    # Price history (build multiple related records)
    price_history = factory.LazyFunction(
        lambda: TickerHistoryFactory.build_batch(
            factory.Faker('random_int', min=30, max=365).generate()
        )
    )

class TestBusinessLogicWithComplexObjects(unittest.TestCase):
    
    def setUp(self):
        factory.Faker.seed(77777)
    
    @patch('src.repos.equities.tickers.ticker_history_repository.TickerHistoryRepository')
    def test_price_analysis_with_factory_history(self, mock_repo_class):
        """Test price analysis logic with Factory Boy generated price history."""
        
        # Generate company with realistic price history
        company_data = CompanyWithHistoryFactory.build()
        company = company_data['company']
        price_history = company_data['price_history']
        
        # Mock repository to return Factory-generated data
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_price_history.return_value = price_history
        
        # Test your price analysis service
        # (This would be your actual business logic)
        
        # Example analysis: calculate average volume
        total_volume = sum(day['volume'] for day in price_history)
        avg_volume = total_volume / len(price_history)
        
        # Verify analysis with Factory-generated realistic data
        self.assertGreater(avg_volume, 100_000)  # Realistic volume range
        self.assertLess(avg_volume, 100_000_000)
        
        # Verify price relationships are realistic (Factory ensures this)
        for day_data in price_history:
            self.assertLessEqual(day_data['low_price'], day_data['close_price'])
            self.assertLessEqual(day_data['close_price'], day_data['high_price'])
            self.assertLessEqual(day_data['low_price'], day_data['open_price'])
            self.assertLessEqual(day_data['open_price'], day_data['high_price'])
        
        # Verify repository was called correctly
        mock_repo.get_price_history.assert_called_once()
    
    @patch('src.services.notification_service.NotificationService')
    def test_alert_service_with_factory_scenarios(self, mock_notification_service):
        """Test alert service with various Factory-generated scenarios."""
        
        # Generate different alert scenarios
        scenarios = [
            # High volume scenario
            CompanyWithHistoryFactory.build(),
            # Low volume scenario  
            CompanyWithHistoryFactory.build(),
            # Price volatility scenario
            CompanyWithHistoryFactory.build()
        ]
        
        mock_notification = MagicMock()
        mock_notification_service.return_value = mock_notification
        
        for scenario in scenarios:
            with self.subTest(company=scenario['company'].company_name):
                company = scenario['company']
                price_history = scenario['price_history']
                
                # Test your alert logic with Factory-generated data
                # (This would be your actual alert service)
                
                # Example: Check if recent volume is above average
                recent_volume = sum(day['volume'] for day in price_history[-5:]) / 5
                historical_avg = sum(day['volume'] for day in price_history[:-5]) / len(price_history[:-5])
                
                if recent_volume > historical_avg * 1.5:  # 50% above average
                    # Would trigger alert in real service
                    mock_notification.send_volume_alert.assert_called()
                
                # Verify Factory-generated data is realistic for alerts
                self.assertIsInstance(company.company_name, str)
                self.assertGreater(len(price_history), 30)  # Sufficient history
                self.assertTrue(all(day['volume'] > 0 for day in price_history))
```

## Advanced Patterns

### Pattern 6: Trait-Based Testing with Mocked Dependencies

```python
class ScenarioCompanyFactory(MockCompanyFactory):
    """Factory with traits for different test scenarios."""
    
    class Params:
        # Define traits for different scenarios
        high_performer = factory.Trait(
            market_cap=factory.Faker('random_int', min=100_000_000_000, max=3_000_000_000_000),
            sector='Technology'
        )
        
        struggling = factory.Trait(
            market_cap=factory.Faker('random_int', min=100_000_000, max=1_000_000_000),
            active=factory.Iterator([True, False])  # Some might be delisted
        )
        
        international = factory.Trait(
            country=factory.Iterator(['Canada', 'United Kingdom', 'Germany', 'Japan'])
        )

class TestTraitBasedScenarios(unittest.TestCase):
    
    @patch('src.external_api.stock_screener.StockScreenerAPI')
    def test_processing_different_company_types(self, mock_api):
        """Test processing different types of companies with mocked API."""
        
        # Generate different company types using traits
        high_performers = ScenarioCompanyFactory.build_batch(5, high_performer=True)
        struggling_companies = ScenarioCompanyFactory.build_batch(3, struggling=True)
        international_companies = ScenarioCompanyFactory.build_batch(4, international=True)
        
        # Mock API responses based on company traits
        def mock_api_response(company):
            if company.market_cap > 10_000_000_000:  # High performer
                return {'rating': 'BUY', 'confidence': 0.9}
            elif company.market_cap < 1_000_000_000:  # Struggling
                return {'rating': 'SELL', 'confidence': 0.7}
            else:
                return {'rating': 'HOLD', 'confidence': 0.5}
        
        mock_api.get_rating.side_effect = mock_api_response
        
        # Test your processing logic
        all_companies = high_performers + struggling_companies + international_companies
        
        for company in all_companies:
            rating = mock_api.get_rating(company)
            
            # Verify different scenarios produce appropriate responses
            if company.market_cap > 10_000_000_000:
                self.assertEqual(rating['rating'], 'BUY')
            elif company.market_cap < 1_000_000_000:
                self.assertEqual(rating['rating'], 'SELL')
```

## Type-Safe Mocking with unittest.mock + Factory Boy

### Using `spec` and `autospec` with Factory Boy Objects

Factory Boy objects can be used with type-safe mocks to ensure your tests respect interface contracts:

```python
from unittest.mock import MagicMock, create_autospec
from typing import List, Optional, TYPE_CHECKING
import factory

if TYPE_CHECKING:
    from src.repos.equities.companies.company_repository import CompanyRepository
    from src.database.equities.tables.company import Company

class TypedCompanyFactory(MockCompanyFactory):
    """Factory that creates properly typed Company objects."""
    
    class Meta:
        model = Company
        sqlalchemy_session = None
    
    # Factory Boy attributes remain the same
    id = factory.Sequence(lambda n: n + 1)
    company_name = factory.Faker('company')
    sector = factory.Iterator(['Technology', 'Healthcare', 'Financial'])
    
    @classmethod
    def build_with_spec(cls, **kwargs) -> 'Company':
        """Build Factory Boy object with proper type spec."""
        company = cls.build(**kwargs)
        
        # Ensure the object has the correct interface
        if not hasattr(company, '__class__'):
            company = MagicMock(spec=Company, **company.__dict__)
            
        return company

class TestRepositoryWithTypedFactories(unittest.TestCase):
    
    def setUp(self):
        factory.Faker.seed(12345)
    
    def test_repository_with_autospec_and_factory_objects(self):
        """Test repository with type-safe mocks and Factory Boy objects."""
        
        # Create type-safe repository mock
        mock_repo = create_autospec(CompanyRepository, spec_set=True)
        
        # Generate realistic companies using Factory Boy
        tech_companies = TypedCompanyFactory.build_batch(5, sector="Technology")
        
        # Ensure all objects have proper typing
        typed_companies = [
            MagicMock(spec=Company, **{
                'id': company.id,
                'company_name': company.company_name,
                'sector': company.sector,
                'market_cap': company.market_cap,
                'active': company.active
            })
            for company in tech_companies
        ]
        
        # Configure typed mock with Factory Boy data
        mock_repo.find_by_sector.return_value = typed_companies
        
        # Test your service
        result = mock_repo.find_by_sector("Technology")
        
        # Type-safe assertions
        self.assertEqual(len(result), 5)
        for company in result:
            self.assertIsInstance(company.id, int)
            self.assertIsInstance(company.company_name, str)
            self.assertEqual(company.sector, "Technology")
            
        # Verify method was called with correct signature
        mock_repo.find_by_sector.assert_called_once_with("Technology")
```

### Typed Factory Methods for Mock Configuration

```python
from typing import cast

class TypedMockFactoryHelpers:
    """Helper methods for creating typed mocks with Factory Boy data."""
    
    @staticmethod
    def create_typed_repo_mock() -> 'CompanyRepository':
        """Create a properly typed repository mock."""
        return cast('CompanyRepository', create_autospec(CompanyRepository, spec_set=True))
    
    @staticmethod
    def create_mock_company_from_factory(factory_company: Company) -> 'Company':
        """Convert Factory Boy company to typed mock."""
        mock_company = MagicMock(spec=Company)
        
        # Copy all attributes from Factory Boy object
        for attr_name in ['id', 'company_name', 'sector', 'industry', 
                         'market_cap', 'country', 'active', 'source']:
            if hasattr(factory_company, attr_name):
                setattr(mock_company, attr_name, getattr(factory_company, attr_name))
        
        return cast('Company', mock_company)
    
    @staticmethod
    def setup_mock_session_with_factory_data(companies: List[Company]):
        """Setup typed SQLAlchemy session mock with Factory Boy data."""
        from sqlalchemy.orm import Session
        
        mock_session = create_autospec(Session, spec_set=True)
        mock_query = MagicMock()
        
        # Configure query chain with proper typing
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = companies
        mock_query.first.return_value = companies[0] if companies else None
        
        return mock_session

class TestWithTypedFactoryHelpers(unittest.TestCase):
    
    def setUp(self):
        factory.Faker.seed(54321)
        self.helpers = TypedMockFactoryHelpers()
    
    def test_complete_typed_workflow(self):
        """Test complete workflow with typed mocks and Factory Boy objects."""
        
        # Generate realistic data with Factory Boy
        source_companies = EnhancedCompanyFactory.build_batch(10)
        
        # Convert to typed mocks
        typed_companies = [
            self.helpers.create_mock_company_from_factory(company)
            for company in source_companies
        ]
        
        # Create typed repository mock
        mock_repo = self.helpers.create_typed_repo_mock()
        mock_repo.get_all_companies.return_value = typed_companies
        
        # Create typed session mock
        mock_session = self.helpers.setup_mock_session_with_factory_data(typed_companies)
        
        # Test with proper typing throughout
        all_companies = mock_repo.get_all_companies()
        
        # Type-safe operations
        self.assertEqual(len(all_companies), 10)
        
        # All objects maintain proper typing
        for company in all_companies:
            self.assertIsInstance(company.company_name, str)
            self.assertIsInstance(company.market_cap, int)
            self.assertIsInstance(company.active, bool)
```

### Type-Safe Factory Traits with Mock Integration

```python
class TypedScenarioCompanyFactory(MockCompanyFactory):
    """Factory with typed traits for different scenarios."""
    
    class Meta:
        model = Company
        sqlalchemy_session = None
    
    company_name = factory.Faker('company')
    sector = 'Technology'
    
    class Params:
        # Typed traits
        high_performer = factory.Trait(
            market_cap=factory.Faker('random_int', min=100_000_000_000, max=3_000_000_000_000),
            active=True
        )
        
        struggling = factory.Trait(
            market_cap=factory.Faker('random_int', min=100_000_000, max=1_000_000_000),
            active=factory.Iterator([True, False])
        )

def test_typed_trait_scenarios(self):
    """Test different scenarios with typed Factory Boy traits."""
    
    # Generate companies with different traits
    high_performers = TypedScenarioCompanyFactory.build_batch(3, high_performer=True)
    struggling_companies = TypedScenarioCompanyFactory.build_batch(2, struggling=True)
    
    # Create typed mocks for each scenario
    mock_high_perf_service = create_autospec('src.services.AnalysisService')
    mock_struggling_service = create_autospec('src.services.AlertService')
    
    # Configure mocks with Factory Boy data
    for company in high_performers:
        typed_company = MagicMock(spec=Company)
        typed_company.market_cap = company.market_cap
        typed_company.sector = company.sector
        
        # Mock returns type-safe response
        mock_high_perf_service.analyze_company.return_value = {
            'rating': 'BUY',
            'confidence': 0.9,
            'company_id': typed_company.id
        }
    
    # Verify typed interactions
    for company in high_performers:
        result = mock_high_perf_service.analyze_company(company)
        self.assertIsInstance(result['rating'], str)
        self.assertIsInstance(result['confidence'], float)
```

### Handling Complex Relationships with Type Safety

```python
class TypedRelationshipTest(unittest.TestCase):
    
    def test_company_with_typed_relationships(self):
        """Test Factory Boy relationships with proper typing."""
        
        # Create companies with relationships using Factory Boy
        companies_with_tickers = CompanyWithTickersFactory.build_batch(5)
        
        # Mock repository that handles relationships
        mock_repo = create_autospec(CompanyRepository, spec_set=True)
        
        # Setup typed responses for relationship queries
        def mock_find_with_tickers(company_id: int) -> Optional['Company']:
            matching_companies = [c for c in companies_with_tickers if c.id == company_id]
            
            if matching_companies:
                company = matching_companies[0]
                
                # Create typed mock with relationships
                mock_company = MagicMock(spec=Company)
                mock_company.id = company.id
                mock_company.company_name = company.company_name
                mock_company.sector = company.sector
                
                # Handle ticker relationships with typing
                mock_tickers = []
                for ticker in company.tickers:
                    mock_ticker = MagicMock(spec=Ticker)
                    mock_ticker.id = ticker.id
                    mock_ticker.symbol = ticker.symbol
                    mock_ticker.company_id = company.id
                    mock_tickers.append(mock_ticker)
                
                mock_company.tickers = mock_tickers
                return cast('Company', mock_company)
            
            return None
        
        # Configure typed mock behavior
        mock_repo.find_with_relationships.side_effect = mock_find_with_tickers
        
        # Test with proper typing
        for company in companies_with_tickers[:3]:  # Test subset
            result = mock_repo.find_with_relationships(company.id)
            
            if result is not None:
                # Type-safe relationship access
                self.assertIsInstance(result.id, int)
                self.assertIsInstance(result.tickers, list)
                
                for ticker in result.tickers:
                    self.assertIsInstance(ticker.symbol, str)
                    self.assertEqual(ticker.company_id, result.id)
```

### Type-Safe Error Handling with Factory Boy

```python
def test_typed_error_scenarios_with_factories(self):
    """Test error scenarios with typed exceptions and Factory Boy data."""
    
    from src.utils.exceptions import ValidationError, DatabaseError
    
    # Create problematic companies using Factory Boy
    invalid_companies = [
        EnhancedCompanyFactory.build(market_cap=-1000),  # Invalid market cap
        EnhancedCompanyFactory.build(sector=None),       # Missing sector
        EnhancedCompanyFactory.build(company_name=""),   # Empty name
    ]
    
    # Create typed mock that raises proper exceptions
    mock_validator = create_autospec('src.validation.CompanyValidator')
    
    def typed_validation_response(company: 'Company') -> None:
        """Type-safe validation that raises appropriate exceptions."""
        if company.market_cap <= 0:
            raise ValidationError(
                f"Invalid market cap: {company.market_cap}",
                field="market_cap",
                value=company.market_cap
            )
        
        if not company.sector:
            raise ValidationError(
                "Sector is required",
                field="sector", 
                value=company.sector
            )
        
        if not company.company_name.strip():
            raise ValidationError(
                "Company name cannot be empty",
                field="company_name",
                value=company.company_name
            )
    
    mock_validator.validate.side_effect = typed_validation_response
    
    # Test each error scenario
    for company in invalid_companies:
        with self.assertRaises(ValidationError) as context:
            mock_validator.validate(company)
        
        # Verify typed exception attributes
        error = context.exception
        self.assertIsInstance(error.args[0], str)  # Error message
        self.assertTrue(hasattr(error, 'field'))   # Field name
        self.assertTrue(hasattr(error, 'value'))   # Invalid value
```

## Best Practices for unittest.mock + Factory Boy

### 1. Separate Factory Definitions

```python
# tests/factories/company_factories.py
class CompanyFactory(SQLAlchemyModelFactory):
    """Reusable factory for Company objects."""
    # Factory definition here

# tests/factories/ticker_factories.py  
class TickerFactory(SQLAlchemyModelFactory):
    """Reusable factory for Ticker objects."""
    # Factory definition here

# tests/test_repositories.py
from tests.factories.company_factories import CompanyFactory
from tests.factories.ticker_factories import TickerFactory
```

### 2. Use Factory Boy for Domain Objects, Mock for Infrastructure

```python
def test_service_layer(self):
    """Good separation of concerns."""
    
    # Use Factory Boy for domain objects (realistic, complex)
    companies = CompanyFactory.build_batch(10)
    
    # Mock infrastructure dependencies (controlled, predictable)
    with patch('src.external_api.MarketDataAPI') as mock_api:
        mock_api.get_prices.return_value = [...]
        
        # Test your service with realistic domain objects
        # but controlled infrastructure
```

### 3. Create Realistic Object Relationships

```python
class CompanyWithFullDataFactory(CompanyFactory):
    """Factory that creates companies with all related data."""
    
    # Create related objects
    tickers = factory.RelatedFactoryBoy('tests.factories.TickerFactory', 'company', size=2)
    price_history = factory.RelatedFactoryBoy('tests.factories.PriceHistoryFactory', 'company', size=90)
    
    class Params:
        with_recent_activity = factory.Trait(
            # Add recent price history
            price_history__size=30,
            active=True
        )
```

## When to Use unittest.mock + Factory Boy

✅ **Perfect For:**
- **Unit testing** business logic with complex domain objects
- **Service layer testing** with realistic object relationships
- **Repository testing** without database dependencies
- **Testing object transformations** with varied input structures
- **Component integration testing** with controlled external dependencies

✅ **Benefits:**
- **Realistic objects**: Factory Boy creates complex, related objects
- **Controlled environment**: unittest.mock isolates external dependencies
- **Maintainable**: Factory changes automatically update all tests
- **Comprehensive**: Easy to test many scenarios with traits and variations

❌ **Don't Use For:**
- **Integration testing** requiring real database operations
- **Testing external API contracts** (use contract testing)
- **Simple unit tests** where basic mocks suffice
- **Performance testing** of actual database operations

## Running Tests

```bash
# Run unittest.mock + Factory Boy tests
python -m unittest discover tests/unit/ -v

# Run specific test patterns
python -m unittest tests.unit.test_mock_factory_integration -v

# Run with factory debugging
FACTORY_DEBUG=1 python -m unittest tests.unit.test_repositories -v
```

This combination provides the perfect balance of realistic, complex test data (Factory Boy) with controlled, isolated testing environment (unittest.mock).