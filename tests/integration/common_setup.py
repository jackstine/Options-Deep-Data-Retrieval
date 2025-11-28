"""Common setup utilities for integration tests.

This module provides shared setup functions for integration tests to eliminate
code duplication and ensure consistent test container configuration.

Usage:
    # At the top of test file (before any src imports)
    from tests.integration.common_setup import setup_test_environment
    setup_test_environment()

    # In test function
    from tests.integration.common_setup import integration_test_container

    def test_something():
        with integration_test_container() as (postgres, repo, port):
            # Your test code here
            pass
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import TYPE_CHECKING, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

if TYPE_CHECKING:
    from src.repos.equities.companies.company_repository import CompanyRepository


def setup_test_environment() -> None:
    """Set up environment variables required for integration tests.

    IMPORTANT: Call this function at the top of your test file, BEFORE
    importing any src modules. This prevents CONFIG from initializing
    with incorrect values during import time.

    Sets the following environment variables:
    - OPTIONS_DEEP_ENV=local-test
    - OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD=test
    - ENVIRONMENT=local-test
    - NASDAQ_API_KEY=test_key
    - EODHD_API_KEY=test_key
    """
    os.environ["OPTIONS_DEEP_ENV"] = "local-test"
    os.environ["OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD"] = "test"
    os.environ["ENVIRONMENT"] = "local-test"
    os.environ["NASDAQ_API_KEY"] = "test_key"
    os.environ["EODHD_API_KEY"] = "test_key"


def create_test_session(postgres: PostgresContainer, port: int) -> Session:
    """Create a SQLAlchemy session for the test database container.

    This is a helper function to reduce code duplication when creating
    database sessions in tests.

    IMPORTANT: The session and engine will be automatically cleaned up
    when the integration_test_container context exits. You don't need
    to manually close the session.

    Args:
        postgres: The PostgreSQL container instance
        port: The exposed port number for the container

    Returns:
        SQLAlchemy Session connected to the test database

    Example:
        with integration_test_container() as (postgres, repo, port):
            session = create_test_session(postgres, port)
            # Use session for assertions
            company = session.query(Company).filter_by(name="Apple Inc.").first()
            assert company is not None
    """
    connection_string = f"postgresql+psycopg2://test:test@{postgres.get_container_host_ip()}:{port}/test"
    engine = create_engine(connection_string, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Store engine and session for cleanup
    if not hasattr(postgres, '_test_engines'):
        postgres._test_engines = []
    if not hasattr(postgres, '_test_sessions'):
        postgres._test_sessions = []

    postgres._test_engines.append(engine)
    postgres._test_sessions.append(session)

    return session


@contextmanager
def integration_test_container() -> Generator[tuple[PostgresContainer, CompanyRepository, int], None, None]:
    """Context manager for integration test PostgreSQL container setup.

    This context manager:
    1. Starts a PostgreSQL container with pre-applied Alembic migrations
    2. Gets the dynamic port assigned by testcontainers
    3. Sets OPTIONS_DEEP_TEST_DB_PORT environment variable
    4. Imports and creates CompanyRepository (after port is set)
    5. Yields the container, repository, and port for test use
    6. Cleans up all SQLAlchemy sessions and engines
    7. Automatically cleans up the container when the context exits

    NOTE: You must build the test Docker image first:
        make build-test-image

    Yields:
        tuple containing:
        - PostgresContainer: The running container instance
        - CompanyRepository: Repository instance connected to the test database
        - int: The dynamic port number assigned to the container

    Example:
        with integration_test_container() as (postgres, repo, port):
            company = Company(...)
            inserted = repo.insert(company)
            assert inserted.id is not None
    """
    # Start PostgreSQL container with pre-applied migrations
    # Image: options-deep-test:latest (built via make build-test-image)
    with PostgresContainer(
        "options-deep-test:latest", username="test", password="test", dbname="test"
    ) as postgres:

        # Get dynamic port assigned by testcontainers
        port = postgres.get_exposed_port(5432)

        # Set environment variable for dynamic port
        # This allows CONFIG to connect to the correct container
        os.environ["OPTIONS_DEEP_TEST_DB_PORT"] = str(port)

        # Import repository AFTER port is set
        # This ensures CONFIG initializes with the correct port
        from src.repos.equities.companies.company_repository import CompanyRepository

        # Create repository instance
        repo = CompanyRepository()

        try:
            # Yield to test
            yield postgres, repo, port
        finally:
            # Clean up all test sessions and engines before container stops
            # This prevents "server closed the connection unexpectedly" errors

            # Close repository session if it exists
            try:
                if hasattr(repo, 'session') and repo.session:
                    repo.session.close()
            except Exception:
                pass  # Ignore errors during cleanup

            # Dispose repository engine if it exists
            try:
                if hasattr(repo, 'engine') and repo.engine:
                    repo.engine.dispose()
            except Exception:
                pass  # Ignore errors during cleanup

            # Close all test sessions
            if hasattr(postgres, '_test_sessions'):
                for session in postgres._test_sessions:
                    try:
                        session.close()
                    except Exception:
                        pass  # Ignore errors during cleanup

            # Dispose all test engines (closes connection pools)
            if hasattr(postgres, '_test_engines'):
                for engine in postgres._test_engines:
                    try:
                        engine.dispose()
                    except Exception:
                        pass  # Ignore errors during cleanup

            # Container cleanup happens automatically when context exits
