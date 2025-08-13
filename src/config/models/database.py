"""Database configuration model."""

from __future__ import annotations

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

        Returns:
            SQLAlchemy connection string
        """
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def get_async_connection_string(self) -> str:
        """Get PostgreSQL async connection string.

        Returns:
            SQLAlchemy async connection string
        """
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
