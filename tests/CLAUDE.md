# Integration Tests

## Integration tests
please ensure that when we run tests that we use `TESTCONTAINERS_RYUK_DISABLED=true`
this is because we use the `pytest-xdist` package to run containers in parallel.

here is an example `TESTCONTAINERS_RYUK_DISABLED=true uv run pytest tests/integration/test_verification/ -n 2 -v`


## Test Structure

The `/tests` directory contains all integration and end-to-end tests for the Options Deep project. Tests are organized by functionality and data source.

### Directory Structure

```
tests/
├── data_source_mocks/          # Mock data sources for testing
│   ├── eodhd/                  # EODHD data source mocks
│   │   ├── fixtures/           # JSON fixture files for mock responses
│   └── nasdaq/                 # NASDAQ data source mocks
│       ├── fixtures/           # JSON fixture files for mock responses
├── integration/                # Integration tests
│   ├── common_setup.py         # Shared setup utilities for integration tests
│   │
│   ├── test_verification/      # Tests to verify parallel container setup
│   │   ├── test_parallel_container_a.py
│   │   ├── test_parallel_container_b.py
│   │   └── test_simple_setup.py
│   │
│   ├── company_ingestion/      # Company data ingestion tests
│   │   ├── eodhd/             # EODHD-specific company ingestion
│   │   │   ├── test_active_company_ingestion.py
│   │   │   ├── test_active_historical_eod_ingestion.py
│   │   │   └── test_delisted_company_ingestion.py
│   │   └── nasdaq/            # NASDAQ-specific company ingestion
│   │       └── test_nasdaq_screener_sync.py
│   │
│   ├── eod/                   # End-of-day data tests
│   │   └── eodhd/
│   │       └── test_eod_ingestion.py
│   │
│   └── splits/                # Stock split tests
│       └── eodhd/
│           ├── test_get_all_companies_splits.py
│           └── test_get_current_day_splits.py
│
└── utils/                     # Test utilities and helpers
    └── db_assertions.py       # Database assertion helper functions
```
## Common Setup

The `tests/integration/common_setup.py` file contains shared utilities for setting up integration tests, including:
- Database container initialization
- Common fixtures
- Shared test configuration

## Parallel Execution

Tests are designed to run in parallel using `pytest-xdist`. The `-n` flag controls parallelism:
- `-n 2` - Run with 2 workers
- `-n auto` - Automatically determine optimal worker count based on CPU cores

Each test should be isolated and not depend on other tests to ensure safe parallel execution.
