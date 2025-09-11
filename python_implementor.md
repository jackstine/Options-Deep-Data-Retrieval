# Python Implementation Style Guide for Options-Deep

## Overview

This condensed style guide provides practical patterns for Python senior engineers working on the Options-Deep codebase. It emphasizes type safety, clean architecture, and maintainable code based on established patterns in the existing codebase.

## Core Principles

1. **Type Safety First** - Use comprehensive type hints and protocols
2. **Protocol-Based Design** - Prefer structural typing over inheritance
3. **Generic Components** - Write reusable, type-safe generic classes
4. **Clean Architecture** - Separate data sources, repositories, and pipelines
5. **Functional Patterns** - Prefer immutable, functional approaches

## Essential Imports Pattern

Every module should start with these imports for modern Python typing:

```python
from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List, Protocol, TypeVar, Generic
from datetime import date
```

## 1. Class Design Patterns

### Data Source Pattern
```python
from src.data_sources.base.company_data_source import CompanyDataSource
from src.data_sources.models.company import Company

class NasdaqCompanySource(CompanyDataSource):
    """Concrete data source implementation."""
    
    @property
    def name(self) -> str:
        return "NASDAQ API"
    
    def get_companies(self) -> list[Company]:
        """Returns companies with comprehensive error handling."""
        dict_data = self._get_dict_of_stocks()
        if dict_data is None:
            return []
        return _convert_dict_to_stocks(dict_data)
    
    def is_available(self) -> bool:
        """Check availability before use."""
        try:
            api_key = en.ENVIRONMENT_VARIABLES.get_nasdaq_api_key()
            return api_key is not None
        except Exception:
            return False
```

### Pipeline Pattern
```python
class CompanyPipeline:
    """Pipeline with dependency injection and comprehensive logging."""
    
    def __init__(
        self,
        company_repo: CompanyRepository | None = None,
        ticker_repo: TickerRepository | None = None,
        ticker_history_repo: TickerHistoryRepository | None = None,
        logger: logging.Logger | None = None,
    ):
        self.company_repo = company_repo or CompanyRepository()
        self.ticker_repo = ticker_repo or TickerRepository()
        self.ticker_history_repo = ticker_history_repo or TickerHistoryRepository()
        self.logger = logger or logging.getLogger(__name__)
```

## 2. Type System Implementation

### Protocol Definitions
```python
from typing import Protocol, runtime_checkable

class DataModelProtocol(Protocol):
    """Structural typing for data models."""
    id: Optional[int]
    
    def to_dict(self) -> dict[str, Any]: ...
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DataModelProtocol: ...

@runtime_checkable
class Cacheable(Protocol):
    """Optional runtime validation."""
    def get_cache_key(self) -> str: ...
    def get_cache_ttl(self) -> int: ...
```

### Generic Repository Pattern
```python
TDataModel = TypeVar('TDataModel', bound=DataModelProtocol)
TDBModel = TypeVar('TDBModel', bound='DBModelProtocol')

class BaseRepository(Generic[TDataModel, TDBModel]):
    """Type-safe repository with generic constraints."""
    
    def __init__(self, db_model_class: type[TDBModel]) -> None:
        self._db_model_class = db_model_class
    
    def insert(self, data_model: TDataModel) -> TDataModel:
        """Insert with full type safety."""
        db_model = self._db_model_class.from_data_model(data_model)
        # Implementation...
        return db_model.to_data_model()
```

### Union Types and Literals
```python
from typing import Union, Literal

Exchange = Literal["NYSE", "NASDAQ", "AMEX"]
SortOrder = Literal["ASC", "DESC"]

def get_company(identifier: Union[int, str]) -> Optional[Company]:
    """Union types for flexible parameters."""
    if isinstance(identifier, int):
        return get_by_id(identifier)
    else:
        return get_by_symbol(identifier)
```

## 3. Error Handling Patterns

### Comprehensive Exception Handling
```python
def _get_dict_of_stocks(self) -> list[dict] | None:
    """Error handling with specific exceptions and logging."""
    api_key = en.ENVIRONMENT_VARIABLES.get_nasdaq_api_key()
    url = f"https://data.nasdaq.com/api/v3/datatables/QUOTEMEDIA/TICKERS?api_key={api_key}&qopts.export=true"
    
    response = requests.get(url)
    if response.status_code == 200:
        try:
            content = _validate_response_contents(response.json())
            return _read_download_file(content)
        except Exception as e:
            raise BaseException(
                "get companies did not get the expected response"
            ) from e
    else:
        raise BaseException(
            f"Failed to retrieve nasdaq companies. Status code: {response.status_code}"
        )
```

### Pipeline Error Aggregation
```python
def run_ingestion(self, sources: list[CompanyDataSource]) -> dict[str, int]:
    """Aggregate errors instead of failing fast."""
    results = {
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
        "tickers_inserted": 0,
        "ticker_histories_inserted": 0,
    }
    
    for source in sources:
        try:
            if not source.is_available():
                self.logger.warning(f"Source {source.name} is not available")
                continue
            # Process source...
        except Exception as e:
            self.logger.error(f"Error getting companies from {source.name}: {e}")
            results["errors"] += 1
    
    return results
```

## 4. Data Processing Patterns

### Data Cleaning and Validation
```python
def _clean_companies(self, companies: list[Company]) -> list[Company]:
    """Consistent data cleaning with logging."""
    clean_companies = []
    seen_tickers = set()
    
    for company in companies:
        # Validation
        if not company.ticker or not company.ticker.symbol:
            continue
        
        ticker = company.ticker.symbol.upper()
        
        # Deduplication
        if ticker in seen_tickers:
            continue
        seen_tickers.add(ticker)
        
        # Data normalization
        if company.company_name:
            company.company_name = company.company_name.strip()
        if company.exchange:
            company.exchange = company.exchange.upper()
        
        clean_companies.append(company)
    
    self.logger.info(
        f"Cleaned data: {len(clean_companies)} companies after removing duplicates"
    )
    return clean_companies
```

### Bulk Operations Pattern
```python
def _comprehensive_sync_to_database(
    self, companies: list[Company]
) -> dict[str, int]:
    """Bulk operations for performance."""
    results = {
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
        "tickers_inserted": 0,
        "ticker_histories_inserted": 0,
    }
    
    if not companies:
        return results
    
    try:
        # Get existing data in bulk
        existing_company_symbols = self.company_repo.get_active_company_symbols()
        existing_ticker_symbols = self.ticker_repo.get_active_ticker_symbols()
        
        # Categorize for bulk operations
        new_companies = self._identify_new_companies(
            companies, existing_company_symbols
        )
        companies_to_update = self._identify_companies_to_update(
            companies, existing_company_symbols
        )
        
        # Bulk insert
        if new_companies:
            self.logger.info(f"Inserting {len(new_companies)} new companies...")
            companies_inserted = self.company_repo.bulk_insert_companies(
                new_companies
            )
            results["inserted"] = companies_inserted
    
    except Exception as e:
        self.logger.error(f"Error during comprehensive database sync: {e}")
        results["errors"] += 1
        raise
    
    return results
```

## 5. Function Design Patterns

### Private Helper Functions
```python
def _convert_dict_to_stocks(ds: list[dict]) -> list[Company]:
    """Convert dictionary data to Company objects."""
    from src.data_sources.models.ticker import Ticker
    
    companies = []
    for k in ds:
        ticker = Ticker(symbol=k[Headers.TICKER], company_id=None)
        company = Company(
            company_name=k[Headers.COMPANY_NAME],
            exchange=k[Headers.EXCHANGE],
            ticker=ticker,
            source="NASDAQ",
        )
        companies.append(company)
    return companies
```

### Type Guards
```python
from typing import TypeGuard

def is_data_model(obj: Any) -> TypeGuard[DataModelProtocol]:
    """Runtime type checking with type narrowing."""
    return (
        hasattr(obj, 'to_dict') and callable(obj.to_dict) and
        hasattr(obj, 'from_dict') and callable(obj.from_dict) and
        hasattr(obj, 'id')
    )

def process_safely(obj: Any) -> None:
    if is_data_model(obj):
        # Type checker knows obj is DataModelProtocol here
        data = obj.to_dict()
        # Process data...
    else:
        raise TypeError("Object does not implement DataModelProtocol")
```

## 6. Documentation Patterns

### Method Documentation
```python
def run_comprehensive_sync(
    self, sources: list[CompanyDataSource]
) -> dict[str, int | set[str]]:
    """Run comprehensive synchronization including unused ticker detection.

    Args:
        sources: List of data sources to get companies from

    Returns:
        Dictionary with comprehensive results including unused tickers:
        {
            "inserted": 5,
            "updated": 3,
            "skipped": 2,
            "errors": 0,
            "tickers_inserted": 5,
            "ticker_histories_inserted": 5,
            "unused_tickers": {"AAPL", "MSFT"},
            "unused_ticker_count": 2
        }
    """
```

### Class Documentation
```python
class CompanyPipeline:
    """Company ingestion pipeline with comprehensive database synchronization.
    
    Handles data ingestion from multiple sources with:
    - Bulk operations for performance
    - Comprehensive error handling and logging
    - Data cleaning and validation
    - Unused ticker detection
    """
```

## 7. Testing Patterns

### Protocol Compliance Testing
```python
def test_company_implements_data_model_protocol():
    """Test that Company class implements DataModelProtocol."""
    company = Company("Test Corp", "NYSE")
    
    # Test protocol methods exist and work
    assert hasattr(company, 'to_dict')
    assert callable(company.to_dict)
    
    data = company.to_dict()
    assert isinstance(data, dict)
    
    # Test class method
    assert hasattr(Company, 'from_dict')
    restored = Company.from_dict(data)
    assert isinstance(restored, Company)
    
    # Test properties
    assert hasattr(company, 'id')
```

## 8. Configuration Patterns

### mypy Configuration
```toml
[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = "src.repos.*"
disallow_any_generics = true
disallow_subclassing_any = true
```

## 9. Common Anti-Patterns to Avoid

### ❌ Avoid: Untyped Parameters
```python
def process_data(data):  # No type hints
    return data.process()
```

### ✅ Prefer: Fully Typed
```python
def process_data(data: DataModelProtocol) -> ProcessedData:
    return data.process()
```

### ❌ Avoid: Catching All Exceptions
```python
try:
    result = api_call()
except:  # Too broad
    return None
```

### ✅ Prefer: Specific Exception Handling
```python
try:
    result = api_call()
except (APIException, NetworkException) as e:
    self.logger.error(f"API call failed: {e}")
    return None
```

### ❌ Avoid: Mutable Default Arguments
```python
def process_items(items: list = []):  # Dangerous
    items.append("processed")
    return items
```

### ✅ Prefer: Safe Defaults
```python
def process_items(items: list[Item] | None = None) -> list[Item]:
    if items is None:
        items = []
    items.append(Item("processed"))
    return items
```

## 10. Performance Considerations

### Bulk Operations
```python
# ✅ Good: Bulk database operations
companies_inserted = self.company_repo.bulk_insert_companies(new_companies)

# ❌ Avoid: Individual operations in loop
for company in companies:
    self.company_repo.insert_company(company)
```

### Type Checking Imports
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.database.models import CompanyTable  # Only during type checking
```

### Lazy Evaluation
```python
from __future__ import annotations  # Postponed annotation evaluation

class Company:
    def get_parent(self) -> Company:  # Forward reference works
        return self.parent_company
```

## Summary

This style guide emphasizes:

1. **Type Safety**: Use protocols, generics, and comprehensive type hints
2. **Clean Architecture**: Separate concerns with clear interfaces
3. **Error Resilience**: Handle errors gracefully with proper logging
4. **Performance**: Use bulk operations and efficient patterns
5. **Maintainability**: Write self-documenting, testable code

Follow these patterns consistently across the codebase to maintain high code quality and developer productivity.