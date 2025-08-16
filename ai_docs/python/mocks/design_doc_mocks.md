# Python Mocking Libraries for PostgreSQL Database Testing

## Objective
Research and evaluate Python libraries and strategies for mocking PostgreSQL databases in testing environments.

## Findings

### 1. General Python Mocking Libraries

#### Built-in unittest.mock Module
- **Documentation**: [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- **Key Features**: Mock, MagicMock, AsyncMock, patch() decorator
- **Pros**: No external dependencies, comprehensive feature set, supports async mocking
- **Cons**: Verbose syntax, complex patch paths
- **Best For**: Legacy codebases, complex mocking scenarios requiring fine-grained control

#### pytest-mock Library
- **GitHub**: [pytest-dev/pytest-mock](https://github.com/pytest-dev/pytest-mock)
- **Documentation**: [pytest-mock docs](https://pytest-mock.readthedocs.io/)
- **Installation**: `pip install pytest-mock`
- **Key Features**: Simplified syntax via `mocker` fixture, automatic cleanup
- **Pros**: Cleaner syntax, seamless pytest integration, automatic mock management
- **Cons**: Requires pytest framework, additional dependency
- **Best For**: New projects using pytest, teams prioritizing code readability

#### Mock vs MagicMock
- **Mock**: Lightweight, requires explicit magic method setup
- **MagicMock**: Pre-implemented magic methods, convenient for complex objects
- **Recommendation**: Use MagicMock for database-like objects that use magic methods

### 2. PostgreSQL-Specific Mocking Solutions

#### pytest-postgresql (Recommended)
- **GitHub**: [ClearcodeHQ/pytest-postgresql](https://github.com/ClearcodeHQ/pytest-postgresql)
- **Documentation**: [pytest-postgresql docs](https://pytest-postgresql.readthedocs.io/)
- **Installation**: `pip install pytest-postgresql`
- **Features**: Creates temporary PostgreSQL instances, three fixture types
- **Pros**: Real PostgreSQL testing, excellent SQLAlchemy integration, active development
- **Cons**: Slower than mocking (~40ms per test), requires Docker/local PostgreSQL
- **Best For**: Integration testing where PostgreSQL-specific features are critical

#### testing.postgresql (Legacy)
- **GitHub**: [tk0miya/testing.postgresql](https://github.com/tk0miya/testing.postgresql)
- **PyPI**: [testing.postgresql](https://pypi.org/project/testing.postgresql/)
- **Installation**: `pip install testing.postgresql`
- **Features**: Simple API, factory pattern optimization
- **Pros**: No external dependencies, lightweight
- **Cons**: Unmaintained (last update 2017), limited modern Python support
- **Status**: Not recommended for new projects

#### pytest-pgsql
- **GitHub**: [CleanCut/pytest-pgsql](https://github.com/CleanCut/pytest-pgsql)
- **Installation**: `pip install pytest-pgsql`
- **Features**: Clean database testing plugin with automatic cleanup
- **Pros**: Two fixture types, good performance with transaction rollback
- **Cons**: Less flexible than pytest-postgresql

#### pgmock
- **GitHub**: [DiamondLightSource/pgmock](https://github.com/DiamondLightSource/pgmock)
- **Installation**: `pip install pgmock`
- **Features**: Query-level mocking, SQLAlchemy integration
- **Pros**: Fine-grained query control, excellent for testing query logic
- **Cons**: Complex setup, requires deep understanding of query structure
- **Best For**: Testing specific SQL query logic

### 3. Database Testing Strategies

#### Testing Approach Comparison
| Approach | Speed | Accuracy | Maintenance | Best For |
|----------|-------|----------|-------------|----------|
| Pure Mocking | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | Unit tests, isolation |
| SQLite In-Memory | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Simple CRUD, CI/CD |
| Transaction Rollback | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Integration tests |
| Fresh DB per Test | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | End-to-end tests |

#### Performance Benchmarks
- **Mocked Database**: ~0.01s per test
- **SQLite In-Memory**: ~0.1s per test  
- **PostgreSQL Local**: ~0.5s per test
- **PostgreSQL Remote**: ~2-5s per test

#### Test Data Management Tools
- **Factory Boy**: [FactoryBoy/factory_boy](https://github.com/FactoryBoy/factory_boy) - Recommended for creating realistic test data
- **Faker**: [joke2k/faker](https://github.com/joke2k/faker) - Generates realistic fake data
- **pytest fixtures**: [pytest fixtures docs](https://docs.pytest.org/en/stable/explanation/fixtures.html) - For reusable test data patterns

## Recommendations

### Layered Testing Strategy
1. **Unit Tests**: Use `pytest-mock` or `unittest.mock` for business logic testing
2. **Integration Tests**: Use `pytest-postgresql` for database interaction testing
3. **End-to-End Tests**: Use real PostgreSQL instances with full cleanup

### Library Selection by Use Case

#### For Unit Testing (Fast Feedback)
```python
# Use pytest-mock for clean syntax
def test_user_service_logic(mocker):
    mock_db = mocker.patch('myapp.services.db_connection')
    mock_db.execute.return_value = [{'id': 1, 'name': 'Test'}]
    result = UserService.get_active_users()
    assert len(result) == 1
```

#### For Integration Testing (Realistic Database Testing)
```python
# Use pytest-postgresql for real PostgreSQL testing
def test_user_repository_integration(postgresql):
    repo = UserRepository(postgresql)
    user = repo.create_user("Test User", "test@example.com")
    found_user = repo.get_by_email("test@example.com")
    assert found_user.name == "Test User"
```

#### For Performance-Critical Testing
- Use SQLite in-memory for simple CRUD operations
- Use transaction rollback strategy for medium complexity
- Reserve fresh databases for critical end-to-end tests

### Best Practices
1. **Use autospec**: Ensures mocks respect original interfaces
2. **Mock at boundaries**: Focus on external dependencies, not internal implementation
3. **Use dependency injection**: Makes code more testable
4. **Verify mock interactions**: Always assert that mocks were called as expected
5. **Keep mocks simple**: Avoid overly complex mock setups

## Implementation Considerations

### For Your PostgreSQL Project
1. **Primary Recommendation**: Use `pytest-postgresql` for database integration tests
2. **Secondary Option**: Use `pytest-mock` for unit tests of business logic
3. **Test Data**: Implement Factory Boy for generating realistic test data
4. **CI/CD**: Use SQLite for fast feedback, PostgreSQL for comprehensive testing

### Setup Priority
1. Install `pytest-postgresql` and `pytest-mock`
2. Configure test database fixtures ([pytest fixtures guide](https://docs.pytest.org/en/stable/explanation/fixtures.html))
3. Implement Factory Boy factories for your models ([Factory Boy docs](https://factoryboy.readthedocs.io/en/stable/))
4. Set up layered testing structure (unit/integration/e2e)
5. Configure CI/CD pipeline with both fast and comprehensive test suites

### Additional Resources
- **pytest Documentation**: [pytest.org](https://docs.pytest.org/)
- **SQLAlchemy Testing**: [SQLAlchemy Testing Guide](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
- **PostgreSQL Testing Best Practices**: [PostgreSQL Testing Wiki](https://wiki.postgresql.org/wiki/Testing)
- **Python Testing 101**: [Real Python Testing Guide](https://realpython.com/python-testing/)

### Specific to PostgreSQL Features
- Use `pytest-postgresql` when testing PostgreSQL-specific features (arrays, JSONB, custom types)
- Use SQLite in-memory for simple CRUD operations that don't rely on PostgreSQL-specific features
- Mock database connections when testing business logic that doesn't depend on specific database behavior