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

        Args:
            driver: Optional SQLAlchemy driver name (e.g., "psycopg2", "psycopg").
                    If provided, will be appended as postgresql+driver://

        Returns:
            SQLAlchemy connection string
        """
        # Override port if testcontainers sets dynamic port
        test_db_port = os.getenv("OPTIONS_DEEP_TEST_DB_PORT")
        port = test_db_port if test_db_port else self.port

        driver_part = f"+{driver}" if driver else ""
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
