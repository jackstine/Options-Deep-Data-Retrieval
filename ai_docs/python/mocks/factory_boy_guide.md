# Factory Boy Usage Guide for Options-Deep

## Core Concepts

Factory Boy is a library for creating test data objects. Instead of manually creating test objects, you define factories that can generate realistic, varied test data automatically.

### Installation
```bash
pip install factory_boy
```

### Key Features
- **Automatic data generation**: Creates objects with realistic data
- **Relationships**: Handles object relationships automatically  
- **Sequences**: Generates unique values for each object
- **Traits**: Create variations of objects for different test scenarios
- **Faker integration**: Uses Faker library for realistic data

> 💡 **Integration Note**: Factory Boy works seamlessly with Faker (see [faker_guide.md](faker_guide.md)) to generate realistic test data. You can use Faker providers directly within Factory Boy declarations.

## Setting Up Factories for Options-Deep

### 1. Company Factory

```python
# tests/factories.py
import factory
from factory import Faker, Sequence, SubFactory
from factory.alchemy import SQLAlchemyModelFactory
from datetime import datetime

from src.database.equities.tables.company import Company
from src.database.equities.tables.ticker import Ticker
from src.data_sources.models.company import Company as CompanyDataModel
from src.data_sources.models.ticker import Ticker as TickerDataModel

class CompanyFactory(SQLAlchemyModelFactory):
    """Factory for creating Company database objects."""
    
    class Meta:
        model = Company
        sqlalchemy_session_persistence = "commit"
    
    # Generate realistic company names
    company_name = Faker('company')
    
    # Exchange selection
    exchange = factory.Iterator(['NASDAQ', 'NYSE', 'AMEX'])
    
    # Sector selection
    sector = factory.Iterator([
        'Technology', 'Healthcare', 'Financial', 'Consumer Discretionary',
        'Consumer Staples', 'Energy', 'Industrials', 'Materials',
        'Real Estate', 'Communication Services', 'Utilities'
    ])
    
    # Industry (related to sector but more specific)
    industry = Faker('bs')  # Business speak for realistic industry names
    
    # Country
    country = 'United States'
    
    # Market cap in billions (1B to 3T range)
    market_cap = Faker('random_int', min=1_000_000_000, max=3_000_000_000_000)
    
    # Company description
    description = Faker('text', max_nb_chars=500)
    
    # Default active status
    active = True
    
    # Data source
    source = 'FACTORY_TEST'


class TickerFactory(SQLAlchemyModelFactory):
    """Factory for creating Ticker database objects."""
    
    class Meta:
        model = Ticker
        sqlalchemy_session_persistence = "commit"
    
    # Generate ticker symbols (3-4 characters) 
    # Using Faker for more realistic tickers (see faker_guide.md for custom StockMarketProvider)
    symbol = Faker('lexify', text='????', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    # Link to company (will be set when used with CompanyFactory)
    company = SubFactory(CompanyFactory)
    
    # Usually primary ticker
    primary_ticker = True


class CompanyDataModelFactory(factory.Factory):
    """Factory for creating Company data models (not database objects)."""
    
    class Meta:
        model = CompanyDataModel
    
    id = None
    company_name = Faker('company')
    exchange = factory.Iterator(['NASDAQ', 'NYSE', 'AMEX'])
    sector = factory.Iterator([
        'Technology', 'Healthcare', 'Financial', 'Consumer Discretionary'
    ])
    industry = Faker('bs')
    country = 'United States'
    market_cap = Faker('random_int', min=1_000_000_000, max=3_000_000_000_000)
    description = Faker('text', max_nb_chars=500)
    active = True
    source = 'FACTORY_TEST'
    
    # Create associated ticker
    ticker = SubFactory('tests.factories.TickerDataModelFactory')


class TickerDataModelFactory(factory.Factory):
    """Factory for creating Ticker data models."""
    
    class Meta:
        model = TickerDataModel
    
    # Use Faker for realistic ticker symbols (see faker_guide.md for StockMarketProvider)
    symbol = Faker('lexify', text='????', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    company_id = None
```

## Using Factories in Tests

### Example: Simple Factory Usage

```python
from tests.factories import CompanyFactory, CompanyDataModelFactory

def test_company_creation_with_factory(db_session):
    """Test creating companies using factories."""
    
    # Create a company using factory
    company = CompanyFactory()
    
    # Factory automatically creates realistic data
    assert company.company_name is not None
    assert company.exchange in ['NASDAQ', 'NYSE', 'AMEX']
    assert company.sector is not None
    assert company.market_cap > 0
    
    # Company is automatically saved to database
    assert company.id is not None

def test_multiple_companies_with_factory():
    """Create multiple companies with varied data."""
    
    # Create 5 companies at once
    companies = CompanyFactory.create_batch(5)
    
    assert len(companies) == 5
    
    # Each company has unique data
    company_names = [c.company_name for c in companies]
    assert len(set(company_names)) == 5  # All names are unique


def test_data_model_factory():
    """Test using data model factory (not database)."""
    
    # Create data model object (not saved to database)
    company_data = CompanyDataModelFactory()
    
    assert isinstance(company_data, CompanyDataModel)
    assert company_data.company_name is not None
    assert company_data.ticker is not None
    assert company_data.ticker.symbol is not None
```

### Example: Customizing Factory Data

```python
def test_custom_company_data():
    """Test creating companies with specific attributes."""
    
    # Override specific attributes
    apple_like = CompanyFactory(
        company_name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=2_800_000_000_000
    )
    
    assert apple_like.company_name == "Apple Inc."
    assert apple_like.sector == "Technology"
    
    # Create multiple companies with same sector
    tech_companies = CompanyFactory.create_batch(
        3, 
        sector="Technology",
        country="United States"
    )
    
    for company in tech_companies:
        assert company.sector == "Technology"
        assert company.country == "United States"
```

## Advanced Factory Patterns

### 1. Using Custom Faker Providers with Factory Boy

```python
# First, define custom Faker provider (see faker_guide.md for complete implementation)
from faker.providers import BaseProvider

class StockMarketProvider(BaseProvider):
    """Custom provider from faker_guide.md"""
    
    def stock_ticker(self):
        return ''.join(self.random_choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', length=4))
    
    def stock_sector(self):
        return self.random_element([
            'Technology', 'Healthcare', 'Financial Services', 'Consumer Discretionary'
        ])
    
    def market_cap(self):
        category = self.random_element(['small', 'mid', 'large', 'mega'])
        if category == 'small':
            return self.random_int(300_000_000, 2_000_000_000)
        elif category == 'mid':
            return self.random_int(2_000_000_000, 10_000_000_000)
        elif category == 'large':
            return self.random_int(10_000_000_000, 200_000_000_000)
        else:  # mega
            return self.random_int(200_000_000_000, 3_000_000_000_000)

# Register with Faker
from faker import Faker
fake = Faker()
fake.add_provider(StockMarketProvider)

# Use in Factory Boy
class EnhancedCompanyFactory(SQLAlchemyModelFactory):
    """Factory using custom Faker providers."""
    
    class Meta:
        model = Company
        sqlalchemy_session_persistence = "commit"
    
    # Use custom Faker providers
    company_name = Faker('company')
    sector = factory.LazyFunction(lambda: fake.stock_sector())
    market_cap = factory.LazyFunction(lambda: fake.market_cap())
    
    # Generate realistic ticker using custom provider
    ticker = factory.SubFactory('tests.factories.EnhancedTickerFactory')

class EnhancedTickerFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Ticker
        sqlalchemy_session_persistence = "commit"
    
    symbol = factory.LazyFunction(lambda: fake.stock_ticker())
    company = SubFactory(EnhancedCompanyFactory)
```

### 2. Traits for Different Company Types

```python
class CompanyFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Company
        sqlalchemy_session_persistence = "commit"
    
    company_name = Faker('company')
    exchange = 'NASDAQ'
    sector = 'Technology'
    industry = Faker('bs')
    country = 'United States'
    market_cap = Faker('random_int', min=1_000_000_000, max=100_000_000_000)
    source = 'FACTORY_TEST'
    
    class Params:
        # Define traits for different company types
        large_cap = factory.Trait(
            market_cap=Faker('random_int', min=10_000_000_000, max=3_000_000_000_000)
        )
        
        small_cap = factory.Trait(
            market_cap=Faker('random_int', min=300_000_000, max=2_000_000_000)
        )
        
        tech_company = factory.Trait(
            sector='Technology',
            industry=factory.Iterator(['Software', 'Hardware', 'Semiconductors'])
        )
        
        financial_company = factory.Trait(
            sector='Financial',
            industry=factory.Iterator(['Banking', 'Insurance', 'Investment Services'])
        )

# Usage in tests
def test_company_traits():
    """Test using traits to create specific company types."""
    
    # Create large-cap tech company
    big_tech = CompanyFactory(large_cap=True, tech_company=True)
    assert big_tech.sector == 'Technology'
    assert big_tech.market_cap >= 10_000_000_000
    
    # Create small-cap financial company
    small_bank = CompanyFactory(small_cap=True, financial_company=True)
    assert small_bank.sector == 'Financial'
    assert small_bank.market_cap < 2_000_000_000
```

### 2. Factories with Relationships

```python
class CompanyWithTickersFactory(CompanyFactory):
    """Factory that creates company with multiple tickers."""
    
    # Create related tickers after company creation
    ticker1 = factory.RelatedFactory('tests.factories.TickerFactory', 'company')
    ticker2 = factory.RelatedFactory('tests.factories.TickerFactory', 'company')

def test_company_with_multiple_tickers(db_session):
    """Test creating company with related tickers."""
    
    company = CompanyWithTickersFactory()
    
    # Company should have 2 tickers
    assert len(company.tickers) == 2
    
    # All tickers should reference this company
    for ticker in company.tickers:
        assert ticker.company_id == company.id
```

### 3. Realistic Stock Data Factory

```python
from src.database.equities.tables.ticker_history import TickerHistory
from datetime import datetime, timedelta

class TickerHistoryFactory(SQLAlchemyModelFactory):
    """Factory for creating stock price history."""
    
    class Meta:
        model = TickerHistory
        sqlalchemy_session_persistence = "commit"
    
    # Link to ticker and company
    ticker = SubFactory(TickerFactory)
    company = factory.LazyAttribute(lambda obj: obj.ticker.company)
    
    # Generate realistic stock prices
    price_date = Faker('date_between', start_date='-1y', end_date='today')
    
    # Base price around $100
    close_price = Faker('pydecimal', left_digits=3, right_digits=2, positive=True, min_value=10, max_value=500)
    
    # Other prices relative to close
    open_price = factory.LazyAttribute(lambda obj: obj.close_price * Faker('pydecimal', left_digits=1, right_digits=3, positive=True, min_value=0.95, max_value=1.05).generate())
    high_price = factory.LazyAttribute(lambda obj: max(obj.open_price, obj.close_price) * Faker('pydecimal', left_digits=1, right_digits=3, positive=True, min_value=1.0, max_value=1.1).generate())
    low_price = factory.LazyAttribute(lambda obj: min(obj.open_price, obj.close_price) * Faker('pydecimal', left_digits=1, right_digits=3, positive=True, min_value=0.9, max_value=1.0).generate())
    
    # Realistic volume
    volume = Faker('random_int', min=100_000, max=100_000_000)
    
    source = 'FACTORY_TEST'

def test_stock_price_history():
    """Test creating realistic stock price data."""
    
    # Create company with price history
    company = CompanyFactory()
    ticker = TickerFactory(company=company)
    
    # Create 30 days of price history
    price_history = TickerHistoryFactory.create_batch(
        30, 
        ticker=ticker,
        company=company
    )
    
    assert len(price_history) == 30
    
    for price_data in price_history:
        # Validate realistic price relationships
        assert price_data.low_price <= price_data.close_price <= price_data.high_price
        assert price_data.low_price <= price_data.open_price <= price_data.high_price
        assert price_data.volume > 0
```

## Integration with pytest Fixtures

### Example: Reusable Factory Fixtures

```python
# conftest.py
import pytest
from tests.factories import CompanyFactory, TickerFactory, CompanyDataModelFactory

@pytest.fixture
def sample_companies(db_session):
    """Create sample companies for testing."""
    return CompanyFactory.create_batch(5)

@pytest.fixture
def tech_companies(db_session):
    """Create technology companies."""
    return CompanyFactory.create_batch(3, sector="Technology")

@pytest.fixture
def company_data_models():
    """Create company data models (not database objects)."""
    return CompanyDataModelFactory.create_batch(3)

# Use in tests
def test_repository_with_sample_data(sample_companies, db_session):
    """Test repository methods with factory-created data."""
    
    from src.repos.equities.companies.company_repository import CompanyRepository
    
    repo = CompanyRepository()
    repo.session = db_session
    
    # Test finding by sector
    tech_companies = repo.find_by_sector("Technology")
    
    # Some companies might be tech companies from the sample
    assert isinstance(tech_companies, list)

def test_pipeline_with_factory_data(company_data_models, db_session):
    """Test pipeline processing with factory-generated data."""
    
    from src.pipelines.companies.simple_pipeline import CompanyPipeline
    
    class MockDBConfig:
        def connection_string(self):
            return str(db_session.bind.url)
    
    pipeline = CompanyPipeline(MockDBConfig())
    pipeline.repository.session = db_session
    
    result = pipeline.process_companies(company_data_models)
    
    assert len(result.successful) == 3
```

## Factory Boy with NASDAQ Screener Testing

### Example: Generate Realistic Screener Data

```python
class NASDAQCompanyFactory(CompanyDataModelFactory):
    """Factory specifically for NASDAQ screener-style data."""
    
    # NASDAQ-specific attributes
    exchange = 'NASDAQ'
    source = 'NASDAQ_SCREENER'
    
    # More realistic NASDAQ company data
    sector = factory.Iterator([
        'Technology', 'Healthcare', 'Consumer Discretionary',
        'Financial', 'Communication Services'
    ])
    
    # NASDAQ ticker format (usually 3-5 characters)
    ticker = factory.SubFactory(
        'tests.factories.NASDAQTickerFactory'
    )

class NASDAQTickerFactory(TickerDataModelFactory):
    """Factory for NASDAQ-style tickers."""
    
    # NASDAQ tickers are typically 4 characters
    symbol = factory.LazyFunction(
        lambda: factory.Faker('lexify', text='????').generate().upper()
    )

def test_nasdaq_screener_simulation():
    """Test processing simulated NASDAQ screener data."""
    
    # Generate realistic NASDAQ companies
    nasdaq_companies = NASDAQCompanyFactory.create_batch(100)
    
    # Verify they look like real NASDAQ data
    for company in nasdaq_companies:
        assert company.exchange == 'NASDAQ'
        assert company.source == 'NASDAQ_SCREENER'
        assert len(company.ticker.symbol) == 4
        assert company.ticker.symbol.isupper()
```

## Performance Testing with Factories

### Example: Generate Large Datasets

```python
def test_bulk_processing_performance(db_session):
    """Test performance with large dataset from factories."""
    
    import time
    
    # Generate 1000 companies
    start_time = time.time()
    companies = CompanyDataModelFactory.create_batch(1000)
    generation_time = time.time() - start_time
    
    print(f"Generated 1000 companies in {generation_time:.2f}s")
    
    # Process through pipeline
    from src.pipelines.companies.simple_pipeline import CompanyPipeline
    
    class MockDBConfig:
        def connection_string(self):
            return str(db_session.bind.url)
    
    pipeline = CompanyPipeline(MockDBConfig())
    pipeline.repository.session = db_session
    
    start_time = time.time()
    result = pipeline.process_companies(companies)
    processing_time = time.time() - start_time
    
    print(f"Processed 1000 companies in {processing_time:.2f}s")
    
    assert len(result.successful) == 1000
    assert processing_time < 30  # Should process reasonably fast
```

## Best Practices for Options-Deep

### 1. Organize Factories by Domain

```python
# tests/factories/company_factories.py
# tests/factories/ticker_factories.py  
# tests/factories/price_factories.py
```

### 2. Use Realistic Data Ranges

```python
# Good: Realistic market cap ranges
market_cap = Faker('random_int', min=1_000_000_000, max=3_000_000_000_000)

# Avoid: Unrealistic values
# market_cap = Faker('random_int')  # Could be negative or too large
```

### 3. Create Factory Fixtures for Common Scenarios

```python
@pytest.fixture
def sp500_like_companies():
    """Create companies that resemble S&P 500 constituents."""
    return CompanyFactory.create_batch(
        500,
        large_cap=True,
        country='United States',
        active=True
    )
```

## Integration with Faker

Factory Boy and Faker work perfectly together to create the most realistic test data:

### Combined Usage Example

```python
# Define Faker provider (from faker_guide.md)
fake = Faker()
fake.add_provider(StockMarketProvider)

# Use in Factory Boy with multiple approaches
class HybridCompanyFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Company
        sqlalchemy_session_persistence = "commit"
    
    # Method 1: Direct Faker usage in Factory Boy
    company_name = Faker('company')
    
    # Method 2: LazyFunction for custom providers
    market_cap = factory.LazyFunction(lambda: fake.market_cap())
    
    # Method 3: LazyAttribute for complex logic
    sector = factory.LazyAttribute(lambda obj: fake.stock_sector())
    
    # Method 4: Sequence with Faker
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=500))

# Generate realistic test data
companies = HybridCompanyFactory.create_batch(100)
```

### Benefits of Factory Boy + Faker Combination

✅ **Best of Both Worlds:**
- **Factory Boy**: Object relationships, database integration, traits
- **Faker**: Realistic data generation, localization, custom providers
- **Together**: Powerful, maintainable test data generation

## When to Use Factory Boy in Options-Deep

✅ **Use For:**
- Creating test data for integration tests
- Generating realistic datasets for performance testing
- Creating varied test scenarios with traits
- Building complex object relationships
- Simulating real-world data patterns
- **With Faker**: Maximum realism and variety in test data

✅ **Benefits:**
- Reduces test setup code
- Creates more realistic test data (especially with Faker)
- Easy to create variations of data
- Handles object relationships automatically
- Makes tests more maintainable

❌ **Don't Use For:**
- Simple unit tests where you need specific values
- Tests that require exact data values
- When you need complete control over every field

## Running Tests with Factory Boy

```bash
# Install Factory Boy
pip install factory_boy

# Run tests that use factories
pytest tests/integration/ -v

# Run with factory debugging
pytest tests/integration/ -v -s

# Generate test coverage report
pytest tests/ --cov=src --cov-report=html
```