# unittest.mock Usage Guide for Options-Deep

## Core Concepts

unittest.mock is Python's built-in mocking library. It replaces real objects with mock objects that you can configure and verify.

### Key Classes
- **Mock**: Basic mock object
- **MagicMock**: Mock with magic methods pre-implemented
- **patch()**: Temporarily replace objects during tests

## Mocking Your Database Repository

### Example: Testing CompanyRepository without Database

```python
from unittest.mock import Mock, patch, MagicMock
from src.repos.equities.companies.company_repository import CompanyRepository
from src.data_sources.models.company import Company

def test_company_repository_find_by_symbol():
    # Create mock database session
    mock_session = MagicMock()
    
    # Configure what the query should return
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = Mock(
        id=1,
        company_name="Apple Inc.",
        ticker=Mock(symbol="AAPL")
    )
    
    # Test your repository
    repo = CompanyRepository()
    repo.session = mock_session  # Inject mock session
    
    result = repo.find_by_symbol("AAPL")
    
    # Verify behavior
    assert result.company_name == "Apple Inc."
    mock_session.query.assert_called_once()
    mock_query.filter.assert_called_once()
```

## Mocking External Data Sources

### Example: Testing NASDAQ Screener without File System

```python
from unittest.mock import patch, mock_open
from src.data_sources.nasdaq.screener import load_screener_file

@patch('builtins.open', new_callable=mock_open, read_data='''Symbol,Name,Market Cap,Country,Sector,Industry
AAPL,Apple Inc.,2800000000000,United States,Technology,Consumer Electronics
GOOGL,Alphabet Inc.,1600000000000,United States,Technology,Internet Content''')
@patch('pathlib.Path.exists', return_value=True)
def test_load_screener_file(mock_exists, mock_file):
    companies = load_screener_file("fake_file.csv")
    
    assert len(companies) == 2
    assert companies[0].company_name == "Apple Inc."
    assert companies[0].ticker.symbol == "AAPL"
    assert companies[1].company_name == "Alphabet Inc."
    assert companies[1].ticker.symbol == "GOOGL"
```

## Mocking Database Configuration

### Example: Testing Configuration Manager

```python
from unittest.mock import patch, Mock
from src.config.configuration import ConfigurationManager

@patch('src.config.configuration.os.getenv')
@patch('builtins.open', new_callable=mock_open, read_data='''{
    "databases": {
        "equities": {
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "username": "test_user"
        }
    }
}''')
@patch('pathlib.Path.exists', return_value=True)
def test_get_equities_config(mock_exists, mock_file, mock_getenv):
    # Mock environment variables
    mock_getenv.side_effect = lambda key, default=None: {
        'ENVIRONMENT': 'local',
        'OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD': 'test_password'
    }.get(key, default)
    
    config_manager = ConfigurationManager()
    db_config = config_manager.get_equities_config()
    
    assert db_config.host == "localhost"
    assert db_config.password == "test_password"
    assert db_config.database == "test_db"
```

## Mocking Company Data Pipeline

### Example: Testing Pipeline Processing

```python
from unittest.mock import Mock, patch
from src.pipelines.companies.simple_pipeline import CompanyPipeline

def test_company_pipeline_process():
    # Create mock repository
    mock_repo = Mock()
    mock_repo.find_by_symbol.return_value = None  # Company doesn't exist
    mock_repo.create_company.return_value = Mock(id=1)
    
    # Create mock companies
    mock_companies = [
        Mock(
            ticker=Mock(symbol="AAPL"),
            company_name="Apple Inc.",
            exchange="NASDAQ"
        ),
        Mock(
            ticker=Mock(symbol="GOOGL"), 
            company_name="Alphabet Inc.",
            exchange="NASDAQ"
        )
    ]
    
    # Test pipeline
    with patch.object(CompanyPipeline, '_get_repository', return_value=mock_repo):
        pipeline = CompanyPipeline()
        result = pipeline.process_companies(mock_companies)
        
        # Verify repository was called correctly
        assert mock_repo.find_by_symbol.call_count == 2
        assert mock_repo.create_company.call_count == 2
```

## Common Patterns for Options-Deep

### Pattern 1: Mock Database Connection

```python
@patch('src.config.configuration.CONFIG.get_equities_config')
def test_with_mock_db_config(mock_config):
    mock_config.return_value = Mock(
        connection_string=lambda: "postgresql://test:test@localhost/test"
    )
    
    # Your test code here
    # Database connection will use mocked configuration
```

### Pattern 2: Mock File Operations

```python
@patch('pathlib.Path.exists', return_value=True)
@patch('pathlib.Path.glob')
def test_screener_file_discovery(mock_glob, mock_exists):
    mock_glob.return_value = [
        Mock(name="nasdaq_screener_8_3_2025.csv"),
        Mock(name="nasdaq_screener_8_4_2025.csv")
    ]
    
    # Test code that discovers screener files
```

### Pattern 3: Mock SQLAlchemy Session

```python
def test_database_operations():
    mock_session = MagicMock()
    
    # Mock query chain
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [Mock(id=1, name="Test Company")]
    
    # Use mock_session in your tests
    # repo.session = mock_session
```

## Best Practices for Options-Deep

### 1. Mock at the Right Level
```python
# Good: Mock external dependencies
@patch('requests.get')  # Mock HTTP calls
@patch('psycopg2.connect')  # Mock database connection

# Avoid: Mocking internal business logic
# @patch('src.models.company.Company.validate')  # Too internal
```

### 2. Use Realistic Mock Data
```python
def create_mock_company():
    return Mock(
        id=1,
        company_name="Apple Inc.",
        ticker=Mock(symbol="AAPL"),
        sector="Technology",
        market_cap=2800000000000,
        exchange="NASDAQ"
    )
```

### 3. Verify Mock Interactions
```python
def test_company_creation():
    mock_repo = Mock()
    
    # Test your code
    service = CompanyService(mock_repo)
    service.create_company("AAPL", "Apple Inc.")
    
    # Verify the repository was called correctly
    mock_repo.create_company.assert_called_once_with(
        symbol="AAPL",
        name="Apple Inc."
    )
```

## Running Tests

```bash
# Run tests with unittest.mock
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_company_repository.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## When to Use unittest.mock in Options-Deep

✅ **Use For:**
- Testing business logic without database
- Mocking external API calls (Yahoo Finance, NASDAQ)
- Testing configuration loading
- Testing file operations

❌ **Avoid For:**
- Testing actual SQL queries (use pytest-postgresql instead)
- Testing database schema changes
- Integration testing between components
- Testing PostgreSQL-specific features