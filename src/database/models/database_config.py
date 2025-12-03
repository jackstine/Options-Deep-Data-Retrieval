"""Database configuration model."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration class."""

    host: str
    port: int
    database: str
    username: str
    password: str
    environment: str

    def get_connection_string(self, driver: str = "") -> str:
        """Get PostgreSQL connection string.

        For testcontainers: Checks for OPTIONS_DEEP_TEST_DB_PORT environment variable
        and overrides the configured port if present. This allows tests to use
        dynamically assigned ports from Docker containers.

        For Docker init: Checks for DOCKER_INIT environment variable and uses Unix
        socket connection when PostgreSQL is only listening on Unix socket during
        container initialization.

        Args:
            driver: Optional SQLAlchemy driver name (e.g., "psycopg2", "psycopg").
                    If provided, will be appended as postgresql+driver://

        Returns:
            SQLAlchemy connection string
        """
        driver_part = f"+{driver}" if driver else ""

        # Check if running during Docker initialization (when only Unix socket is available)
        if os.getenv("DOCKER_INIT") == "true":
            # Use Unix socket connection for Docker initialization
            # PostgreSQL in docker-entrypoint-initdb.d only listens on Unix socket, not TCP
            # Cannot use URL encoding or query params with create_engine directly
            # This connection string won't work - need to use connect_args in create_engine
            # Returning a placeholder that will be overridden by connect_args
            return f"postgresql{driver_part}://{self.username}:{self.password}@/{self.database}"

        # Override port if testcontainers sets dynamic port
        test_db_port = os.getenv("OPTIONS_DEEP_TEST_DB_PORT")
        port = test_db_port if test_db_port else self.port

        return f"postgresql{driver_part}://{self.username}:{self.password}@{self.host}:{port}/{self.database}"

    def get_async_connection_string(self, driver: str = "asyncpg") -> str:
        """Get PostgreSQL async connection string.

        For testcontainers: Checks for OPTIONS_DEEP_TEST_DB_PORT environment variable
        and overrides the configured port if present.

        Args:
            driver: SQLAlchemy async driver name. Defaults to "asyncpg".
                    Other options include "psycopg" (psycopg3 async).

        Returns:
            SQLAlchemy async connection string
        """
        # Override port if testcontainers sets dynamic port
        test_db_port = os.getenv("OPTIONS_DEEP_TEST_DB_PORT")
        port = test_db_port if test_db_port else self.port

        return f"postgresql+{driver}://{self.username}:{self.password}@{self.host}:{port}/{self.database}"
