# pytest-mock Usage Guide for Options-Deep

## Core Concepts

pytest-mock provides a simplified interface to unittest.mock through the `mocker` fixture. It automatically cleans up mocks between tests and offers cleaner syntax.

### Installation
```bash
pip install pytest-mock
```

### Key Features
- **mocker fixture**: Automatic mock creation and cleanup
- **Simplified syntax**: No decorators needed
- **Direct access**: Mock objects available immediately

## Mocking Your CompanyRepository

### Example: Clean Repository Testing

```python
def test_find_companies_by_sector(mocker):
    # Mock the database session
    mock_session = mocker.MagicMock()
    mock_query = mocker.MagicMock()
    
    # Configure mock chain
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [
        mocker.Mock(id=1, company_name="Apple Inc.", sector="Technology"),
        mocker.Mock(id=2, company_name="Microsoft Corp.", sector="Technology")
    ]
    
    # Test your repository
    repo = CompanyRepository()
    repo.session = mock_session
    
    companies = repo.find_by_sector("Technology")
    
    assert len(companies) == 2
    assert companies[0].company_name == "Apple Inc."
    mock_session.query.assert_called_once()
```

## Mocking Configuration System

### Example: Test Database Configuration

```python
def test_configuration_manager_equities_config(mocker):
    # Mock environment variables
    mocker.patch.dict('os.environ', {
        'ENVIRONMENT': 'local',
        'OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD': 'test_password'
    })
    
    # Mock file operations
    mock_config_data = {
        "databases": {
            "equities": {
                "host": "localhost",
                "port": 5432,
                "database": "options_deep_test",
                "username": "test_user"
            }
        }
    }
    
    mocker.patch('pathlib.Path.exists', return_value=True)
    mocker.patch('builtins.open', mocker.mock_open(read_data=str(mock_config_data)))
    mocker.patch('json.load', return_value=mock_config_data)
    
    from src.config.configuration import ConfigurationManager
    
    config = ConfigurationManager()
    db_config = config.get_equities_config()
    
    assert db_config.host == "localhost"
    assert db_config.password == "test_password"
```

## Mocking Data Sources

### Example: NASDAQ Screener with Clean Syntax

```python
def test_load_screener_file_success(mocker):
    # Mock file system
    mocker.patch('pathlib.Path.exists', return_value=True)
    
    csv_data = [
        {'Symbol': 'AAPL', 'Name': 'Apple Inc.', 'Market Cap': '2800000000000',
         'Country': 'United States', 'Sector': 'Technology', 'Industry': 'Consumer Electronics'},
        {'Symbol': 'GOOGL', 'Name': 'Alphabet Inc.', 'Market Cap': '1600000000000', 
         'Country': 'United States', 'Sector': 'Technology', 'Industry': 'Internet Content'}
    ]
    
    mock_csv_reader = mocker.MagicMock()
    mock_csv_reader.fieldnames = ['Symbol', 'Name', 'Market Cap', 'Country', 'Sector', 'Industry']
    mock_csv_reader.__iter__.return_value = iter(csv_data)
    
    mocker.patch('builtins.open', mocker.mock_open())
    mocker.patch('csv.DictReader', return_value=mock_csv_reader)
    
    from src.data_sources.nasdaq.screener import load_screener_file
    
    companies = load_screener_file("test_file.csv")
    
    assert len(companies) == 2
    assert companies[0].company_name == "Apple Inc."
    assert companies[0].ticker.symbol == "AAPL"
```

## Mocking Pipeline Operations

### Example: Company Processing Pipeline

```python
def test_company_pipeline_processing(mocker):
    # Create mock repository
    mock_repo = mocker.MagicMock()
    
    # Mock repository methods
    mock_repo.find_by_symbol.return_value = None  # Company doesn't exist
    mock_repo.create_company.return_value = mocker.Mock(id=1)
    
    # Mock database configuration
    mock_db_config = mocker.Mock()
    mock_db_config.connection_string.return_value = "postgresql://test"
    
    # Mock the repository creation in pipeline
    mocker.patch('src.pipelines.companies.simple_pipeline.CompanyRepository', 
                return_value=mock_repo)
    
    from src.pipelines.companies.simple_pipeline import CompanyPipeline
    
    # Create test companies
    companies = [
        mocker.Mock(
            ticker=mocker.Mock(symbol="AAPL"),
            company_name="Apple Inc.",
            exchange="NASDAQ"
        )
    ]
    
    pipeline = CompanyPipeline(mock_db_config)
    result = pipeline.process_companies(companies)
    
    # Verify interactions
    mock_repo.find_by_symbol.assert_called_once_with("AAPL")
    mock_repo.create_company.assert_called_once()
```

## Testing Data Models

### Example: Company Model Validation

```python
def test_company_model_creation(mocker):
    # Create mock ticker
    mock_ticker = mocker.Mock(
        symbol="AAPL",
        company_id=None
    )
    
    from src.data_sources.models.company import Company
    
    company = Company(
        id=None,
        ticker=mock_ticker,
        company_name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
        industry="Consumer Electronics",
        country="United States",
        market_cap=2800000000000,
        description="Technology company",
        source="TEST"
    )
    
    assert company.company_name == "Apple Inc."
    assert company.ticker.symbol == "AAPL"
    assert company.market_cap == 2800000000000
```

## Advanced pytest-mock Features

### 1. Spy Functionality

```python
def test_company_repository_with_spy(mocker):
    # Create actual repository
    repo = CompanyRepository()
    
    # Spy on a method to track calls without replacing behavior
    spy_find = mocker.spy(repo, 'find_by_symbol')
    
    # Mock only the database interaction
    mock_session = mocker.MagicMock()
    repo.session = mock_session
    
    # Call the method
    repo.find_by_symbol("AAPL")
    
    # Verify the spy recorded the call
    spy_find.assert_called_once_with("AAPL")
```

### 2. Patch Multiple Objects

```python
def test_screener_sync_command(mocker):
    # Patch multiple dependencies at once
    mock_config = mocker.patch('src.cmd.nasdaq_screener_sync.main.CONFIG')
    mock_load_screener = mocker.patch('src.cmd.nasdaq_screener_sync.main.load_screener_files_from_directory')
    mock_pipeline = mocker.patch('src.cmd.nasdaq_screener_sync.main.CompanyPipeline')
    
    # Configure mocks
    mock_config.get_equities_config.return_value = mocker.Mock()
    mock_load_screener.return_value = [mocker.Mock()]
    mock_pipeline.return_value.process_companies.return_value = mocker.Mock(successful=1)
    
    # Import and test after patching
    from src.cmd.nasdaq_screener_sync.main import main
    
    result = main()
    
    # All mocks are automatically cleaned up after test
```

### 3. Context Manager Mocking

```python
def test_database_transaction(mocker):
    # Mock database session context manager
    mock_session = mocker.MagicMock()
    mock_session.__enter__.return_value = mock_session
    mock_session.__exit__.return_value = None
    
    mock_create_session = mocker.patch('sqlalchemy.orm.sessionmaker')
    mock_create_session.return_value = lambda: mock_session
    
    # Test code that uses 'with session:' pattern
    # The context manager behavior is properly mocked
```

## Fixture Integration

### Example: Reusable Mock Fixtures

```python
import pytest

@pytest.fixture
def mock_company_repo(mocker):
    """Reusable mock repository fixture."""
    mock_repo = mocker.MagicMock()
    
    # Default behavior
    mock_repo.find_by_symbol.return_value = None
    mock_repo.create_company.return_value = mocker.Mock(id=1)
    
    return mock_repo

@pytest.fixture  
def mock_db_config(mocker):
    """Reusable database configuration mock."""
    return mocker.Mock(
        host="localhost",
        port=5432,
        database="test_db",
        username="test_user",
        password="test_pass",
        connection_string=lambda: "postgresql://test_user:test_pass@localhost:5432/test_db"
    )

# Use fixtures in tests
def test_with_fixtures(mock_company_repo, mock_db_config):
    from src.pipelines.companies.simple_pipeline import CompanyPipeline
    
    pipeline = CompanyPipeline(mock_db_config)
    # Test using the fixtures
```

## Best Practices for Options-Deep

### 1. Use Descriptive Mock Names
```python
def test_company_sync(mocker):
    mock_nasdaq_source = mocker.patch('src.data_sources.nasdaq.screener.load_screener_file')
    mock_db_repo = mocker.patch('src.repos.equities.companies.company_repository.CompanyRepository')
    
    # Clear what each mock represents
```

### 2. Group Related Patches
```python
def test_full_pipeline(mocker):
    # Group all data source mocks
    mock_nasdaq = mocker.patch('src.data_sources.nasdaq.screener.load_screener_file')
    mock_yahoo = mocker.patch('src.data_sources.yahoo_finance.yahoo_finance.fetch_quotes')
    
    # Group all database mocks  
    mock_config = mocker.patch('src.config.configuration.CONFIG')
    mock_repo = mocker.patch('src.repos.equities.companies.company_repository.CompanyRepository')
```

### 3. Verify Important Interactions
```python
def test_pipeline_error_handling(mocker):
    mock_repo = mocker.MagicMock()
    mock_repo.create_company.side_effect = Exception("Database error")
    
    # Test your pipeline
    pipeline = CompanyPipeline()
    pipeline.repository = mock_repo
    
    # Verify error handling
    with pytest.raises(Exception):
        pipeline.process_companies([mock_company])
    
    # Verify rollback was called or error was logged
```

## Running pytest-mock Tests

```bash
# Install and run
pip install pytest-mock
pytest tests/ -v

# Run with specific markers
pytest tests/ -m "not integration" -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## When to Use pytest-mock in Options-Deep

✅ **Use For:**
- Unit testing business logic
- Mocking external dependencies (APIs, files)
- Testing error handling paths
- Fast test execution

✅ **Advantages over unittest.mock:**
- Cleaner syntax with mocker fixture
- Automatic cleanup between tests
- Better pytest integration
- Simpler patch management

❌ **Still Avoid For:**
- Integration testing with real databases
- Testing actual SQL query behavior
- End-to-end workflow testing