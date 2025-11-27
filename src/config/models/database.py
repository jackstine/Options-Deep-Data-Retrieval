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

    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string.

        For testcontainers: Checks for OPTIONS_DEEP_TEST_DB_PORT environment variable
        and overrides the configured port if present. This allows tests to use
        dynamically assigned ports from Docker containers.

        Returns:
            SQLAlchemy connection string
        """
        # Override port if testcontainers sets dynamic port
        test_db_port = os.getenv("OPTIONS_DEEP_TEST_DB_PORT")
        port = test_db_port if test_db_port else self.port

        return f"postgresql://{self.username}:{self.password}@{self.host}:{port}/{self.database}"

    def get_async_connection_string(self) -> str:
        """Get PostgreSQL async connection string.

        For testcontainers: Checks for OPTIONS_DEEP_TEST_DB_PORT environment variable
        and overrides the configured port if present.

        Returns:
            SQLAlchemy async connection string
        """
        # Override port if testcontainers sets dynamic port
        test_db_port = os.getenv("OPTIONS_DEEP_TEST_DB_PORT")
        port = test_db_port if test_db_port else self.port

        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{port}/{self.database}"
