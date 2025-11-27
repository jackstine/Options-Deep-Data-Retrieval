"""Pytest configuration and fixtures for integration tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Start a PostgreSQL testcontainer for the test session.

    This fixture creates a PostgreSQL container using testcontainers-python
    with default credentials (test/test/test). The container is shared across
    all tests in the session for performance.

    Yields:
        PostgresContainer instance with running PostgreSQL database
    """
    with PostgresContainer("postgres:16", username="test", password="test", dbname="test") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def setup_test_environment(postgres_container: PostgresContainer) -> Generator[dict[str, str], None, None]:
    """Set up environment variables for test database configuration.

    This fixture configures the environment to use the test database by:
    1. Setting OPTIONS_DEEP_ENV to 'local-test'
    2. Setting database password to testcontainer default
    3. Setting dynamic port from testcontainer
    4. Setting mock API keys for data sources

    Args:
        postgres_container: PostgreSQL testcontainer instance

    Yields:
        Dictionary of environment variables set for testing
    """
    # Store original environment variables
    original_env = {
        "OPTIONS_DEEP_ENV": os.environ.get("OPTIONS_DEEP_ENV"),
        "OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD": os.environ.get("OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD"),
        "NASDAQ_API_KEY": os.environ.get("NASDAQ_API_KEY"),
        "EODHD_API_KEY": os.environ.get("EODHD_API_KEY"),
        "ENVIRONMENT": os.environ.get("ENVIRONMENT"),
    }

    # Set test environment variables
    test_env = {
        "OPTIONS_DEEP_ENV": "local-test",
        "OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD": "test",  # Matches testcontainer default
        "NASDAQ_API_KEY": "test_nasdaq_key",  # Mock API key
        "EODHD_API_KEY": "test_eodhd_key",  # Mock API key
        "ENVIRONMENT": "local-test",
    }

    for key, value in test_env.items():
        os.environ[key] = value

    # Get dynamic port from testcontainer
    dynamic_port = postgres_container.get_exposed_port(5432)
    os.environ["OPTIONS_DEEP_TEST_DB_PORT"] = str(dynamic_port)

    yield test_env

    # Restore original environment variables
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    os.environ.pop("OPTIONS_DEEP_TEST_DB_PORT", None)


@pytest.fixture(scope="session")
def equities_database_url(postgres_container: PostgresContainer, setup_test_environment: dict[str, str]) -> str:
    """Get SQLAlchemy database URL for equities database.

    Args:
        postgres_container: PostgreSQL testcontainer instance
        setup_test_environment: Test environment variables

    Returns:
        SQLAlchemy connection URL string
    """
    return postgres_container.get_connection_url(driver="psycopg2")


@pytest.fixture(scope="session")
def apply_equities_migrations(equities_database_url: str, setup_test_environment: dict[str, str]) -> None:
    """Apply Alembic migrations to equities test database.

    This fixture runs all Alembic migrations against the test database
    to create the full schema before tests run.

    Args:
        equities_database_url: SQLAlchemy connection URL
        setup_test_environment: Test environment variables
    """
    # Get project root and alembic.ini path
    project_root = Path(__file__).parent.parent
    alembic_ini_path = project_root / "src" / "database" / "equities" / "alembic.ini"

    # Set environment variable for dynamic port (used by alembic env.py)
    dynamic_port = os.environ.get("OPTIONS_DEEP_TEST_DB_PORT")

    # Run alembic upgrade head
    env = os.environ.copy()
    env["OPTIONS_DEEP_ENV"] = "local-test"
    env["OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD"] = "test"
    env["ENVIRONMENT"] = "local-test"
    env["OPTIONS_DEEP_TEST_DB_PORT"] = dynamic_port or "5432"

    result = subprocess.run(
        ["alembic", "-c", str(alembic_ini_path), "upgrade", "head"],
        cwd=str(project_root),
        env=env,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Alembic migration failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )


@pytest.fixture(scope="module")
def equities_db_engine(equities_database_url: str, apply_equities_migrations: None):
    """Create SQLAlchemy engine for equities database.

    Args:
        equities_database_url: SQLAlchemy connection URL
        apply_equities_migrations: Ensures migrations are applied

    Yields:
        SQLAlchemy Engine instance
    """
    engine = create_engine(equities_database_url)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def equities_db_session(equities_db_engine) -> Generator[Session, None, None]:
    """Create a database session for a single test.

    This fixture provides a clean database session for each test.
    After the test completes, all changes are rolled back to maintain
    test isolation.

    Args:
        equities_db_engine: SQLAlchemy engine

    Yields:
        SQLAlchemy Session for test use
    """
    SessionLocal = sessionmaker(bind=equities_db_engine)
    session = SessionLocal()

    yield session

    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def clean_database(equities_db_session: Session) -> Generator[Session, None, None]:
    """Provide a clean database by truncating all tables before each test.

    This fixture ensures complete test isolation by removing all data
    from all tables before the test runs.

    Args:
        equities_db_session: Database session

    Yields:
        Clean database session
    """
    # List of tables to truncate (in correct order to handle foreign keys)
    tables = [
        "historical_eod_pricing",
        "misplaced_eod_pricing",
        "missing_eod_pricing",
        "splits",
        "tickers",
        "ticker_history",
        "ticker_history_stats",
        "companies",
        "system",
    ]

    # Truncate all tables
    for table in tables:
        try:
            equities_db_session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        except Exception:
            # Table might not exist yet, continue
            pass

    equities_db_session.commit()

    yield equities_db_session


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Get path to test data directory.

    Returns:
        Path to tests/data_source_mocks directory
    """
    return Path(__file__).parent / "data_source_mocks"


@pytest.fixture(scope="session")
def eodhd_fixtures_dir(test_data_dir: Path) -> Path:
    """Get path to EODHD fixtures directory.

    Args:
        test_data_dir: Test data directory path

    Returns:
        Path to EODHD fixtures
    """
    return test_data_dir / "eodhd" / "fixtures"


@pytest.fixture(scope="session")
def nasdaq_fixtures_dir(test_data_dir: Path) -> Path:
    """Get path to NASDAQ fixtures directory.

    Args:
        test_data_dir: Test data directory path

    Returns:
        Path to NASDAQ fixtures
    """
    return test_data_dir / "nasdaq" / "fixtures"


@pytest.fixture(scope="session")
def yahoo_finance_fixtures_dir(test_data_dir: Path) -> Path:
    """Get path to Yahoo Finance fixtures directory.

    Args:
        test_data_dir: Test data directory path

    Returns:
        Path to Yahoo Finance fixtures
    """
    return test_data_dir / "yahoo_finance" / "fixtures"


@pytest.fixture(scope="session")
def test_equities_config(equities_database_url: str):
    """Create a test equities config with testcontainer database URL.

    This fixture provides a config object that can be used by repositories
    during tests, pointing to the testcontainer database.

    Args:
        equities_database_url: SQLAlchemy connection URL

    Returns:
        Mock config object with database attribute
    """
    from src.config.models.database import DatabaseConfig

    # Parse the connection URL to extract components
    # Format: postgresql://username:password@host:port/database
    url_parts = equities_database_url.replace("postgresql://", "").replace("psycopg2://", "")
    auth_part, host_part = url_parts.split("@")
    username, password = auth_part.split(":")
    host_port, database = host_part.split("/")
    host, port = host_port.split(":")

    database_config = DatabaseConfig(
        host=host,
        port=int(port),
        database=database.split("?")[0],  # Remove query params if any
        username=username,
        password=password,
        environment="local-test",
    )

    class MockEquitiesConfig:
        def __init__(self, db_config: DatabaseConfig) -> None:
            self.database = db_config

    return MockEquitiesConfig(database_config)
