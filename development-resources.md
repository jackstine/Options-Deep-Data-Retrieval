# Development Resources

## Python Typing Best Practices

This document outlines the typing standards and best practices for the Options Deep stock analysis project.

### Why Use Type Hints?

- **Code Documentation**: Type hints serve as inline documentation for function parameters and return values
- **IDE Support**: Better autocomplete, refactoring, and error detection in IDEs
- **Static Analysis**: Catch type-related bugs before runtime using mypy
- **Team Collaboration**: Makes code more readable and maintainable for team members
- **Gradual Adoption**: Can be added incrementally without affecting runtime behavior

### Basic Type Annotations

#### Variables
```python
# Basic types
name: str = "AAPL"
price: float = 150.25
volume: int = 1000000
is_active: bool = True

# Collections (Python 3.9+)
symbols: list[str] = ["AAPL", "GOOGL", "MSFT"]
prices: dict[str, float] = {"AAPL": 150.25, "GOOGL": 2800.50}
coordinates: tuple[float, float] = (10.5, 20.3)
unique_symbols: set[str] = {"AAPL", "GOOGL"}
```

#### Functions
```python
def calculate_sma(prices: list[float], period: int) -> float:
    """Calculate Simple Moving Average."""
    return sum(prices[-period:]) / period

def fetch_stock_data(
    symbol: str,
    start_date: str,
    end_date: str | None = None,
    include_volume: bool = True
) -> dict[str, any]:
    """Fetch stock data with optional parameters."""
    pass
```

### Advanced Typing Patterns

#### Union Types (Multiple Possible Types)
```python
from typing import Union

# Python 3.10+ syntax (preferred)
def process_input(data: str | int | float) -> str:
    return str(data)

# Pre-3.10 syntax
def process_input_legacy(data: Union[str, int, float]) -> str:
    return str(data)
```

#### Optional Types
```python
from typing import Optional

# Python 3.10+ syntax (preferred)
def get_stock_price(symbol: str) -> float | None:
    # May return None if stock not found
    pass

# Pre-3.10 syntax
def get_stock_price_legacy(symbol: str) -> Optional[float]:
    pass
```

#### Generic Types
```python
from typing import TypeVar, Generic, Protocol

T = TypeVar('T')

class DataProcessor(Generic[T]):
    def process(self, data: T) -> T:
        return data

# Usage
price_processor: DataProcessor[float] = DataProcessor()
symbol_processor: DataProcessor[str] = DataProcessor()
```

#### Protocols (Structural Subtyping)
```python
from typing import Protocol

class DataSource(Protocol):
    def fetch_data(self, symbol: str) -> dict[str, any]:
        ...
    
    def validate_connection(self) -> bool:
        ...

# Any class implementing these methods is compatible
def process_data(source: DataSource, symbol: str) -> dict[str, any]:
    if source.validate_connection():
        return source.fetch_data(symbol)
    raise ConnectionError("Data source unavailable")
```

#### Dataclasses with Type Hints
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class StockPrice:
    symbol: str
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    
    def price_change(self) -> float:
        return self.close_price - self.open_price
```

#### Callable Types
```python
from typing import Callable

# Function that takes a float and returns float
AnalysisFunction = Callable[[float], float]

def apply_analysis(data: list[float], func: AnalysisFunction) -> list[float]:
    return [func(value) for value in data]

# Usage
def square_root(x: float) -> float:
    return x ** 0.5

results = apply_analysis([1.0, 4.0, 9.0], square_root)
```

### Project-Specific Typing Patterns

#### Database Models
```python
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Stock(Base):
    __tablename__ = 'stocks'
    
    id: int = Column(Integer, primary_key=True)
    symbol: str = Column(String(10), nullable=False)
    name: str = Column(String(255), nullable=False)
    exchange: str = Column(String(50), nullable=False)
    sector: Optional[str] = Column(String(100))
```

#### Data Transformation
```python
from pandas import DataFrame
from typing import Dict, Any

class DataTransformer:
    def transform(self, raw_data: Dict[str, Any]) -> DataFrame:
        """Transform raw API data to DataFrame."""
        pass
    
    def validate_data(self, data: DataFrame) -> bool:
        """Validate data integrity."""
        pass
```

#### Algorithm Results
```python
from dataclasses import dataclass
from typing import Dict, List
from enum import Enum

class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

@dataclass
class AnalysisResult:
    symbol: str
    algorithm_name: str
    signal: SignalType
    confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any]
```

### Mypy Configuration

Create a `mypy.ini` file in your project root:

```ini
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

# Per-module options
[mypy-pandas.*]
ignore_missing_imports = True

[mypy-numpy.*]
ignore_missing_imports = True

[mypy-yfinance.*]
ignore_missing_imports = True
```

### Common Typing Patterns for Financial Data

#### Price Data
```python
from typing import NamedTuple
from datetime import datetime

class OHLCV(NamedTuple):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

PriceHistory = list[OHLCV]
```

#### Technical Indicators
```python
from typing import Protocol

class TechnicalIndicator(Protocol):
    def calculate(self, prices: list[float]) -> list[float]:
        """Calculate indicator values."""
        ...
    
    @property
    def period(self) -> int:
        """Return the period required for calculation."""
        ...
```

### Type Checking Commands

```bash
# Install mypy
pip install mypy

# Run type checking on entire project
mypy src/

# Run type checking on specific file
mypy src/data_sources/base.py

# Generate type coverage report
mypy --html-report mypy_reports src/
```

### IDE Integration

#### VS Code
1. Install Python extension
2. Enable type checking in settings:
   ```json
   {
       "python.analysis.typeCheckingMode": "strict",
       "python.linting.mypyEnabled": true
   }
   ```

#### PyCharm
- Type checking is enabled by default
- Configure mypy as external tool for additional checking

### Best Practices Summary

1. **Start Simple**: Begin with basic type hints and gradually add more complex types
2. **Be Consistent**: Use the same typing patterns throughout the project
3. **Document Complex Types**: Add docstrings for complex generic types
4. **Use Modern Syntax**: Prefer `str | None` over `Optional[str]` in Python 3.10+
5. **Leverage Protocols**: Use protocols for flexible interfaces
6. **Type Your APIs**: Always type public functions and class methods
7. **Handle Optionals**: Be explicit about when values can be None
8. **Use Dataclasses**: Prefer dataclasses over regular classes for data containers
9. **Test Your Types**: Include type checking in your CI/CD pipeline
10. **Ignore When Necessary**: Use `# type: ignore` sparingly for legitimate cases

### Useful Resources

- [Official Python Typing Documentation](https://docs.python.org/3/library/typing.html)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [PEP 585 - Built-in Generic Types](https://peps.python.org/pep-0585/)
- [Typing Extensions](https://pypi.org/project/typing-extensions/)