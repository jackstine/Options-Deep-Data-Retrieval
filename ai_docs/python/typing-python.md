# Python Type Enforcement and Interface Discovery

## Overview

Python's type system provides several mechanisms to enforce interface contracts and enable static analysis without running the interpreter. This document covers the various approaches available for type enforcement and interface discovery in Python, including the core standard library modules that make advanced typing possible.

## Python Standard Library Foundation

### The `typing` Module

The `typing` module is the cornerstone of Python's type system, providing the infrastructure for type hints, generics, and advanced type constructs.

#### Core Components

```python
from typing import (
    # Basic types
    Any, Union, Optional, 
    
    # Generic types  
    TypeVar, Generic, Type,
    
    # Collection types
    List, Dict, Set, Tuple, Sequence, Mapping,
    
    # Protocol and structural typing
    Protocol, runtime_checkable,
    
    # Advanced type constructs
    Literal, Final, ClassVar, Annotated,
    
    # Type checking utilities
    TYPE_CHECKING, get_type_hints, get_origin, get_args,
    
    # Callable types
    Callable, Awaitable, Coroutine,
    
    # Type guards and narrowing
    TypeGuard, TypeIs  # Python 3.10+
)
```

#### Essential `typing` Features for Repository Design

**Generic Type Variables:**
```python
from typing import TypeVar, Generic, Protocol

# Define type variables with bounds
TDataModel = TypeVar('TDataModel', bound='DataModelProtocol')
TDBModel = TypeVar('TDBModel', bound='DBModelProtocol')

# Constrained type variables
TNumeric = TypeVar('TNumeric', int, float, Decimal)

# Generic class definition
class BaseRepository(Generic[TDataModel, TDBModel]):
    """Generic repository with type safety."""
    
    def __init__(self, model_class: Type[TDataModel]) -> None:
        self.model_class = model_class
```

**Protocol Classes for Structural Typing:**
```python
from typing import Protocol, runtime_checkable

class DataModelProtocol(Protocol):
    """Structural typing interface - no inheritance required."""
    id: Optional[int]
    
    def to_dict(self) -> Dict[str, Any]: ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self: ...

# Optional runtime checking
@runtime_checkable
class Serializable(Protocol):
    def to_dict(self) -> Dict[str, Any]: ...

# Usage with isinstance() at runtime
def process_data(obj: Any) -> None:
    if isinstance(obj, Serializable):
        data = obj.to_dict()  # Type checker knows this exists
```

**Union Types and Optional:**
```python
from typing import Union, Optional

# Union types for multiple possible types
def get_company(identifier: Union[int, str]) -> Optional[Company]:
    """Get company by ID (int) or ticker symbol (str)."""
    if isinstance(identifier, int):
        return get_by_id(identifier)
    else:
        return get_by_symbol(identifier)

# Optional is shorthand for Union[T, None]
Optional[int] == Union[int, None]  # These are equivalent
```

**Literal Types for Precise Values:**
```python
from typing import Literal

Exchange = Literal["NYSE", "NASDAQ", "AMEX"]
OrderDirection = Literal["ASC", "DESC"]

def get_companies(exchange: Exchange, 
                 order: OrderDirection = "ASC") -> List[Company]:
    """Type-safe enumeration of allowed values."""
    # IDE will autocomplete only valid exchange values
    pass
```

**Type Checking Utilities:**
```python
from typing import TYPE_CHECKING, get_type_hints, get_origin, get_args

# Avoid circular imports during type checking
if TYPE_CHECKING:
    from src.database.models import CompanyTable

class CompanyRepository:
    def __init__(self, model_class: 'Type[CompanyTable]') -> None:
        # String annotation resolves during type checking only
        self.model_class = model_class

# Runtime type inspection
def analyze_generic_type(cls):
    """Analyze generic type information at runtime."""
    hints = get_type_hints(cls)
    for name, hint in hints.items():
        origin = get_origin(hint)  # e.g., list, dict, Union
        args = get_args(hint)      # e.g., (str, int) for Dict[str, int]
        print(f"{name}: {hint} (origin: {origin}, args: {args})")
```

### The `abc` Module (Abstract Base Classes)

The `abc` module provides infrastructure for defining Abstract Base Classes with abstract methods and properties.

#### Core ABC Components

```python
from abc import ABC, abstractmethod, abstractproperty, abstractclassmethod, abstractstaticmethod

class DataModelBase(ABC):
    """Abstract base class enforcing interface through inheritance."""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Abstract method - must be implemented by subclasses."""
        pass
    
    @abstractproperty  # Deprecated - use @property + @abstractmethod
    def id(self) -> Optional[int]:
        """Abstract property."""
        pass
    
    # Modern approach for abstract properties
    @property
    @abstractmethod
    def name(self) -> str:
        """Abstract property using modern syntax."""
        pass
    
    @abstractclassmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataModelBase':
        """Abstract class method."""
        pass
    
    @abstractstaticmethod
    def validate_data(data: Dict[str, Any]) -> bool:
        """Abstract static method."""
        pass
```

#### ABC vs Protocol Comparison

```python
# ABC Approach - Inheritance required
class DataModelABC(ABC):
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]: pass

class Company(DataModelABC):  # Must inherit
    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name}

# Protocol Approach - Structural typing
class DataModelProtocol(Protocol):
    def to_dict(self) -> Dict[str, Any]: ...

class Company:  # No inheritance needed
    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name}

# Both work with type checking, but Protocol is more flexible
```

#### When to Use ABC vs Protocol

**Use ABC when:**
- You want to provide default implementations
- You need runtime inheritance checking
- You want to prevent instantiation of incomplete classes
- You have a clear inheritance hierarchy

**Use Protocol when:**
- You want structural typing (duck typing with type safety)
- You're working with existing classes you can't modify
- You prefer composition over inheritance
- You want maximum flexibility

### The `__future__` Module

The `__future__` module enables new language features before they become the default, crucial for modern type annotations.

#### Essential `__future__` Imports for Typing

```python
from __future__ import annotations

# Enables postponed evaluation of annotations (PEP 563)
# This allows forward references and improves performance

class Company:
    def get_parent(self) -> Company:  # Forward reference works
        return self.parent_company
    
    def process_companies(self, companies: list[Company]) -> dict[str, Company]:
        # Can use built-in generics (Python 3.9+ syntax)
        return {c.name: c for c in companies}
```

**Benefits of `from __future__ import annotations`:**

1. **Forward References:**
```python
from __future__ import annotations

class Node:
    def __init__(self, parent: Optional[Node] = None):  # Forward reference
        self.parent = parent
```

2. **Built-in Generic Types (Python 3.9+):**
```python
from __future__ import annotations

# Without __future__ import (old way)
from typing import List, Dict
def process_data(items: List[str]) -> Dict[str, int]: ...

# With __future__ import (modern way)
def process_data(items: list[str]) -> dict[str, int]: ...
```

3. **Performance Improvement:**
```python
from __future__ import annotations

# Annotations are stored as strings and evaluated lazily
# Reduces module import time and memory usage
class Repository:
    def get_many(self) -> list[ComplexDataModel]:  # Not evaluated at import
        pass
```

#### Combining All Three Modules

```python
from __future__ import annotations  # Enable modern annotations

from abc import ABC, abstractmethod  # Abstract base classes
from typing import (  # Type system infrastructure
    Protocol, TypeVar, Generic, Optional, Dict, Any, List,
    runtime_checkable, TYPE_CHECKING
)

# Type variables
TModel = TypeVar('TModel', bound='DataModelProtocol')

# Protocol for structural typing
class DataModelProtocol(Protocol):
    id: Optional[int]
    
    def to_dict(self) -> dict[str, Any]: ...
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DataModelProtocol: ...

# ABC for inheritance-based contracts
class ProcessorBase(ABC):
    @abstractmethod
    def process(self, data: Any) -> Any: ...
    
    def log_processing(self, message: str) -> None:
        """Concrete method with default implementation."""
        print(f"Processing: {message}")

# Generic repository combining both approaches
class BaseRepository(Generic[TModel]):
    """Type-safe repository using modern Python typing."""
    
    def __init__(self, model_class: type[TModel]) -> None:
        self.model_class = model_class
    
    def insert(self, model: TModel) -> TModel:
        """Insert with full type safety."""
        data = model.to_dict()  # Protocol ensures this exists
        # ... implementation
        return model
    
    def find_by_criteria(self, **criteria) -> list[TModel]:
        """Find with type-safe return."""
        # ... implementation
        return []

# Usage with type checking
if TYPE_CHECKING:
    from src.models import CompanyModel

class CompanyRepository(BaseRepository[CompanyModel]):
    """Concrete repository with specific type."""
    pass
```

## Static Type Checking Tools

### mypy
The most popular static type checker for Python:

```bash
# Install mypy
pip install mypy

# Check types
mypy src/
mypy --strict src/repos/
```

### pyright/pylance
Microsoft's type checker (used by VS Code):

```bash
# Install pyright
npm install -g pyright

# Check types
pyright src/
```

### Other Tools
- **Pyre** (Facebook's type checker)
- **Pytype** (Google's type checker)

## Interface Enforcement Mechanisms

### 1. Protocol Classes (Structural Typing)

**Best for interface contracts - most recommended approach**

```python
from typing import Protocol, runtime_checkable

class DataModelProtocol(Protocol):
    """Interface that all data models must implement."""
    id: Optional[int]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self:
        """Create from dictionary."""
        ...

class DBModelProtocol(Protocol):
    """Interface that all SQLAlchemy models must implement."""
    id: int
    
    def to_data_model(self) -> DataModelProtocol:
        """Convert to data model."""
        ...
    
    @classmethod
    def from_data_model(cls, data: DataModelProtocol) -> Self:
        """Create from data model."""
        ...

# Usage in generic class
from typing import Generic, TypeVar

TDataModel = TypeVar('TDataModel', bound=DataModelProtocol)
TDBModel = TypeVar('TDBModel', bound=DBModelProtocol)

class BaseRepository(Generic[TDataModel, TDBModel]):
    """Type-safe repository with interface enforcement."""
    
    def __init__(self, db_model_class: Type[TDBModel]) -> None:
        self._db_model_class = db_model_class
    
    def insert(self, data_model: TDataModel) -> TDataModel:
        # mypy will enforce that data_model implements DataModelProtocol
        db_model = self._db_model_class.from_data_model(data_model)
        # ... implementation
        return db_model.to_data_model()
```

**Static Analysis Benefits:**
- mypy/pyright will catch protocol violations at check time
- IDE autocomplete works correctly
- No runtime overhead (unless using `@runtime_checkable`)

### 2. Abstract Base Classes (ABC)

**Traditional inheritance-based approach**

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class DataModelBase(ABC):
    """Abstract base class for data models."""
    
    @property
    @abstractmethod
    def id(self) -> Optional[int]:
        """Record ID."""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataModelBase':
        """Create from dictionary."""
        pass

# Concrete implementation must inherit
class Company(DataModelBase):
    def __init__(self, company_name: str, exchange: str, id: Optional[int] = None):
        self.company_name = company_name
        self.exchange = exchange
        self._id = id
    
    @property
    def id(self) -> Optional[int]:
        return self._id
    
    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "company_name": self.company_name, "exchange": self.exchange}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Company':
        return cls(data["company_name"], data["exchange"], data.get("id"))

# Usage with type constraint
from typing import TypeVar

TDataModel = TypeVar('TDataModel', bound=DataModelBase)

class BaseRepository(Generic[TDataModel]):
    def insert(self, data_model: TDataModel) -> TDataModel:
        # Guaranteed to have DataModelBase methods
        data_dict = data_model.to_dict()
        # ... implementation
```

**Static Analysis Benefits:**
- Inheritance relationship is explicit
- mypy enforces abstract method implementation
- Clear in class hierarchy

**Drawbacks:**
- Requires inheritance (less flexible than protocols)
- Runtime overhead for ABC machinery

### 3. TypedDict for Structured Data

**For dictionary-based interfaces**

```python
from typing import TypedDict, Optional, Literal

class CompanyDict(TypedDict):
    """Typed dictionary interface for company data."""
    id: Optional[int]
    company_name: str
    exchange: Literal["NYSE", "NASDAQ", "AMEX"]
    sector: Optional[str]
    active: bool

def process_company(company: CompanyDict) -> None:
    # mypy enforces dictionary structure
    print(f"Processing {company['company_name']}")
    # mypy error if key doesn't exist or wrong type
    
# Partial TypedDict for optional fields
class PartialCompanyDict(TypedDict, total=False):
    """Company data with all optional fields."""
    id: int
    company_name: str
    exchange: str
    sector: str
    active: bool
```

**Static Analysis Benefits:**
- Dictionary structure enforced by mypy
- Required vs optional keys
- Exact key name checking

### 4. Dataclass with Type Enforcement

**Using dataclasses with validation**

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, ClassVar
import inspect

@dataclass
class DataModelContract:
    """Base dataclass with interface enforcement."""
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Default implementation using dataclass fields."""
        return {field.name: getattr(self, field.name) for field in fields(self)}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create instance from dictionary with type checking."""
        # Get the class signature for validation
        sig = inspect.signature(cls)
        filtered_data = {k: v for k, v in data.items() if k in sig.parameters}
        return cls(**filtered_data)

@dataclass
class Company(DataModelContract):
    """Company dataclass with enforced interface."""
    company_name: str = ""
    exchange: str = ""
    sector: Optional[str] = None
    active: bool = True
    
    # Class-level type checking
    _required_fields: ClassVar[set] = {"company_name", "exchange"}
    
    def __post_init__(self):
        """Runtime validation of required fields."""
        for field_name in self._required_fields:
            if not getattr(self, field_name):
                raise ValueError(f"Required field {field_name} is empty")
```

## Advanced Type Enforcement Patterns

### 1. Generic Type Constraints with Protocols

```python
from typing import Protocol, TypeVar, Generic, Type

class Insertable(Protocol):
    """Protocol for objects that can be inserted into database."""
    
    def to_dict(self) -> Dict[str, Any]: ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self: ...

class Updateable(Protocol):
    """Protocol for objects that can be updated."""
    
    id: Optional[int]
    
    def get_update_fields(self) -> Set[str]: ...

# Multiple protocol constraints
TModel = TypeVar('TModel', bound=Insertable)
TUpdateModel = TypeVar('TUpdateModel', bound=Insertable & Updateable)  # Intersection

class Repository(Generic[TModel, TUpdateModel]):
    def insert(self, model: TModel) -> TModel:
        # Guaranteed to have Insertable methods
        data = model.to_dict()
        # ...
    
    def update(self, model: TUpdateModel) -> bool:
        # Guaranteed to have both Insertable and Updateable methods
        if model.id is None:
            raise ValueError("Cannot update model without ID")
        update_fields = model.get_update_fields()
        # ...
```

### 2. Interface Validation Decorators

```python
from functools import wraps
from typing import get_type_hints, Any, Callable

def validate_interface(protocol_class):
    """Decorator to validate that class implements protocol at definition time."""
    
    def decorator(cls):
        # Get protocol methods
        protocol_methods = {name for name in dir(protocol_class) 
                          if not name.startswith('_') and callable(getattr(protocol_class, name))}
        
        # Check class implements all protocol methods
        class_methods = {name for name in dir(cls) 
                        if not name.startswith('_') and callable(getattr(cls, name))}
        
        missing_methods = protocol_methods - class_methods
        if missing_methods:
            raise TypeError(f"Class {cls.__name__} missing protocol methods: {missing_methods}")
        
        return cls
    
    return decorator

# Usage
@validate_interface(DataModelProtocol)
class Company:
    # Must implement all DataModelProtocol methods or decorator raises TypeError
    def to_dict(self) -> Dict[str, Any]:
        return {}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Company':
        return cls()
```

### 3. Type Guards for Runtime Checking

```python
from typing import TypeGuard

def is_data_model(obj: Any) -> TypeGuard[DataModelProtocol]:
    """Type guard to check if object implements DataModelProtocol."""
    return (
        hasattr(obj, 'to_dict') and callable(obj.to_dict) and
        hasattr(obj, 'from_dict') and callable(obj.from_dict) and
        hasattr(obj, 'id')
    )

def process_model(obj: Any) -> None:
    if is_data_model(obj):
        # mypy now knows obj is DataModelProtocol
        data = obj.to_dict()
        model_id = obj.id
    else:
        raise TypeError("Object does not implement DataModelProtocol")
```

## Static Analysis Configuration

### mypy Configuration

Create `mypy.ini` or `pyproject.toml`:

```ini
# mypy.ini
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

# Per-module configuration
[mypy-src.repos.*]
disallow_any_generics = True
disallow_subclassing_any = True

[mypy-tests.*]
disallow_untyped_defs = False
disallow_incomplete_defs = False
```

Or in `pyproject.toml`:

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

### Pre-commit Hooks for Type Checking

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict]
        exclude: ^tests/
  
  - repo: https://github.com/microsoft/pyright
    rev: v1.1.350
    hooks:
      - id: pyright
```

## IDE Integration

### VS Code Settings

```json
{
    "python.analysis.typeCheckingMode": "strict",
    "python.analysis.autoImportCompletions": true,
    "python.analysis.diagnosticMode": "workspace",
    "python.linting.mypyEnabled": true,
    "python.linting.mypyArgs": ["--strict"],
    "python.linting.enabled": true
}
```

### PyCharm Configuration

1. Enable type checking in Settings > Editor > Inspections > Python
2. Configure external tools for mypy
3. Enable type hints in code completion

## Best Practices for Interface Enforcement

### 1. Use Protocols for Structural Typing

```python
# ✅ Good - Flexible structural typing
class Serializable(Protocol):
    def to_dict(self) -> Dict[str, Any]: ...

# ✅ Usage
def save_to_json(obj: Serializable) -> str:
    return json.dumps(obj.to_dict())

# Any object with to_dict() method works
save_to_json(company)  # Company has to_dict()
save_to_json(ticker)   # Ticker has to_dict()
```

### 2. Combine Protocols with Generics

```python
# ✅ Good - Type-safe generic with interface constraint
TModel = TypeVar('TModel', bound=Serializable)

class DataProcessor(Generic[TModel]):
    def process(self, items: List[TModel]) -> List[Dict[str, Any]]:
        return [item.to_dict() for item in items]
```

### 3. Use Type Guards for Runtime Safety

```python
# ✅ Good - Safe runtime checking
def process_safely(obj: Any) -> None:
    if is_serializable(obj):
        # Type checker knows obj is Serializable here
        data = obj.to_dict()
        # ... process data
    else:
        raise TypeError("Object must be serializable")
```

### 4. Document Interface Requirements

```python
class BaseRepository(Generic[TDataModel, TDBModel]):
    """
    Base repository with enforced interfaces.
    
    Type Parameters:
        TDataModel: Must implement DataModelProtocol
                   - to_dict() -> Dict[str, Any]
                   - from_dict(Dict[str, Any]) -> Self
                   - id: Optional[int] property
        
        TDBModel: Must implement DBModelProtocol
                 - to_data_model() -> TDataModel
                 - from_data_model(TDataModel) -> Self
                 - id: int property
    """
```

## Testing Interface Compliance

### Unit Tests for Protocol Compliance

```python
import pytest
from typing import get_type_hints

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

def test_protocol_typing():
    """Test that type annotations are correct."""
    hints = get_type_hints(Company.to_dict)
    assert hints['return'] == Dict[str, Any]
```

### Static Analysis in CI/CD

```yaml
# GitHub Actions example
name: Type Check
on: [push, pull_request]

jobs:
  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install mypy types-all
          pip install -r requirements.txt
      
      - name: Run mypy
        run: mypy src/ --strict
      
      - name: Run pyright
        run: |
          npm install -g pyright
          pyright src/
```

## Summary

**Recommended Approach for Options-Deep:**

1. **Use Protocols** for interface definitions (most flexible)
2. **Configure mypy** with strict settings for static analysis
3. **Use Generic TypeVars** with protocol bounds for type safety
4. **Add pre-commit hooks** for automatic type checking
5. **Document interface requirements** clearly in docstrings

**Example Implementation:**

```python
# Interface definition
class DataModelProtocol(Protocol):
    id: Optional[int]
    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self: ...

# Type-safe generic repository
TDataModel = TypeVar('TDataModel', bound=DataModelProtocol)

class BaseRepository(Generic[TDataModel]):
    def insert(self, model: TDataModel) -> TDataModel:
        # Static type checker enforces protocol compliance
        data = model.to_dict()  # Guaranteed to exist
        # ... implementation
```

This approach provides:
- ✅ **Static analysis** without running code
- ✅ **IDE support** with autocomplete and error highlighting  
- ✅ **Flexible interfaces** without inheritance requirements
- ✅ **Type safety** with generic constraints
- ✅ **Runtime safety** with optional type guards

## Standard Library Module Integration Best Practices

### Complete Repository Example Using All Three Modules

```python
from __future__ import annotations  # Modern annotations and performance

from abc import ABC, abstractmethod  # Abstract base classes when needed
from typing import (  # Complete typing toolkit
    Protocol, TypeVar, Generic, Optional, Dict, Any, List, Set,
    Union, Literal, Final, ClassVar, TYPE_CHECKING,
    runtime_checkable, get_type_hints
)

# Constants using Final
DEFAULT_PAGE_SIZE: Final[int] = 50
SUPPORTED_EXCHANGES: Final[Set[str]] = {"NYSE", "NASDAQ", "AMEX"}

# Literal types for precise values
Exchange = Literal["NYSE", "NASDAQ", "AMEX"]
SortOrder = Literal["ASC", "DESC"]

# Protocol for data models (structural typing)
class DataModelProtocol(Protocol):
    """Interface for all data models using structural typing."""
    id: Optional[int]
    
    def to_dict(self) -> dict[str, Any]: ...
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DataModelProtocol: ...
    
    def is_valid(self) -> bool: ...

# ABC for processors (inheritance-based when you need shared behavior)
class ProcessorBase(ABC):
    """Abstract processor with shared functionality."""
    
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self._logger = self._setup_logging()
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """Abstract processing method."""
        pass
    
    def _setup_logging(self) -> Any:
        """Concrete helper method."""
        # Shared logging setup
        return None

# Type variables with protocol bounds
TDataModel = TypeVar('TDataModel', bound=DataModelProtocol)
TProcessor = TypeVar('TProcessor', bound=ProcessorBase)

# Runtime checkable protocol for optional runtime validation
@runtime_checkable
class Cacheable(Protocol):
    """Protocol for objects that can be cached."""
    
    def get_cache_key(self) -> str: ...
    
    def get_cache_ttl(self) -> int: ...

# Generic repository combining all concepts
class BaseRepository(Generic[TDataModel]):
    """Modern type-safe repository using all standard library features."""
    
    # Class variables with proper typing
    _instances: ClassVar[dict[str, BaseRepository]] = {}
    
    def __init__(
        self, 
        model_class: type[TDataModel],
        processor: Optional[ProcessorBase] = None
    ) -> None:
        self.model_class = model_class
        self.processor = processor
        
        # Runtime type validation using get_type_hints
        self._validate_model_protocol()
    
    def _validate_model_protocol(self) -> None:
        """Runtime validation that model implements required protocol."""
        hints = get_type_hints(self.model_class)
        required_methods = {'to_dict', 'from_dict', 'is_valid'}
        
        for method in required_methods:
            if not hasattr(self.model_class, method):
                raise TypeError(
                    f"Model {self.model_class.__name__} missing required method: {method}"
                )
    
    def find_by_exchange(
        self, 
        exchange: Exchange,  # Literal type ensures valid values
        order: SortOrder = "ASC"
    ) -> list[TDataModel]:
        """Find models by exchange with type-safe parameters."""
        # Implementation would use exchange and order
        return []
    
    def get_with_cache(self, model_id: int) -> Optional[TDataModel]:
        """Get model with optional caching support."""
        model = self._get_by_id(model_id)
        
        # Runtime protocol checking
        if model and isinstance(model, Cacheable):
            # Type checker knows model has cache methods
            cache_key = model.get_cache_key()
            ttl = model.get_cache_ttl()
            # Use cache...
        
        return model
    
    def _get_by_id(self, model_id: int) -> Optional[TDataModel]:
        """Private method for actual data retrieval."""
        # Implementation...
        return None
    
    def bulk_process(
        self, 
        models: list[TDataModel],
        processor: Optional[TProcessor] = None
    ) -> list[TDataModel]:
        """Bulk processing with optional custom processor."""
        active_processor = processor or self.processor
        
        if not active_processor:
            return models
        
        # Type checker knows processor has process method (ABC guarantees it)
        return [active_processor.process(model) for model in models]

# Conditional imports for type checking only
if TYPE_CHECKING:
    from src.database.models import CompanyDBModel
    from src.processors.company import CompanyProcessor

# Concrete implementation
class CompanyRepository(BaseRepository[Company]):
    """Company-specific repository with full type safety."""
    
    def __init__(self, processor: Optional[CompanyProcessor] = None) -> None:
        super().__init__(Company, processor)
    
    def get_tech_companies(self) -> list[Company]:
        """Domain-specific method with full type safety."""
        return self.find_by_exchange("NASDAQ")  # Literal type prevents typos

# Factory function using Union types
def create_repository(
    repo_type: Literal["company", "ticker"],
    config: dict[str, Any]
) -> Union[CompanyRepository, TickerRepository]:
    """Factory with precise return types."""
    if repo_type == "company":
        return CompanyRepository()
    else:
        return TickerRepository()

# Usage example showing all features working together
def main() -> None:
    """Example usage of type-safe repository system."""
    
    # Type-safe factory usage
    company_repo = create_repository("company", {})
    
    # Literal types prevent invalid values
    nasdaq_companies = company_repo.find_by_exchange("NASDAQ", "DESC")
    
    # Generic typing ensures type safety
    for company in nasdaq_companies:
        # Type checker knows company has DataModelProtocol methods
        data = company.to_dict()
        is_valid = company.is_valid()
        
        # Runtime protocol checking
        if isinstance(company, Cacheable):
            cache_key = company.get_cache_key()

if __name__ == "__main__":
    main()
```

### Key Benefits of This Integrated Approach

1. **`typing` Module Provides:**
   - Generic type safety with `TypeVar` and `Generic`
   - Structural typing with `Protocol`
   - Precise value constraints with `Literal`
   - Runtime type inspection with `get_type_hints`

2. **`abc` Module Provides:**
   - Inheritance-based contracts when shared behavior is needed
   - Compile-time enforcement of abstract methods
   - Clear class hierarchies for related components

3. **`__future__` Import Provides:**
   - Modern annotation syntax (`list` instead of `List`)
   - Forward reference support
   - Better performance through lazy evaluation

### When to Use Each Approach

| Scenario | Use | Why |
|----------|-----|-----|
| Data Models | `Protocol` | Structural typing, no inheritance needed |
| Processors/Services | `ABC` | Shared behavior, clear inheritance |
| Configuration | `TypedDict` + `Literal` | Precise structure and values |
| Generic Components | `TypeVar` + `Generic` | Type safety across different models |
| Runtime Validation | `@runtime_checkable` | Optional isinstance() checking |
| Circular Imports | `TYPE_CHECKING` | Import only during type checking |
| Modern Syntax | `__future__` annotations | Performance and forward references |

This integrated approach gives you the full power of Python's type system while maintaining flexibility and performance.