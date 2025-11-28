# Integration Test Suite

This directory contains the integration test suite for the Options Deep project. Integration tests verify the complete flow from data sources through pipelines to the database.

## Overview

The integration test suite uses:
- **pytest** - Test framework
- **testcontainers-python** - Automatic Docker container management for PostgreSQL
- **Pre-built Docker image** - Custom `options-deep-test:latest` image with Alembic migrations pre-applied
- **Mock data sources** - Fixture-based mocks instead of real API calls
- **Fast test execution** - No migration delay (schema already exists in image)

## Quick Start

### Prerequisites

1. **Docker Desktop** must be installed and running
2. **Python 3.13+** with uv package manager
3. Test dependencies installed
4. **Test Docker image** built (see Docker Image Build section below)

### Install Test Dependencies

```bash
# Install test dependencies
uv sync --group test

# Or install all dependencies including dev and test
uv sync --all-groups
```

### Build Test Docker Image

Before running integration tests, you must build the Docker image with pre-applied migrations:

```bash
# Build the test image (uses multi-stage caching for speed)
make build-test-image

# Or build manually
./scripts/build_test_image.sh

# Force rebuild without cache (if migrations changed significantly)
make rebuild-test-image

# Remove test images to start fresh
make clean-test-image
```

**When to rebuild:**
- After adding new Alembic migrations
- After modifying database models
- After changing database configuration files
- When switching branches with different database schemas

### Run Integration Tests

```bash
# Run all integration tests (with parallel execution)
TESTCONTAINERS_RYUK_DISABLED=true uv run pytest tests/integration/ -n auto -v

# Run only company ingestion tests (with 3 parallel workers)
TESTCONTAINERS_RYUK_DISABLED=true uv run pytest tests/integration/company_ingestion/ -n 3 -v

# Run verification tests (with 2 parallel workers)
TESTCONTAINERS_RYUK_DISABLED=true uv run pytest tests/integration/test_verification/ -n 2 -v

# Run all tests sequentially (no parallelization)
TESTCONTAINERS_RYUK_DISABLED=true uv run pytest tests/integration/ -v

# Run all tests (unit + integration)
make test-all
```

**Why `TESTCONTAINERS_RYUK_DISABLED=true`?**
- Required for parallel test execution with `pytest-xdist`
- Disables Ryuk container resource reaper which conflicts with parallel workers
- Each test worker manages its own container lifecycle

### Run Specific Test Files

```bash
# Run a specific test file
pytest tests/integration/company_ingestion/nasdaq/test_nasdaq_screener_sync.py -v

# Run a specific test class
pytest tests/integration/company_ingestion/nasdaq/test_nasdaq_screener_sync.py::TestNasdaqScreenerSync -v

# Run a specific test method
pytest tests/integration/company_ingestion/nasdaq/test_nasdaq_screener_sync.py::TestNasdaqScreenerSync::test_initial_ingestion_creates_companies -v
```

## Test Structure

```
tests/
├── README.md                           # This file
├── conftest.py                         # Pytest fixtures (DB, Docker, etc.)
├── pytest.ini                          # Pytest configuration
├── run_integration_tests.sh           # Test runner script
│
├── data_source_mocks/                  # Mock data sources
│   ├── eodhd/
│   │   ├── mock_symbols.py            # Mock EODHD symbols source
│   │   └── fixtures/
│   │       ├── symbols_active.json    # Active symbols fixture data
│   │       ├── symbols_delisted.json  # Delisted symbols fixture data
│   │       ├── eod_data.json          # EOD pricing fixture data
│   │       ├── bulk_eod.json          # Bulk EOD fixture data
│   │       └── splits.json            # Splits fixture data
│   ├── nasdaq/
│   │   ├── mock_screener.py           # Mock NASDAQ screener source
│   │   └── fixtures/
│   │       └── screener.csv           # NASDAQ screener fixture data
│   └── yahoo_finance/
│       └── fixtures/
│           └── quotes.json            # Yahoo Finance quotes fixture data
│
├── utils/                              # Test utilities
│   ├── db_assertions.py               # Database assertion helpers
│   └── fixture_builders.py            # Test data builders
│
└── integration/                        # Integration tests
    └── company_ingestion/
        ├── nasdaq/
        │   └── test_nasdaq_screener_sync.py
        └── eodhd/
            ├── test_active_company_ingestion.py
            └── test_delisted_company_ingestion.py
```

## How It Works

### 1. Docker Image with Pre-Applied Migrations

Integration tests use a custom Docker image (`options-deep-test:latest`) that has Alembic migrations pre-applied during the image build. This significantly speeds up test execution.

**Multi-Stage Build Process:**

1. **Base Image Stage** (`options-deep-test-base:latest`)
   - Based on `postgres:latest`
   - Installs Python 3, pip, and creates virtual environment
   - Installs Alembic and SQLAlchemy dependencies
   - **Cached** - rarely needs rebuilding (only when dependencies change)

2. **Migration Image Stage** (`options-deep-test:latest`)
   - Uses cached base image
   - Copies source code (database models, migrations, config)
   - Creates `.local-test.env` configuration file
   - Adds initialization script to `/docker-entrypoint-initdb.d/`
   - **Rebuilt frequently** - whenever migrations or models change

### 2. Migration Build Process (Unix Socket Connection)

During Docker image build, migrations are applied using a **Unix socket connection**:

**Why Unix Socket?**
- PostgreSQL initialization scripts in `/docker-entrypoint-initdb.d/` run during container startup
- At this stage, PostgreSQL **only listens on Unix socket**, not TCP
- Unix socket location: `/var/run/postgresql/.s.PGSQL.5432`

**Connection String Format:**
```python
# Unix socket connection (used during Docker init)
postgresql+psycopg2://test:test@/test?host=/var/run/postgresql
```

**Build Flow:**
1. Container starts and initializes PostgreSQL
2. Init script `/docker-entrypoint-initdb.d/10-run-migrations.sh` runs
3. Script sets `DOCKER_INIT=true` environment variable
4. Alembic `env.py` detects `DOCKER_INIT=true` and uses Unix socket connection
5. Migrations execute: `alembic upgrade head`
6. Tables are created and schema is ready
7. PostgreSQL restarts and begins listening on TCP (port 5432)
8. Image is saved with fully migrated database

**Key Files:**
- `dockerfiles/test/Dockerfile` - Multi-stage Dockerfile
- `scripts/build_test_image.sh` - Build automation script
- `docker-entrypoint-init.sh` - Migration execution script
- `src/database/equities/migrations/env.py` - Connection logic with `DOCKER_INIT` check

### 3. Test Container Startup (TCP Connection)

When you run integration tests, **testcontainers-python** starts the pre-migrated image:

**TCP Connection:**
```python
# TCP connection (used during tests)
postgresql+psycopg2://test:test@localhost:55432/test  # port is dynamic
```

**Startup Flow:**
1. testcontainers starts container from `options-deep-test:latest` image
2. PostgreSQL starts with schema already created (from baked-in migrations)
3. PostgreSQL listens on TCP port 5432 inside container
4. testcontainers maps port 5432 to random host port (e.g., 55432)
5. `OPTIONS_DEEP_TEST_DB_PORT` environment variable is set to the dynamic port
6. Tests connect via TCP to `localhost:{dynamic_port}`
7. Database is already migrated - tests can run immediately

**Why Two Connection Methods?**
- **Build time** (Unix socket): PostgreSQL initialization only supports Unix socket
- **Test time** (TCP): testcontainers requires TCP to expose ports to host machine

### 4. Test Execution with Function-Scoped Containers

Each test gets its own PostgreSQL container for complete isolation:

**Container Pattern (from `common_setup.py`):**
```python
from tests.integration.common_setup import integration_test_container

def test_something():
    with integration_test_container() as (postgres, repo, port):
        # Each test gets:
        # - Fresh PostgreSQL container
        # - Pre-migrated database schema
        # - Isolated test environment
        # - Dynamic port assignment

        # Import pipeline after port is set
        from src.pipelines.companies.new_company_pipeline import CompanyPipeline

        # Create pipeline and run test
        # Pipeline automatically uses correct database via environment variables
        pipeline = CompanyPipeline()
        result = pipeline.run_ingestion([mock_source])

        # Container automatically cleaned up on exit
```

**Test Flow:**
1. Each test creates its own PostgreSQL container via context manager
2. Container uses pre-migrated `options-deep-test:latest` image
3. Dynamic port assigned and set in `OPTIONS_DEEP_TEST_DB_PORT`
4. `CONFIG` imported inside test (after port is set)
5. Mock data sources load data from **fixture files** (no real API calls)
6. Database assertions verify results using session from repository
7. Container automatically cleaned up when test completes

**Parallel Execution:**
- Tests can run in parallel using `pytest-xdist` with `-n` flag
- Each worker gets independent containers (no conflicts)
- Example: `pytest tests/integration/ -n 3` runs with 3 parallel workers
- Requires `TESTCONTAINERS_RYUK_DISABLED=true` environment variable
- ~3x faster execution with parallel workers

### 5. Cleanup

After each test completes:

1. Database connections are closed
2. PostgreSQL container is **automatically stopped and removed** by context manager
3. No manual cleanup required
4. Docker image remains cached for next test run (fast startup)
5. Each test leaves no state behind (complete isolation)

## Environment Configuration

### Test Environment Variables

Integration tests use the `local-test` environment with these settings:

- `OPTIONS_DEEP_ENV=local-test`
- `OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD=test`
- `NASDAQ_API_KEY=test_nasdaq_key` (mock)
- `EODHD_API_KEY=test_eodhd_key` (mock)
- `ENVIRONMENT=local-test`

These are set automatically by `conftest.py` fixtures and the test runner script.

### Configuration Files

- `/src/config/environment_configs/local-test.json` - Test database config
- `/tests/pytest.ini` - Pytest configuration
- `/tests/conftest.py` - Pytest fixtures and setup

## Writing New Integration Tests

### Test Template

```python
"""Integration tests for [feature name]."""

from __future__ import annotations

# IMPORTANT: Set environment variables BEFORE importing any src modules
from tests.integration.common_setup import setup_test_environment

setup_test_environment()

# NOW safe to import src modules
from tests.integration.common_setup import integration_test_container
from tests.data_source_mocks.your_source import MockYourSource
from tests.utils.db_assertions import count_companies


class TestYourFeature:
    """Integration tests for your feature."""

    def test_your_scenario(self):
        """Test your specific scenario."""
        with integration_test_container() as (postgres, repo, port):
            # Import pipeline AFTER port is set
            from src.pipelines.your_pipeline import YourPipeline

            # Create mock source and pipeline
            mock_source = MockYourSource()
            pipeline = YourPipeline()

            # Get database session from repository
            session = repo.session

            # Arrange
            initial_count = count_companies(session)

            # Act
            result = pipeline.run([mock_source])

            # Assert
            assert result.success
            assert count_companies(session) > initial_count
```

**Key Points:**
1. **Call `setup_test_environment()` at the top** - BEFORE importing src modules
2. **Use `integration_test_container()` context manager** - Each test gets its own container
3. **Import pipelines inside the context** - After port is set by the container
4. **Get session from repo** - Use `repo.session` for database assertions
5. **No pytest fixtures needed** - Create mock sources and pipelines directly in test
6. **Keep class structure** - Use `class Test...` for organization
7. **Pipelines auto-configure** - They read database config from environment variables

### Adding Fixture Data

1. Create a JSON or CSV file in `tests/data_source_mocks/<source>/fixtures/`
2. Use realistic data from `data_source_samples.md` as reference
3. Keep fixture data small (10-20 records) for fast tests

### Creating Mock Data Sources

1. Create mock class in `tests/data_source_mocks/<source>/`
2. Implement the same interface as the real data source
3. Load and return data from fixture files instead of making API calls

## Test Utilities

### Database Assertions

```python
from tests.utils.db_assertions import (
    assert_company_exists,
    assert_ticker_exists,
    assert_ticker_history_valid,
    count_companies,
    count_tickers,
)

# Assert a company exists with expected fields
company = assert_company_exists(
    db,
    "Apple Inc.",
    expected_fields={"exchange": "NASDAQ"}
)

# Assert a ticker exists
ticker = assert_ticker_exists(db, "AAPL", company_id=company.id)

# Count records
total = count_companies(db)
active_only = count_companies(db, active_only=True)
```

### Fixture Builders

```python
from tests.utils.fixture_builders import (
    build_company_data,
    build_eod_pricing_data,
    build_split_data,
)

# Build test data
company = build_company_data(symbol="TEST", company_name="Test Inc.")
pricing = build_eod_pricing_data(symbol="TEST", close=100.0)
split = build_split_data(symbol="TEST", split_ratio="2/1")
```

## Troubleshooting

### Docker Image Not Found

**Error**: `docker.errors.ImageNotFound: 404 Client Error for http+docker://localhost/v1.47/images/options-deep-test:latest/json: Not Found ("No such image: options-deep-test:latest")`

**Solution**: Build the test Docker image first:

```bash
make build-test-image
```

### Docker Not Running

**Error**: `ERROR: Docker is not running!`

**Solution**: Start Docker Desktop and wait for it to be fully running.

### Port Conflicts

**Error**: Port already in use

**Solution**: testcontainers uses random ports automatically, so this should not happen. If it does, check for stale containers:

```bash
docker ps -a
docker rm -f $(docker ps -aq)  # Remove all stopped containers
```

### Test Execution Time

**Before Docker Image Optimization**: 10-30 seconds (container startup + Alembic migrations)
**After Docker Image Optimization**: 2-5 seconds (container startup only, migrations pre-applied)

If tests are slow:
- Verify you're using `options-deep-test:latest` image (not `postgres:16`)
- Check that image was built successfully with `docker images | grep options-deep-test`
- Run specific test files instead of the entire suite
- Use test markers to run subsets of tests

### Migration Build Failures

**Error**: Alembic migration failed during Docker image build

**Common Causes:**
1. **Syntax errors in migration files** - Fix the migration file and rebuild
2. **Missing environment variables** - Ensure `DOCKER_INIT=true` is set in init script
3. **Connection issues** - Verify Unix socket connection string is correct

**Solution**: Check the Docker build logs:

```bash
# Rebuild with verbose output
docker build -t options-deep-test:latest -f dockerfiles/test/Dockerfile . --progress=plain

# Check if base image exists
docker images | grep options-deep-test-base

# Clean rebuild (no cache)
make rebuild-test-image
```

**Debug specific layer:**
```bash
# View migration script output
docker run --rm -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test -e POSTGRES_DB=test \
  options-deep-test:latest 2>&1 | grep -A 20 "Alembic"
```

### Migrations Out of Date

**Error**: Test database schema doesn't match expected tables

**Solution**: Rebuild the Docker image after changing migrations:

```bash
# Quick rebuild (uses cached base image)
make build-test-image

# Full rebuild (when dependencies changed)
make rebuild-test-image
```

### Unix Socket Connection Errors

**Error**: During image build: `connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed`

**Possible Causes:**
1. PostgreSQL not yet started (init scripts run too early)
2. Incorrect socket path
3. Missing `DOCKER_INIT=true` environment variable

**Solution**: Verify the init script sets the environment correctly:

```bash
# Check init script
cat docker-entrypoint-init.sh | grep DOCKER_INIT

# Should output:
# export DOCKER_INIT=true
```

### Test Database Cleanup Issues

If tests fail and leave dirty data, the `clean_database` fixture automatically truncates all tables before each test.

## Continuous Integration

For CI/CD pipelines (GitHub Actions, GitLab CI, etc.):

```yaml
# Example GitHub Actions workflow
- name: Run Integration Tests
  run: |
    # Start Docker service
    sudo systemctl start docker

    # Build test Docker image with pre-applied migrations
    make build-test-image

    # Run tests
    make integration-test
```

**Important for CI:**
- Must build Docker image before running tests: `make build-test-image`
- testcontainers works automatically in CI environments that support Docker
- Docker image build is cached between CI runs for faster execution
- Use `make rebuild-test-image` if cache causes issues

## Future Enhancements

Planned additions to the test suite:

1. **EOD Pricing Tests** - Integration tests for daily EOD ingestion
2. **Splits Processing Tests** - Integration tests for stock splits
3. **End-to-End Tests** - Full workflow tests across multiple pipelines
4. **Performance Tests** - Measure pipeline execution time
5. **Coverage Reporting** - Add pytest-cov for coverage metrics

## References

- [testcontainers-python Documentation](https://context7.com/testcontainers/testcontainers-python)
- [pytest Documentation](https://context7.com/pytest-dev/pytest)
- [Data Source Sample Data](/data_source_samples.md)
