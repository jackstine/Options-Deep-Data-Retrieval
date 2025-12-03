# Python Testing Guide: Skipping and Focusing on Tests

This guide covers how to skip or focus on particular tests in Python using both pytest and unittest frameworks.

## pytest (Recommended for Integration Tests)

### Skipping Tests

#### 1. Unconditional Skip
Skip a test unconditionally with an optional reason:

```python
import pytest

@pytest.mark.skip(reason="Not implemented yet")
def test_feature():
    pass

@pytest.mark.skip(reason="Temporarily disabled")
def test_broken_feature():
    pass
```

#### 2. Conditional Skip
Skip tests based on conditions:

```python
import sys
import pytest

@pytest.mark.skipif(sys.version_info < (3, 10), reason="Requires Python 3.10+")
def test_new_feature():
    pass

@pytest.mark.skipif(sys.platform == "win32", reason="Does not run on Windows")
def test_unix_only():
    pass
```

#### 3. Skip Within Test
Skip programmatically inside a test:

```python
def test_conditional():
    if not has_required_dependency():
        pytest.skip("Dependency not available")
    # Rest of test
```

### Focusing on Specific Tests

#### 1. Run Specific Tests by Path/Name
```bash
# Run specific test file
pytest tests/test_file.py

# Run specific test function
pytest tests/test_file.py::test_function_name

# Run specific test method in a class
pytest tests/test_file.py::TestClass::test_method

# Run tests matching a pattern
pytest -k "test_user"
```

#### 2. Using Custom Markers
Define markers in `pytest.ini` or `pyproject.toml`:

```ini
[pytest]
markers =
    focus: Focus on this test
    slow: Marks tests as slow
    integration: Integration tests
```

Mark tests:

```python
@pytest.mark.focus
def test_important():
    pass

@pytest.mark.slow
def test_expensive_operation():
    pass
```

Run only marked tests:

```bash
# Run only focused tests
pytest -m focus

# Run all except slow tests
pytest -m "not slow"

# Run integration tests only
pytest -m integration
```

#### 3. Auto-Focus Feature (Advanced)
Add to `conftest.py` to automatically run only focused tests when any exist:

```python
def pytest_collection_modifyitems(config, items):
    """Auto-focus: if any test has 'focus' marker, run only those"""
    focused_items = [item for item in items if item.get_closest_marker('focus')]
    if focused_items:
        items[:] = focused_items
```

#### 4. Skip Slow Tests Unless Specified
In `conftest.py`:

```python
def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )

def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")

def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
```

Usage:
```bash
# Skip slow tests (default)
pytest

# Run slow tests
pytest --runslow
```

## unittest (Built-in Framework)

### Skipping Tests

#### 1. Unconditional Skip
```python
import unittest

class TestFeatures(unittest.TestCase):
    @unittest.skip("Work in progress")
    def test_feature(self):
        pass

    @unittest.skip("Temporarily disabled")
    def test_broken(self):
        pass
```

#### 2. Conditional Skip with skipIf
```python
@unittest.skipIf(sys.version_info < (3, 10), "Requires Python 3.10+")
def test_new_feature(self):
    pass

@unittest.skipIf(not has_dependency(), "Dependency not available")
def test_with_dependency(self):
    pass
```

#### 3. Conditional Skip with skipUnless
```python
@unittest.skipUnless(sys.platform.startswith("linux"), "Requires Linux")
def test_linux_only(self):
    pass

@unittest.skipUnless(has_feature(), "Feature not enabled")
def test_feature(self):
    pass
```

#### 4. Skip Within Test Method
```python
def test_conditional(self):
    if not has_required_resource():
        self.skipTest("Resource not available")
    # Rest of test
```

#### 5. Raise SkipTest Exception
```python
def test_something(self):
    if not condition:
        raise unittest.SkipTest("Condition not met")
    # Rest of test
```

#### 6. Skip Entire Test Class
```python
@unittest.skip("Class not ready")
class TestFeature(unittest.TestCase):
    def test_one(self):
        pass

    def test_two(self):
        pass
```

### Focusing on Specific Tests (unittest)

#### 1. Run Specific Tests
```bash
# Run specific test module
python -m unittest tests.test_module

# Run specific test class
python -m unittest tests.test_module.TestClass

# Run specific test method
python -m unittest tests.test_module.TestClass.test_method
```

#### 2. Using Test Suites
```python
import unittest

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestClass('test_specific_method'))
    suite.addTest(TestClass('test_another_method'))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
```

## Best Practices

1. **Always provide a reason** when skipping tests to help future developers understand why
2. **Use markers** for test categorization (slow, integration, unit, etc.)
3. **Don't commit focused tests** - use focus markers locally only for development
4. **Review skipped tests regularly** - they may become outdated
5. **Use conditional skips** for environment-specific tests (OS, Python version, dependencies)
6. **Prefer pytest** for new tests due to more features and better developer experience

## Quick Reference

### pytest
```bash
pytest -m focus                    # Run focused tests
pytest -m "not slow"               # Skip slow tests
pytest -k "test_user"              # Run tests matching pattern
pytest tests/test_file.py::test_x  # Run specific test
pytest --runslow                   # Run including slow tests
```

### unittest
```bash
python -m unittest tests.test_module.TestClass.test_method  # Run specific test
python -m unittest discover                                 # Run all tests
```
