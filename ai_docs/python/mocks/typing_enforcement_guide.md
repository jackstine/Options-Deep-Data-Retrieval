# Type Enforcement with unittest.mock, Faker, and Factory Boy

## Core Concepts

Type safety in Python testing is crucial for maintaining code quality and preventing runtime errors. When using mocking libraries with data generation tools, you can enforce type contracts to ensure your tests accurately reflect production behavior.

### Key Type Safety Features

- **`spec` parameter**: Enforces that mocked objects have the same interface as the original
- **`autospec` parameter**: Automatically creates specs based on introspection
- **`create_autospec()` function**: Creates auto-specced mocks with full type checking
- **`spec_set=True`**: Prevents adding non-existent attributes
- **Type hints with `TYPE_CHECKING`**: Provides IDE support without runtime overhead

## Pattern 1: Type-Safe Repository Mocking

### Basic Type Enforcement with `spec`

```python
from unittest.mock import MagicMock, create_autospec
from typing import TYPE_CHECKING, List, Optional, cast
from faker import Faker
from faker.providers import BaseProvider

from src.repos.equities.companies.company_repository import CompanyRepository
from src.data_sources.models.company import Company

if TYPE_CHECKING:
    from src.database.equities.tables.company import Company as CompanyDB

class TypedStockMarketProvider(BaseProvider):
    """Type-safe custom provider for financial data."""
    
    def stock_ticker(self) -> str:
        """Generate a realistic 4-character stock ticker."""
        return ''.join(self.random_choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', length=4))
    
    def stock_sector(self) -> str:
        """Generate a realistic stock sector."""
        sectors = ['Technology', 'Healthcare', 'Financial Services', 'Consumer Discretionary']
        return self.random_element(sectors)
    
    def market_cap(self) -> int:
        """Generate realistic market capitalization."""
        category = self.random_element(['small', 'mid', 'large', 'mega'])
        if category == 'small':
            return self.random_int(300_000_000, 2_000_000_000)
        elif category == 'mid':
            return self.random_int(2_000_000_000, 10_000_000_000)
        elif category == 'large':
            return self.random_int(10_000_000_000, 200_000_000_000)
        else:  # mega
            return self.random_int(200_000_000_000, 3_000_000_000_000)

class TestTypedRepositoryMocking(unittest.TestCase):
    
    def setUp(self):
        self.fake = Faker()
        self.fake.add_provider(TypedStockMarketProvider)
        Faker.seed(12345)
    
    def create_typed_company_mock(self, **overrides) -> Company:
        """Create a type-safe Company mock with Faker data."""
        
        # Use spec to enforce Company interface
        mock_company = MagicMock(spec=Company)
        
        # Generate realistic data with proper types
        default_data = {
            'id': self.fake.random_int(1, 10000),
            'company_name': self.fake.company(),
            'exchange': self.fake.random_element(['NASDAQ', 'NYSE', 'AMEX']),
            'sector': self.fake.stock_sector(),
            'industry': self.fake.bs().title(),
            'market_cap': self.fake.market_cap(),
            'country': 'United States',
            'active': True
        }
        
        # Apply overrides
        default_data.update(overrides)
        
        # Set attributes with type enforcement
        for attr, value in default_data.items():
            setattr(mock_company, attr, value)
        
        return mock_company
    
    def test_autospec_repository_interface(self):
        """Test repository with full interface enforcement."""
        
        # Create auto-specced mock that enforces CompanyRepository interface
        mock_repo = create_autospec(CompanyRepository, spec_set=True)
        
        # Generate typed test data
        expected_company = self.create_typed_company_mock(
            company_name="Test Corp",
            sector="Technology"
        )
        
        # Configure mock with proper return types
        mock_repo.find_by_symbol.return_value = expected_company
        mock_repo.find_by_sector.return_value = [expected_company]
        
        # Test method calls - these will fail if method signatures don't match
        result = mock_repo.find_by_symbol("TEST")
        sector_results = mock_repo.find_by_sector("Technology")
        
        # Type-safe assertions
        self.assertEqual(result.company_name, "Test Corp")
        self.assertEqual(result.sector, "Technology")
        self.assertIsInstance(sector_results, list)
        self.assertEqual(len(sector_results), 1)
        
        # Verify method signatures were enforced
        mock_repo.find_by_symbol.assert_called_once_with("TEST")
        mock_repo.find_by_sector.assert_called_once_with("Technology")
        
        # This would raise AttributeError - method doesn't exist
        # mock_repo.nonexistent_method()  # Uncomment to test
    
    def test_optional_return_types(self):
        """Test handling Optional return types with type safety."""
        
        mock_repo = create_autospec(CompanyRepository, spec_set=True)
        
        # Test case 1: Company found (80% chance with Faker)
        company_exists = self.fake.boolean(chance_of_getting_true=80)
        
        if company_exists:
            mock_company = self.create_typed_company_mock(
                company_name=self.fake.company(),
                market_cap=self.fake.market_cap()
            )
            mock_repo.find_by_symbol.return_value = mock_company
        else:
            mock_repo.find_by_symbol.return_value = None
        
        # Test the Optional[Company] return type
        result: Optional[Company] = mock_repo.find_by_symbol("AAPL")
        
        if result is not None:
            # Type checker knows this is Company, not Optional[Company]
            self.assertIsInstance(result.company_name, str)
            self.assertIsInstance(result.market_cap, int)
            self.assertGreater(result.market_cap, 0)
        else:
            self.assertIsNone(result)
    
    def test_list_return_types(self):
        """Test type-safe list handling with varied data."""
        
        mock_repo = create_autospec(CompanyRepository, spec_set=True)
        
        # Generate list of companies with varied sectors
        sectors = ["Technology", "Healthcare", "Financial Services"]
        typed_companies: List[Company] = []
        
        for sector in sectors:
            # Create 2-5 companies per sector
            company_count = self.fake.random_int(2, 5)
            for _ in range(company_count):
                company = self.create_typed_company_mock(sector=sector)
                typed_companies.append(company)
        
        # Mock returns typed list
        mock_repo.find_all.return_value = typed_companies
        
        # Test with type hints
        all_companies: List[Company] = mock_repo.find_all()
        
        # Type-safe operations
        self.assertIsInstance(all_companies, list)
        self.assertGreater(len(all_companies), 0)
        
        for company in all_companies:
            self.assertIn(company.sector, sectors)
            self.assertIsInstance(company.company_name, str)
            self.assertIsInstance(company.market_cap, int)
```

## Pattern 2: Type-Safe Factory Boy Integration

### Enhanced Factory with Type Enforcement

```python
import factory
from factory import Faker as FactoryFaker, SubFactory
from factory.alchemy import SQLAlchemyModelFactory
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.database.equities.tables.company import Company as CompanyDB
    from src.database.equities.tables.ticker import Ticker as TickerDB

class TypedCompanyFactory(SQLAlchemyModelFactory):
    """Type-safe Company factory with realistic data generation."""
    
    class Meta:
        model = 'src.database.equities.tables.company.Company'
        sqlalchemy_session_persistence = "commit"
    
    # Generate typed, realistic data
    company_name: str = FactoryFaker('company')
    exchange: str = factory.Iterator(['NASDAQ', 'NYSE', 'AMEX'])
    sector: str = factory.LazyFunction(lambda: TypedStockMarketProvider().stock_sector())
    industry: str = FactoryFaker('bs')
    country: str = 'United States'
    market_cap: int = factory.LazyFunction(lambda: TypedStockMarketProvider().market_cap())
    active: bool = True
    source: str = 'TYPED_FACTORY'
    
    @factory.post_generation
    def validate_types(self, create, extracted, **kwargs):
        """Post-generation validation to ensure type safety."""
        if not create:
            return
        
        # Type validation
        assert isinstance(self.company_name, str), f"company_name must be str, got {type(self.company_name)}"
        assert isinstance(self.market_cap, int), f"market_cap must be int, got {type(self.market_cap)}"
        assert isinstance(self.active, bool), f"active must be bool, got {type(self.active)}"
        assert self.exchange in ['NASDAQ', 'NYSE', 'AMEX'], f"Invalid exchange: {self.exchange}"

class TypedTickerFactory(SQLAlchemyModelFactory):
    """Type-safe Ticker factory."""
    
    class Meta:
        model = 'src.database.equities.tables.ticker.Ticker'
        sqlalchemy_session_persistence = "commit"
    
    symbol: str = factory.LazyFunction(lambda: TypedStockMarketProvider().stock_ticker())
    company = SubFactory(TypedCompanyFactory)
    primary_ticker: bool = True

def create_typed_mock_from_factory(factory_class, spec_class, **kwargs):
    """Helper function to create type-safe mocks from factory data."""
    
    # Generate data using factory (but don't save to DB)
    factory_instance = factory_class.build(**kwargs)
    
    # Create spec'd mock
    typed_mock = MagicMock(spec=spec_class)
    
    # Copy factory data to mock with type safety
    for field_name in spec_class.__annotations__:
        if hasattr(factory_instance, field_name):
            value = getattr(factory_instance, field_name)
            setattr(typed_mock, field_name, value)
    
    return typed_mock

class TestTypedFactoryIntegration(unittest.TestCase):
    
    def setUp(self):
        self.fake = Faker()
        self.fake.add_provider(TypedStockMarketProvider)
    
    def test_typed_factory_with_mock_repository(self):
        """Test Factory Boy data with type-safe repository mocks."""
        
        # Create auto-specced repository
        mock_repo = create_autospec(CompanyRepository, spec_set=True)
        
        # Generate realistic companies using factory
        factory_companies = TypedCompanyFactory.build_batch(5)
        
        # Convert to typed mocks
        typed_mocks = []
        for factory_company in factory_companies:
            mock_company = create_typed_mock_from_factory(
                TypedCompanyFactory, 
                Company,
                company_name=factory_company.company_name,
                sector=factory_company.sector,
                market_cap=factory_company.market_cap
            )
            typed_mocks.append(mock_company)
        
        # Configure repository mock
        mock_repo.find_by_sector.return_value = typed_mocks
        
        # Test with type safety
        result = mock_repo.find_by_sector("Technology")
        
        # Type-safe assertions
        self.assertIsInstance(result, list)
        for company in result:
            self.assertIsInstance(company.company_name, str)
            self.assertIsInstance(company.market_cap, int)
            self.assertGreater(company.market_cap, 0)
    
    def test_typed_factory_validation(self):
        """Test that factories generate type-valid data."""
        
        # Create companies with type validation
        companies = TypedCompanyFactory.build_batch(10)
        
        for company in companies:
            # These assertions will pass due to post_generation validation
            self.assertIsInstance(company.company_name, str)
            self.assertIsInstance(company.market_cap, int)
            self.assertIsInstance(company.active, bool)
            self.assertIn(company.exchange, ['NASDAQ', 'NYSE', 'AMEX'])
    
    def test_relationship_type_safety(self):
        """Test type safety in factory relationships."""
        
        # Create company with ticker using SubFactory
        company = TypedCompanyFactory()
        ticker = TypedTickerFactory(company=company)
        
        # Type-safe relationship verification
        self.assertEqual(ticker.company.id, company.id)
        self.assertIsInstance(ticker.symbol, str)
        self.assertEqual(len(ticker.symbol), 4)
        self.assertTrue(ticker.symbol.isupper())
```

## Pattern 3: Complete Type-Safe Integration

### Combining All Three Libraries with Full Type Safety

```python
class TypedIntegrationTest(unittest.TestCase):
    """Complete integration of unittest.mock + Faker + Factory Boy with type safety."""
    
    def setUp(self):
        self.fake = Faker()
        self.fake.add_provider(TypedStockMarketProvider)
        Faker.seed(54321)
    
    def create_typed_pipeline_test(self):
        """Example of full integration with type safety."""
        
        # 1. Create auto-specced repository mock
        mock_repo = create_autospec(CompanyRepository, spec_set=True)
        
        # 2. Generate test data using Factory Boy
        input_companies = TypedCompanyFactory.build_batch(20)
        
        # 3. Configure mock responses with Faker-generated realistic data
        def mock_find_by_symbol(symbol: str) -> Optional[Company]:
            # Use Faker to decide if company exists (20% chance)
            exists = self.fake.boolean(chance_of_getting_true=20)
            
            if exists:
                # Return existing company mock with Faker data
                return self.create_typed_company_mock(
                    company_name=self.fake.company(),
                    sector=self.fake.stock_sector(),
                    market_cap=self.fake.market_cap()
                )
            return None
        
        def mock_create_company(company_data: Company) -> Company:
            # Simulate successful creation with generated ID
            created_company = self.create_typed_company_mock(
                id=self.fake.random_int(1, 10000),
                company_name=company_data.company_name,
                sector=company_data.sector,
                market_cap=company_data.market_cap
            )
            return created_company
        
        def mock_update_company(company_data: Company) -> Company:
            # Simulate successful update
            updated_company = self.create_typed_company_mock(
                id=company_data.id,
                company_name=company_data.company_name,
                sector=company_data.sector,
                market_cap=company_data.market_cap
            )
            return updated_company
        
        # Configure mock methods with type-safe side effects
        mock_repo.find_by_symbol.side_effect = mock_find_by_symbol
        mock_repo.create_company.side_effect = mock_create_company
        mock_repo.update_company.side_effect = mock_update_company
        
        # 4. Test pipeline with type safety
        from src.pipelines.companies.simple_pipeline import CompanyPipeline
        
        # Mock configuration
        mock_config = MagicMock()
        mock_config.connection_string.return_value = "postgresql://test"
        
        # Create pipeline with mocked repository
        pipeline = CompanyPipeline(mock_config)
        pipeline.repository = mock_repo
        
        # Process companies
        result = pipeline.process_companies(input_companies)
        
        # Type-safe verification
        self.assertIsInstance(result.successful, list)
        self.assertIsInstance(result.failed, list)
        
        total_processed = len(result.successful) + len(result.failed)
        self.assertEqual(total_processed, 20)
        
        # Verify mock interactions with correct types
        self.assertEqual(mock_repo.find_by_symbol.call_count, 20)
        
        # All calls should have string arguments (ticker symbols)
        for call in mock_repo.find_by_symbol.call_args_list:
            symbol_arg = call[0][0]
            self.assertIsInstance(symbol_arg, str)
    
    def test_typed_error_scenarios(self):
        """Test type-safe error handling."""
        
        from src.utils.exceptions import ValidationError, DatabaseError
        
        mock_repo = create_autospec(CompanyRepository, spec_set=True)
        
        # Generate typed error scenarios with Faker
        error_scenarios = [
            ValidationError(f"Invalid ticker: {self.fake.stock_ticker()}"),
            DatabaseError(f"Connection timeout after {self.fake.random_int(5, 30)}s"),
            ValueError(f"Market cap must be positive, got {self.fake.random_int(-1000, -1)}")
        ]
        
        # Mock raises typed exceptions
        mock_repo.create_company.side_effect = self.fake.random_element(error_scenarios)
        
        # Create test company with Factory Boy
        test_company = TypedCompanyFactory.build()
        
        # Test typed exception handling
        with self.assertRaises((ValidationError, DatabaseError, ValueError)) as context:
            mock_repo.create_company(test_company)
        
        # Exception message should be realistic
        self.assertIsInstance(str(context.exception), str)
        self.assertGreater(len(str(context.exception)), 0)
    
    def test_performance_with_type_safety(self):
        """Test performance impact of type-safe testing."""
        
        import time
        
        # Generate large dataset with type safety
        start_time = time.time()
        
        typed_companies = TypedCompanyFactory.build_batch(1000)
        
        generation_time = time.time() - start_time
        
        # Verify all generated data maintains type safety
        for company in typed_companies[:10]:  # Sample verification
            self.assertIsInstance(company.company_name, str)
            self.assertIsInstance(company.market_cap, int)
            self.assertIsInstance(company.active, bool)
        
        # Performance should be reasonable
        self.assertLess(generation_time, 5.0)  # Less than 5 seconds
        
        print(f"Generated 1000 type-safe companies in {generation_time:.2f}s")
```

## Advanced Type Safety Patterns

### 1. Generic Type Helpers

```python
from typing import TypeVar, Generic, List, Callable, Any
from unittest.mock import MagicMock

T = TypeVar('T')

class TypedMockBuilder(Generic[T]):
    """Generic helper for creating type-safe mocks."""
    
    def __init__(self, spec_class: type, fake: Faker):
        self.spec_class = spec_class
        self.fake = fake
    
    def create_mock(self, **overrides) -> T:
        """Create a type-safe mock with Faker data."""
        mock_obj = MagicMock(spec=self.spec_class)
        
        # Generate default values based on type hints
        if hasattr(self.spec_class, '__annotations__'):
            for field_name, field_type in self.spec_class.__annotations__.items():
                if field_name not in overrides:
                    default_value = self._generate_value_for_type(field_type)
                    setattr(mock_obj, field_name, default_value)
        
        # Apply overrides
        for key, value in overrides.items():
            setattr(mock_obj, key, value)
        
        return cast(T, mock_obj)
    
    def _generate_value_for_type(self, field_type: type) -> Any:
        """Generate appropriate Faker value based on type."""
        if field_type == str:
            return self.fake.word()
        elif field_type == int:
            return self.fake.random_int(1, 1000000)
        elif field_type == bool:
            return self.fake.boolean()
        elif field_type == float:
            return self.fake.pyfloat(positive=True)
        else:
            return None

# Usage
def test_generic_typed_mocks():
    fake = Faker()
    fake.add_provider(TypedStockMarketProvider)
    
    company_builder = TypedMockBuilder[Company](Company, fake)
    
    typed_company = company_builder.create_mock(
        company_name=fake.company(),
        sector=fake.stock_sector()
    )
    
    # Type checker knows this is Company
    assert isinstance(typed_company.company_name, str)
```

### 2. Type-Safe Configuration Mocking

```python
from dataclasses import dataclass
from typing import Protocol

@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    username: str
    password: str

class ConfigProtocol(Protocol):
    def get_database_config(self) -> DatabaseConfig: ...

def test_typed_config_mocking():
    """Test configuration mocking with full type safety."""
    
    fake = Faker()
    fake.add_provider(TypedStockMarketProvider)
    
    # Create typed mock configuration
    mock_config = MagicMock(spec=ConfigProtocol)
    
    # Generate realistic config with Faker
    realistic_db_config = DatabaseConfig(
        host=fake.hostname(),
        port=fake.random_int(5432, 5439),
        database=f"options_deep_{fake.word()}",
        username=fake.user_name(),
        password=fake.password(length=16)
    )
    
    mock_config.get_database_config.return_value = realistic_db_config
    
    # Test with type safety
    config: DatabaseConfig = mock_config.get_database_config()
    
    # Type-safe assertions
    assert isinstance(config.host, str)
    assert isinstance(config.port, int)
    assert 5432 <= config.port <= 5439
    assert "options_deep" in config.database
```

## Best Practices for Type-Safe Testing

### 1. Always Use `spec` or `autospec`

```python
# ✅ Good: Type-safe mock
mock_repo = create_autospec(CompanyRepository, spec_set=True)

# ❌ Bad: No type checking
mock_repo = MagicMock()  # Can have any attribute/method
```

### 2. Combine Type Hints with Runtime Validation

```python
def create_validated_company_mock(fake: Faker, **overrides) -> Company:
    """Create type-safe company mock with validation."""
    
    mock_company = MagicMock(spec=Company)
    
    # Generate with type validation
    data = {
        'company_name': fake.company(),
        'market_cap': fake.market_cap(),
        'sector': fake.stock_sector(),
        **overrides
    }
    
    # Runtime type validation
    assert isinstance(data['company_name'], str)
    assert isinstance(data['market_cap'], int)
    assert data['market_cap'] > 0
    
    for key, value in data.items():
        setattr(mock_company, key, value)
    
    return mock_company
```

### 3. Use TYPE_CHECKING for Development-Time Types

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # These imports are only for type checking, not runtime
    from src.database.equities.tables.company import Company as CompanyDB
    from sqlalchemy.orm import Session

def create_typed_db_session_mock() -> 'Session':
    """Create properly typed database session mock."""
    from unittest.mock import create_autospec
    
    # Import here to avoid circular dependencies
    from sqlalchemy.orm import Session
    
    return create_autospec(Session, spec_set=True)
```

## Error Handling with Type Safety

### Common Type Safety Issues and Solutions

```python
class TypeSafetyTest(unittest.TestCase):
    
    def test_optional_handling_with_types(self):
        """Properly handle Optional types in mocks."""
        
        mock_repo = create_autospec(CompanyRepository)
        fake = Faker()
        fake.add_provider(TypedStockMarketProvider)
        
        # Mock method that returns Optional[Company]
        def mock_find_optional(symbol: str) -> Optional[Company]:
            if fake.boolean(chance_of_getting_true=70):
                return MagicMock(
                    spec=Company,
                    company_name=fake.company(),
                    sector=fake.stock_sector()
                )
            return None
        
        mock_repo.find_by_symbol.side_effect = mock_find_optional
        
        # Type-safe usage
        result: Optional[Company] = mock_repo.find_by_symbol("TEST")
        
        # Proper Optional handling
        if result is not None:
            # Type checker knows result is Company here
            self.assertIsInstance(result.company_name, str)
        else:
            # Handle None case
            self.assertIsNone(result)
    
    def test_list_type_safety(self):
        """Ensure list return types are properly typed."""
        
        mock_repo = create_autospec(CompanyRepository)
        fake = Faker()
        fake.add_provider(TypedStockMarketProvider)
        
        # Generate typed list
        companies: List[Company] = [
            MagicMock(
                spec=Company,
                company_name=fake.company(),
                sector=fake.stock_sector()
            )
            for _ in range(5)
        ]
        
        mock_repo.find_all.return_value = companies
        
        # Type-safe list operations
        result: List[Company] = mock_repo.find_all()
        
        # List comprehension with type safety
        tech_companies = [c for c in result if c.sector == "Technology"]
        
        self.assertIsInstance(result, list)
        self.assertIsInstance(tech_companies, list)
```

## Performance Considerations

### Type Safety vs. Performance

```python
def test_performance_with_type_safety():
    """Measure performance impact of type-safe testing."""
    
    import time
    
    fake = Faker()
    fake.add_provider(TypedStockMarketProvider)
    
    # Time regular mock creation
    start_time = time.time()
    regular_mocks = [MagicMock() for _ in range(1000)]
    regular_time = time.time() - start_time
    
    # Time type-safe mock creation  
    start_time = time.time()
    typed_mocks = [
        MagicMock(spec=Company) for _ in range(1000)
    ]
    typed_time = time.time() - start_time
    
    # Time factory-generated mocks
    start_time = time.time()
    factory_mocks = TypedCompanyFactory.build_batch(1000)
    factory_time = time.time() - start_time
    
    print(f"Regular mocks: {regular_time:.3f}s")
    print(f"Typed mocks: {typed_time:.3f}s") 
    print(f"Factory mocks: {factory_time:.3f}s")
    
    # Type safety should not significantly impact performance
    assert typed_time < regular_time * 2  # Less than 2x slower
```

## Integration Testing with Type Safety

### Full Integration Example

```python
@pytest.mark.integration
def test_full_typed_integration(db_session):
    """Complete integration test with type safety."""
    
    # Setup
    fake = Faker()
    fake.add_provider(TypedStockMarketProvider)
    
    # Create real database objects using factories
    real_companies = TypedCompanyFactory.create_batch(
        10, 
        _session=db_session
    )
    
    # Create type-safe mocks for external services
    mock_api = create_autospec('src.external.market_data_api.MarketDataAPI')
    
    # Configure mock with realistic responses
    def mock_get_company_data(symbol: str) -> dict:
        return {
            'symbol': symbol,
            'name': fake.company(),
            'sector': fake.stock_sector(),
            'market_cap': fake.market_cap(),
            'last_updated': fake.date_time_this_year().isoformat()
        }
    
    mock_api.get_company_data.side_effect = mock_get_company_data
    
    # Test service that combines database and external API
    from src.services.company_enrichment_service import CompanyEnrichmentService
    
    service = CompanyEnrichmentService(db_session, mock_api)
    
    # Process companies with type safety
    enriched_companies = service.enrich_companies(
        [c.ticker.symbol for c in real_companies]
    )
    
    # Type-safe verification
    assert len(enriched_companies) == 10
    
    for company in enriched_companies:
        assert isinstance(company.company_name, str)
        assert isinstance(company.market_cap, int)
        assert company.market_cap > 0
    
    # Verify mock interactions
    assert mock_api.get_company_data.call_count == 10
```

## Summary

Type enforcement in Python testing with unittest.mock, Faker, and Factory Boy provides:

✅ **Benefits:**
- **Compile-time error detection** with type checkers
- **Interface enforcement** prevents invalid mock usage
- **Realistic test data** with proper types
- **Better IDE support** with autocomplete and type hints
- **Refactoring safety** - type mismatches are caught early

✅ **Key Techniques:**
- Use `create_autospec()` and `spec=` for interface enforcement
- Combine Faker providers with typed data generation
- Use Factory Boy post-generation hooks for type validation
- Leverage `TYPE_CHECKING` for development-time type imports
- Create generic helpers for common type-safe patterns

✅ **When to Use:**
- Large codebases where type safety is critical
- Integration tests that mock external services
- Performance testing with realistic, varied data
- APIs with strict interface contracts
- Team development where consistency is important

This approach ensures your tests are both realistic and type-safe, catching errors before they reach production while maintaining the flexibility to test with varied, realistic data.