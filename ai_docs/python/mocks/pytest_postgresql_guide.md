# pytest-postgresql Usage Guide for Options-Deep

## Core Concepts

pytest-postgresql creates real PostgreSQL database instances for testing. It provides temporary, isolated databases that are perfect for integration testing with your actual database schema.

### Installation
```bash
pip install pytest-postgresql
```

### Key Features
- **Real PostgreSQL**: Uses actual PostgreSQL databases, not mocks
- **Automatic cleanup**: Databases are created and destroyed per test
- **Multiple fixture types**: Session, function, or process-scoped databases
- **SQLAlchemy integration**: Works seamlessly with your ORM

## Basic Setup for Options-Deep

### 1. Configure pytest-postgresql

Create `conftest.py` in your tests directory:

```python
import pytest
from pytest_postgresql import factories
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.equities.base import Base
from src.database.equities.tables.company import Company
from src.database.equities.tables.ticker import Ticker
from src.database.equities.tables.ticker_history import TickerHistory

# Create PostgreSQL process and database factories
postgresql_proc = factories.postgresql_proc(
    port=None,  # Use random port
    unixsocketdir='/tmp'
)

postgresql = factories.postgresql('postgresql_proc')

@pytest.fixture
def db_engine(postgresql):
    """Create database engine with your schema."""
    connection_string = f"postgresql://postgres@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    engine = create_engine(connection_string)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    """Create database session for testing."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    
    yield session
    
    session.close()
```

## Testing Your CompanyRepository

### Example: Integration Test with Real Database

```python
from src.repos.equities.companies.company_repository import CompanyRepository
from src.data_sources.models.company import Company as CompanyModel
from src.data_sources.models.ticker import Ticker as TickerModel

def test_company_repository_create_and_find(db_session):
    """Test creating and finding companies with real database."""
    
    # Create repository with real session
    repo = CompanyRepository()
    repo.session = db_session
    
    # Create test company model
    ticker = TickerModel(symbol="AAPL", company_id=None)
    company_model = CompanyModel(
        id=None,
        ticker=ticker,
        company_name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
        industry="Consumer Electronics",
        country="United States",
        market_cap=2800000000000,
        description="Technology company",
        source="TEST"
    )
    
    # Create company in database
    created_company = repo.create_company(company_model)
    
    # Verify creation
    assert created_company.id is not None
    assert created_company.company_name == "Apple Inc."
    
    # Find by symbol
    found_company = repo.find_by_symbol("AAPL")
    assert found_company is not None
    assert found_company.company_name == "Apple Inc."
    assert found_company.sector == "Technology"

def test_company_repository_find_by_sector(db_session):
    """Test finding companies by sector."""
    
    repo = CompanyRepository()
    repo.session = db_session
    
    # Create multiple companies in different sectors
    companies = [
        CompanyModel(
            id=None,
            ticker=TickerModel(symbol="AAPL", company_id=None),
            company_name="Apple Inc.",
            exchange="NASDAQ",
            sector="Technology",
            industry="Consumer Electronics",
            country="United States",
            market_cap=2800000000000,
            source="TEST"
        ),
        CompanyModel(
            id=None,
            ticker=TickerModel(symbol="JPM", company_id=None),
            company_name="JPMorgan Chase",
            exchange="NYSE", 
            sector="Financial",
            industry="Banking",
            country="United States",
            market_cap=400000000000,
            source="TEST"
        ),
        CompanyModel(
            id=None,
            ticker=TickerModel(symbol="GOOGL", company_id=None),
            company_name="Alphabet Inc.",
            exchange="NASDAQ",
            sector="Technology", 
            industry="Internet Content",
            country="United States",
            market_cap=1600000000000,
            source="TEST"
        )
    ]
    
    # Create all companies
    for company in companies:
        repo.create_company(company)
    
    # Find technology companies
    tech_companies = repo.find_by_sector("Technology")
    
    assert len(tech_companies) == 2
    tech_names = [c.company_name for c in tech_companies]
    assert "Apple Inc." in tech_names
    assert "Alphabet Inc." in tech_names
    
    # Find financial companies
    financial_companies = repo.find_by_sector("Financial")
    assert len(financial_companies) == 1
    assert financial_companies[0].company_name == "JPMorgan Chase"
```

## Testing Database Schema and Migrations

### Example: Test Database Schema

```python
from sqlalchemy import inspect
from src.database.equities.tables.company import Company
from src.database.equities.tables.ticker import Ticker

def test_database_schema_exists(db_engine):
    """Verify that all expected tables exist with correct columns."""
    
    inspector = inspect(db_engine)
    
    # Check companies table
    companies_columns = inspector.get_columns('companies')
    column_names = [col['name'] for col in companies_columns]
    
    expected_columns = [
        'id', 'company_name', 'exchange', 'sector', 'industry', 
        'country', 'market_cap', 'description', 'active', 'source',
        'created_at', 'updated_at'
    ]
    
    for col in expected_columns:
        assert col in column_names, f"Column {col} missing from companies table"
    
    # Check tickers table
    tickers_columns = inspector.get_columns('tickers')
    ticker_column_names = [col['name'] for col in tickers_columns]
    
    expected_ticker_columns = ['id', 'symbol', 'company_id', 'primary_ticker', 'created_at']
    
    for col in expected_ticker_columns:
        assert col in ticker_column_names, f"Column {col} missing from tickers table"

def test_database_relationships(db_session):
    """Test that database relationships work correctly."""
    
    # Create company
    from src.database.equities.tables.company import Company
    from src.database.equities.tables.ticker import Ticker
    
    company = Company(
        company_name="Test Company",
        exchange="NASDAQ",
        sector="Technology",
        source="TEST"
    )
    db_session.add(company)
    db_session.flush()  # Get the ID without committing
    
    # Create ticker linked to company
    ticker = Ticker(
        symbol="TEST",
        company_id=company.id,
        primary_ticker=True
    )
    db_session.add(ticker)
    db_session.commit()
    
    # Test relationship
    assert len(company.tickers) == 1
    assert company.tickers[0].symbol == "TEST"
    assert ticker.company.company_name == "Test Company"
```

## Testing Data Pipeline with Real Database

### Example: End-to-End Pipeline Test

```python
from src.pipelines.companies.simple_pipeline import CompanyPipeline
from src.data_sources.models.company import Company as CompanyModel
from src.data_sources.models.ticker import Ticker as TickerModel

def test_company_pipeline_integration(db_session):
    """Test the complete company processing pipeline."""
    
    # Create mock database config that uses our test session
    class MockDBConfig:
        def connection_string(self):
            return str(db_session.bind.url)
    
    # Create test companies
    companies = [
        CompanyModel(
            id=None,
            ticker=TickerModel(symbol="AAPL", company_id=None),
            company_name="Apple Inc.",
            exchange="NASDAQ",
            sector="Technology",
            industry="Consumer Electronics",
            country="United States",
            market_cap=2800000000000,
            source="NASDAQ_SCREENER"
        ),
        CompanyModel(
            id=None,
            ticker=TickerModel(symbol="GOOGL", company_id=None), 
            company_name="Alphabet Inc.",
            exchange="NASDAQ",
            sector="Technology",
            industry="Internet Content", 
            country="United States",
            market_cap=1600000000000,
            source="NASDAQ_SCREENER"
        )
    ]
    
    # Process through pipeline
    pipeline = CompanyPipeline(MockDBConfig())
    
    # Override the repository session with our test session
    pipeline.repository.session = db_session
    
    result = pipeline.process_companies(companies)
    
    # Verify results
    assert len(result.successful) == 2
    assert len(result.failed) == 0
    
    # Verify data was actually inserted
    from src.database.equities.tables.company import Company
    
    stored_companies = db_session.query(Company).all()
    assert len(stored_companies) == 2
    
    company_names = [c.company_name for c in stored_companies]
    assert "Apple Inc." in company_names
    assert "Alphabet Inc." in company_names
```

## Testing NASDAQ Screener Integration

### Example: Test CSV Loading with Database

```python
import tempfile
import csv
from pathlib import Path
from src.data_sources.nasdaq.screener import load_screener_file
from src.pipelines.companies.simple_pipeline import CompanyPipeline

def test_screener_to_database_integration(db_session):
    """Test loading screener data and storing in database."""
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
        csv_data = [
            ['Symbol', 'Name', 'Last Sale', 'Net Change', '% Change', 'Market Cap', 
             'Country', 'IPO Year', 'Volume', 'Sector', 'Industry'],
            ['AAPL', 'Apple Inc.', '150.00', '2.50', '1.69%', '2800000000000',
             'United States', '1980', '50000000', 'Technology', 'Consumer Electronics'],
            ['GOOGL', 'Alphabet Inc.', '2800.00', '-15.50', '-0.55%', '1600000000000',
             'United States', '2004', '25000000', 'Technology', 'Internet Content']
        ]
        
        writer = csv.writer(temp_file)
        writer.writerows(csv_data)
        temp_file_path = temp_file.name
    
    try:
        # Load companies from screener file
        companies = load_screener_file(temp_file_path)
        
        assert len(companies) == 2
        assert companies[0].company_name == "Apple Inc."
        assert companies[1].company_name == "Alphabet Inc."
        
        # Process through pipeline into database
        class MockDBConfig:
            def connection_string(self):
                return str(db_session.bind.url)
        
        pipeline = CompanyPipeline(MockDBConfig())
        pipeline.repository.session = db_session
        
        result = pipeline.process_companies(companies)
        
        # Verify database storage
        assert len(result.successful) == 2
        
        from src.database.equities.tables.company import Company
        stored_companies = db_session.query(Company).all()
        assert len(stored_companies) == 2
        
    finally:
        # Cleanup temp file
        Path(temp_file_path).unlink()
```

## Performance Testing with Real Database

### Example: Bulk Operations Test

```python
import time
from src.repos.equities.companies.company_repository import CompanyRepository
from src.data_sources.models.company import Company as CompanyModel
from src.data_sources.models.ticker import Ticker as TickerModel

def test_bulk_company_creation_performance(db_session):
    """Test performance of bulk company creation."""
    
    repo = CompanyRepository()
    repo.session = db_session
    
    # Create 1000 test companies
    companies = []
    for i in range(1000):
        ticker = TickerModel(symbol=f"TEST{i:04d}", company_id=None)
        company = CompanyModel(
            id=None,
            ticker=ticker,
            company_name=f"Test Company {i}",
            exchange="NASDAQ",
            sector="Technology",
            industry="Software",
            country="United States",
            market_cap=1000000000 + i * 1000000,
            source="TEST"
        )
        companies.append(company)
    
    # Time the bulk creation
    start_time = time.time()
    
    for company in companies:
        repo.create_company(company)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Verify all companies were created
    from src.database.equities.tables.company import Company
    count = db_session.query(Company).count()
    assert count == 1000
    
    # Performance assertion (adjust based on your requirements)
    assert processing_time < 10.0, f"Bulk creation took {processing_time:.2f}s, expected < 10s"
    
    print(f"Created 1000 companies in {processing_time:.2f} seconds")
    print(f"Average: {(processing_time/1000)*1000:.2f}ms per company")
```

## Configuration for CI/CD

### Example: GitHub Actions Setup

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest-postgresql
          
      - name: Run integration tests
        run: pytest tests/integration/ -v
        env:
          # pytest-postgresql will use these if needed
          PGHOST: localhost
          PGUSER: postgres
          PGPASSWORD: postgres
```

## Best Practices for Options-Deep

### 1. Separate Unit and Integration Tests

```bash
# Directory structure
tests/
├── unit/           # Fast tests with mocks
├── integration/    # Tests with pytest-postgresql
└── conftest.py     # Shared fixtures
```

### 2. Use Appropriate Test Scopes

```python
# Session-scoped for expensive setup
@pytest.fixture(scope="session")
def session_postgresql():
    # Shared database for multiple tests
    pass

# Function-scoped for test isolation  
@pytest.fixture(scope="function")
def clean_db():
    # Fresh database per test
    pass
```

### 3. Test Database Constraints

```python
def test_unique_constraints(db_session):
    """Verify database constraints work correctly."""
    
    from src.database.equities.tables.company import Company
    
    # Create first company
    company1 = Company(company_name="Test", exchange="NASDAQ", source="TEST")
    db_session.add(company1)
    db_session.commit()
    
    # Try to create duplicate - should fail if constraints are working
    from sqlalchemy.exc import IntegrityError
    
    with pytest.raises(IntegrityError):
        company2 = Company(company_name="Test", exchange="NASDAQ", source="TEST")
        db_session.add(company2) 
        db_session.commit()
```

## When to Use pytest-postgresql in Options-Deep

✅ **Use For:**
- Testing repository methods with real SQL
- Verifying database schema and constraints
- Integration testing between components
- Testing PostgreSQL-specific features (JSONB, arrays)
- Performance testing with realistic data
- Testing database migrations

❌ **Don't Use For:**
- Testing business logic that doesn't need database
- Fast unit tests (use pytest-mock instead)
- Simple validation logic
- External API interactions

## Running Integration Tests

```bash
# Install dependencies
pip install pytest-postgresql

# Run only integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/integration/ --cov=src --cov-report=html

# Run specific database tests
pytest tests/integration/test_repositories.py -v

# Run with database cleanup verification
pytest tests/integration/ -v -s
```