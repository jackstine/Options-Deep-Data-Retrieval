# pgmock Usage Guide for Options-Deep

## Core Concepts

pgmock is a specialized library for mocking PostgreSQL queries at the SQL level. Instead of mocking database connections, it intercepts and mocks specific SQL queries, making it ideal for testing query logic and SQLAlchemy operations.

### Installation
```bash
pip install pgmock
```

### Key Features
- **Query-level mocking**: Mock specific SQL queries and subqueries
- **SQLAlchemy integration**: Works with SQLAlchemy ORM queries
- **Query inspection**: Capture and verify generated SQL
- **Fine-grained control**: Mock individual parts of complex queries

## Basic pgmock Setup

### Example: Mock a Simple Repository Query

```python
import pgmock
from sqlalchemy import create_engine, text
from src.repos.equities.companies.company_repository import CompanyRepository

def test_company_repository_with_pgmock():
    """Test repository query logic without database."""
    
    # Create in-memory SQLite engine (pgmock works with any SQLAlchemy engine)
    engine = create_engine("sqlite:///:memory:")
    
    # Mock data to return
    mock_company_data = [
        {'id': 1, 'company_name': 'Apple Inc.', 'sector': 'Technology', 'symbol': 'AAPL'},
        {'id': 2, 'company_name': 'Microsoft Corp.', 'sector': 'Technology', 'symbol': 'MSFT'}
    ]
    
    # Create pgmock context
    with pgmock.mock(engine) as mocker:
        # Mock the query that finds companies by sector
        mocker.patch(
            pgmock.sql("SELECT * FROM companies WHERE sector = ?"),
            rows=mock_company_data,
            cols=['id', 'company_name', 'sector', 'symbol']
        )
        
        # Test your repository code
        repo = CompanyRepository()
        repo.engine = engine
        
        # This will use the mocked query result
        tech_companies = repo.find_by_sector("Technology")
        
        # Verify the mock data was returned
        assert len(tech_companies) == 2
        assert tech_companies[0]['company_name'] == 'Apple Inc.'
        
        # Verify the correct query was executed
        assert len(mocker.renderings) == 1
        executed_sql = mocker.renderings[0]
        assert "WHERE sector" in executed_sql
```

## Mocking Complex SQLAlchemy Queries

### Example: Mock Company Statistics Query

```python
def test_company_sector_statistics(db_session):
    """Test complex aggregation query with pgmock."""
    
    # Mock data for sector statistics
    mock_stats = [
        {'sector': 'Technology', 'company_count': 150, 'avg_market_cap': 250000000000},
        {'sector': 'Healthcare', 'company_count': 89, 'avg_market_cap': 45000000000},
        {'sector': 'Financial', 'company_count': 67, 'avg_market_cap': 78000000000}
    ]
    
    with pgmock.mock(db_session.bind) as mocker:
        # Mock the aggregation query
        mocker.patch(
            pgmock.sql("""
                SELECT 
                    sector,
                    COUNT(*) as company_count,
                    AVG(market_cap) as avg_market_cap
                FROM companies 
                WHERE active = true
                GROUP BY sector
                ORDER BY company_count DESC
            """),
            rows=mock_stats,
            cols=['sector', 'company_count', 'avg_market_cap']
        )
        
        from src.repos.equities.companies.company_repository import CompanyRepository
        
        repo = CompanyRepository()
        repo.session = db_session
        
        # Execute the query
        stats = repo.get_sector_statistics()
        
        # Verify results
        assert len(stats) == 3
        assert stats[0]['sector'] == 'Technology'
        assert stats[0]['company_count'] == 150
        
        # Verify query was executed
        assert len(mocker.renderings) >= 1
```

## Mocking Subqueries

### Example: Mock Complex Join Query

```python
def test_companies_with_recent_price_data():
    """Test query that joins companies with recent price data."""
    
    # Mock data for companies with recent prices
    mock_results = [
        {
            'company_id': 1,
            'company_name': 'Apple Inc.',
            'symbol': 'AAPL',
            'latest_price': 150.25,
            'price_date': '2025-01-15'
        },
        {
            'company_id': 2, 
            'company_name': 'Microsoft Corp.',
            'symbol': 'MSFT',
            'latest_price': 380.75,
            'price_date': '2025-01-15'
        }
    ]
    
    engine = create_engine("sqlite:///:memory:")
    
    with pgmock.mock(engine) as mocker:
        # Mock the subquery that gets latest prices
        latest_price_subquery = pgmock.subquery('latest_prices')
        mocker.patch(
            latest_price_subquery,
            rows=[
                {'ticker_id': 1, 'latest_price': 150.25, 'price_date': '2025-01-15'},
                {'ticker_id': 2, 'latest_price': 380.75, 'price_date': '2025-01-15'}
            ],
            cols=['ticker_id', 'latest_price', 'price_date']
        )
        
        # Mock the main query
        main_query = pgmock.sql("""
            SELECT 
                c.id as company_id,
                c.company_name,
                t.symbol,
                lp.latest_price,
                lp.price_date
            FROM companies c
            JOIN tickers t ON t.company_id = c.id
            JOIN (latest_prices) lp ON lp.ticker_id = t.id
            WHERE c.active = true
            ORDER BY lp.latest_price DESC
        """)
        
        mocker.patch(
            main_query,
            rows=mock_results,
            cols=['company_id', 'company_name', 'symbol', 'latest_price', 'price_date']
        )
        
        # Execute query through your repository
        from src.repos.equities.companies.company_repository import CompanyRepository
        
        repo = CompanyRepository()
        repo.engine = engine
        
        companies_with_prices = repo.get_companies_with_latest_prices()
        
        assert len(companies_with_prices) == 2
        assert companies_with_prices[0]['company_name'] == 'Apple Inc.'
        assert companies_with_prices[0]['latest_price'] == 150.25
```

## Testing SQLAlchemy ORM Queries

### Example: Mock ORM-Generated SQL

```python
from sqlalchemy.orm import sessionmaker
from src.database.equities.tables.company import Company

def test_orm_query_with_pgmock():
    """Test SQLAlchemy ORM query with pgmock."""
    
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Mock data
    mock_companies = [
        {'id': 1, 'company_name': 'Apple Inc.', 'sector': 'Technology'},
        {'id': 2, 'company_name': 'Google Inc.', 'sector': 'Technology'}
    ]
    
    with pgmock.mock(engine) as mocker:
        # Mock ORM-generated query
        # Note: pgmock can intercept queries generated by SQLAlchemy ORM
        mocker.patch(
            pgmock.sql_containing("FROM companies"),  # Match any query from companies table
            rows=mock_companies,
            cols=['id', 'company_name', 'sector']
        )
        
        # Use SQLAlchemy ORM
        tech_companies = session.query(Company).filter(Company.sector == 'Technology').all()
        
        # pgmock intercepted the ORM query and returned mock data
        assert len(tech_companies) == 2
        
        # Inspect what SQL was generated
        generated_queries = mocker.renderings
        assert len(generated_queries) >= 1
        assert "FROM companies" in generated_queries[0]
        assert "WHERE" in generated_queries[0]
```

## Mocking Data Pipeline Queries

### Example: Test Company Sync Process

```python
def test_company_sync_with_query_mocking():
    """Test the company synchronization process with query-level mocking."""
    
    engine = create_engine("sqlite:///:memory:")
    
    with pgmock.mock(engine) as mocker:
        # Mock query to check if company exists
        mocker.patch(
            pgmock.sql_containing("SELECT * FROM companies WHERE"),
            rows=[],  # Empty result = company doesn't exist
            cols=['id', 'company_name', 'exchange']
        )
        
        # Mock ticker existence check
        mocker.patch(
            pgmock.sql_containing("SELECT * FROM tickers WHERE symbol"),
            rows=[],  # Empty result = ticker doesn't exist
            cols=['id', 'symbol', 'company_id']
        )
        
        # Mock company insertion
        mocker.patch(
            pgmock.sql_containing("INSERT INTO companies"),
            rows=[{'id': 1}],  # Return generated ID
            cols=['id']
        )
        
        # Mock ticker insertion  
        mocker.patch(
            pgmock.sql_containing("INSERT INTO tickers"),
            rows=[{'id': 1}],
            cols=['id']
        )
        
        # Test your sync pipeline
        from src.pipelines.companies.simple_pipeline import CompanyPipeline
        
        # Create test company data
        from src.data_sources.models.company import Company as CompanyModel
        from src.data_sources.models.ticker import Ticker as TickerModel
        
        test_company = CompanyModel(
            id=None,
            ticker=TickerModel(symbol="TEST", company_id=None),
            company_name="Test Company",
            exchange="NASDAQ",
            sector="Technology",
            source="TEST"
        )
        
        # Mock database config
        class MockDBConfig:
            def connection_string(self):
                return str(engine.url)
        
        pipeline = CompanyPipeline(MockDBConfig())
        result = pipeline.process_companies([test_company])
        
        # Verify the sync worked
        assert len(result.successful) == 1
        
        # Verify the correct queries were executed
        executed_queries = mocker.renderings
        
        # Should have checked for existing company
        assert any("SELECT" in query and "companies" in query for query in executed_queries)
        
        # Should have inserted new company
        assert any("INSERT INTO companies" in query for query in executed_queries)
        
        # Should have inserted new ticker
        assert any("INSERT INTO tickers" in query for query in executed_queries)
```

## Advanced pgmock Features

### 1. Query Pattern Matching

```python
def test_flexible_query_matching():
    """Test different ways to match SQL queries."""
    
    engine = create_engine("sqlite:///:memory:")
    
    with pgmock.mock(engine) as mocker:
        # Exact SQL match
        mocker.patch(
            pgmock.sql("SELECT * FROM companies WHERE sector = ?"),
            rows=[{'id': 1, 'name': 'Test'}],
            cols=['id', 'name']
        )
        
        # Partial SQL match
        mocker.patch(
            pgmock.sql_containing("FROM companies"),
            rows=[{'id': 2, 'name': 'Test2'}],
            cols=['id', 'name'] 
        )
        
        # Regex match
        mocker.patch(
            pgmock.sql_regex(r"SELECT .* FROM companies WHERE \w+ = \?"),
            rows=[{'id': 3, 'name': 'Test3'}],
            cols=['id', 'name']
        )
```

### 2. Multiple Query Mocking

```python
def test_multiple_query_mocking():
    """Test mocking multiple related queries."""
    
    engine = create_engine("sqlite:///:memory:")
    
    with pgmock.mock(engine) as mocker:
        # Mock sequence of queries
        
        # First query: Get company
        mocker.patch(
            pgmock.sql_containing("SELECT * FROM companies"),
            rows=[{'id': 1, 'company_name': 'Apple Inc.'}],
            cols=['id', 'company_name']
        )
        
        # Second query: Get tickers for company  
        mocker.patch(
            pgmock.sql_containing("SELECT * FROM tickers WHERE company_id"),
            rows=[
                {'id': 1, 'symbol': 'AAPL', 'company_id': 1},
                {'id': 2, 'symbol': 'AAPL.O', 'company_id': 1}
            ],
            cols=['id', 'symbol', 'company_id']
        )
        
        # Third query: Get price history
        mocker.patch(
            pgmock.sql_containing("SELECT * FROM ticker_history"),
            rows=[
                {'id': 1, 'ticker_id': 1, 'close_price': 150.25, 'price_date': '2025-01-15'},
                {'id': 2, 'ticker_id': 1, 'close_price': 148.50, 'price_date': '2025-01-14'}
            ],
            cols=['id', 'ticker_id', 'close_price', 'price_date']
        )
        
        # Execute complex operation that uses all three queries
        # Your code here...
        
        # Verify all queries were executed
        assert len(mocker.renderings) >= 3
```

## Integration with Other Testing Tools

### Example: Combine with pytest-mock

```python
def test_repository_with_pgmock_and_pytest_mock(mocker):
    """Combine pgmock with pytest-mock for comprehensive testing."""
    
    # Use pytest-mock to mock external dependencies
    mock_config = mocker.patch('src.config.configuration.CONFIG')
    mock_config.get_equities_config.return_value = mocker.Mock(
        connection_string=lambda: "sqlite:///:memory:"
    )
    
    # Use pgmock to mock database queries
    engine = create_engine("sqlite:///:memory:")
    
    with pgmock.mock(engine) as pg_mocker:
        pg_mocker.patch(
            pgmock.sql_containing("SELECT * FROM companies"),
            rows=[{'id': 1, 'company_name': 'Test Company'}],
            cols=['id', 'company_name']
        )
        
        # Test your code that uses both mocked config and mocked queries
        from src.repos.equities.companies.company_repository import CompanyRepository
        
        repo = CompanyRepository()
        repo.engine = engine
        
        companies = repo.get_all_companies()
        
        # Verify both mocks worked
        assert len(companies) == 1
        mock_config.get_equities_config.assert_called_once()
```

## Best Practices for Options-Deep

### 1. Use pgmock for Query Logic Testing

```python
# Good: Test complex query logic
def test_complex_aggregation_query():
    with pgmock.mock(engine) as mocker:
        mocker.patch(
            pgmock.sql_containing("GROUP BY sector"),
            rows=mock_aggregated_data,
            cols=['sector', 'count', 'avg_market_cap']
        )
        # Test the query logic
```

### 2. Verify Generated SQL

```python
def test_query_generation():
    """Verify your code generates the expected SQL."""
    
    with pgmock.mock(engine) as mocker:
        # Set up mock
        mocker.patch(pgmock.sql_containing("FROM companies"), rows=[], cols=[])
        
        # Execute your code
        repo.find_by_sector("Technology")
        
        # Verify the SQL that was generated
        executed_sql = mocker.renderings[0]
        assert "WHERE sector = ?" in executed_sql
        assert "Technology" in str(mocker.parameters)
```

### 3. Test Query Performance Logic

```python
def test_query_optimization():
    """Test that your code generates efficient queries."""
    
    with pgmock.mock(engine) as mocker:
        mocker.patch(pgmock.sql_containing("FROM companies"), rows=[], cols=[])
        
        # Execute operation
        repo.bulk_update_companies(company_list)
        
        # Verify minimal number of queries executed
        assert len(mocker.renderings) <= 5  # Should be efficient
        
        # Verify no N+1 query problems
        assert not any("SELECT" in q for q in mocker.renderings[1:])
```

## When to Use pgmock in Options-Deep

✅ **Use For:**
- Testing complex SQL query logic
- Verifying generated SQL is correct
- Testing query optimization
- Mocking specific database operations
- Testing SQLAlchemy query construction

✅ **Benefits:**
- Tests actual SQL logic without database
- Can verify query performance characteristics  
- Intercepts ORM-generated queries
- Fine-grained control over query mocking

❌ **Don't Use For:**
- Simple business logic testing (use pytest-mock)
- Testing database schema or constraints
- Integration testing (use pytest-postgresql)
- Testing non-database code

❌ **Limitations:**
- More complex setup than simple mocking
- Requires understanding of generated SQL
- May not catch database-specific issues
- Limited to query-level mocking

## Running Tests with pgmock

```bash
# Install pgmock
pip install pgmock

# Run tests that use pgmock
pytest tests/unit/test_query_logic.py -v

# Run with SQL debugging
pytest tests/unit/test_query_logic.py -v -s

# Combine with other test types
pytest tests/ --ignore=tests/integration/ -v  # Skip integration tests
```