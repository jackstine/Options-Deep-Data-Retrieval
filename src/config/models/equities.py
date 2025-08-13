"""Equities configuration model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config.models.database import DatabaseConfig


@dataclass
class EquitiesConfig:
    """Equities configuration class containing database and other settings."""

    database: DatabaseConfig

    @classmethod
    def from_config_data(
        cls, config_data: dict[str, Any], environment: str, password: str
    ) -> EquitiesConfig:
        """Create EquitiesConfig from configuration data.

        Args:
            config_data: Raw configuration data for equities
            environment: Current environment name
            password: Database password

        Returns:
            EquitiesConfig instance
        """
        database_config = DatabaseConfig(
            host=config_data["host"],
            port=config_data["port"],
            database=config_data["database"],
            username=config_data["username"],
            password=password,
            environment=environment,
        )

        return cls(database=database_config)
