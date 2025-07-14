# Developer Guide - Stock Analysis Application

## Project Overview
A Python-based stock analysis application with multi-source data ingestion, normalization, and algorithmic analysis capabilities. Built with modular architecture and comprehensive typing.

## Development Setup

### Prerequisites
- Python 3.9+
- PostgreSQL
- Virtual environment tool (venv/conda)

### Initial Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python scripts/setup_database.py
```

## Code Standards

### Type Annotations
- **MANDATORY**: All functions, methods, and variables must have type annotations
- Use `from typing import` for complex types
- Use `from __future__ import annotations` for forward references
- Example:
```python
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

@dataclass
class StockQuote:
    symbol: str
    price: float
    volume: int
    timestamp: datetime

def fetch_quotes(symbols: List[str]) -> List[StockQuote]:
    ...
```

### Data Source Wrapper Pattern
All data sources must implement the `DataSourceBase` abstract class:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pandas as pd

class DataSourceBase(ABC):
    @abstractmethod
    def fetch_quotes(self, symbols: List[str]) -> List[StockQuote]:
        """Fetch stock quotes for given symbols"""
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate data source connection"""
        pass
    
    @abstractmethod
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        pass
```

### Data Normalization
- All data sources must return standardized `StockQuote` objects
- Handle timezone conversion to UTC
- Normalize symbol formats (e.g., remove exchange suffixes)
- Validate data integrity before returning

### Error Handling
```python
from src.utils.exceptions import DataSourceError, ValidationError

class YahooFinanceProvider(DataSourceBase):
    def fetch_quotes(self, symbols: List[str]) -> List[StockQuote]:
        try:
            # Implementation
            pass
        except ConnectionError as e:
            raise DataSourceError(f"Failed to connect to Yahoo Finance: {e}")
        except ValueError as e:
            raise ValidationError(f"Invalid symbol format: {e}")
```

## Project Structure Implementation

### Current Priority: Data Source Layer
1. `src/data_sources/base.py` - Abstract base class
2. `src/data_sources/models.py` - Data models (StockQuote, etc.)
3. `src/data_sources/providers/yahoo_finance.py` - First concrete implementation
4. `src/data_sources/factory.py` - Provider factory

### Key Components

#### Stock Quote Model
```python
@dataclass
class StockQuote:
    symbol: str
    price: float
    bid: Optional[float]
    ask: Optional[float]
    volume: int
    market_cap: Optional[float]
    timestamp: datetime
    source: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        pass
```

#### Data Source Factory
```python
class DataSourceFactory:
    _providers: Dict[str, Type[DataSourceBase]] = {}
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[DataSourceBase]) -> None:
        """Register a data source provider"""
        pass
    
    @classmethod
    def create_provider(cls, provider_type: str, **config) -> DataSourceBase:
        """Create provider instance"""
        pass
```

## Testing Guidelines

### Test Structure
- Unit tests: `tests/unit/test_data_sources/`
- Integration tests: `tests/integration/test_data_pipeline/`
- Mock external APIs in unit tests
- Use fixtures for consistent test data

### Example Test
```python
import pytest
from unittest.mock import Mock, patch
from src.data_sources.providers.yahoo_finance import YahooFinanceProvider

@pytest.fixture
def yahoo_provider():
    return YahooFinanceProvider(api_key="test_key")

def test_fetch_quotes_success(yahoo_provider):
    symbols = ["AAPL", "GOOGL"]
    quotes = yahoo_provider.fetch_quotes(symbols)
    
    assert len(quotes) == 2
    assert all(isinstance(q, StockQuote) for q in quotes)
    assert all(q.symbol in symbols for q in quotes)
```

## Configuration Management

### Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `YAHOO_API_KEY` - Yahoo Finance API key
- `ALPHA_VANTAGE_API_KEY` - Alpha Vantage API key
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

### Settings Class
```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str
    yahoo_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
```

## Development Workflow

1. **Feature Development**: Create feature branch from main
2. **Type Checking**: Run `mypy src/` before committing
3. **Testing**: Run `pytest` with minimum 90% coverage
4. **Linting**: Use `black` for formatting, `flake8` for linting
5. **Documentation**: Update docstrings and this guide as needed

## Immediate Implementation Tasks

### Phase 1: Core Data Source Infrastructure
1. Implement `DataSourceBase` abstract class
2. Create `StockQuote` data model with full typing
3. Build Yahoo Finance provider as reference implementation
4. Add factory pattern for provider instantiation
5. Create comprehensive test suite

### Phase 2: Data Pipeline
1. Add data validation and normalization
2. Implement caching layer
3. Add error handling and retry logic
4. Create configuration management

## API Design Principles

- **Consistency**: All providers return identical data structures
- **Reliability**: Comprehensive error handling and retries
- **Performance**: Async operations where possible
- **Testability**: Dependency injection for easy mocking
- **Extensibility**: Simple to add new data sources

## Notes
- All external API calls should be async where possible
- Use dependency injection for testability
- Log all data source operations for debugging
- Cache frequently requested data to reduce API calls
- Validate all incoming data before normalization