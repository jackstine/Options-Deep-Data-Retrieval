"""Generic configuration management for multiple environments."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.config.models.algorithm import AlgorithmConfig
from src.config.models.database import DatabaseConfig
from src.config.models.equities import EquitiesConfig


class ConfigurationManager:
    """Generic configuration manager for multiple environments."""

    def __init__(self) -> None:
        """Initialize configuration manager."""
        load_dotenv()
        self._environment = os.getenv("ENVIRONMENT", "local").lower()
        self._config_dir = Path(__file__).parent / "environment_configs"
        self._config_cache: dict[str, Any] = {}
        self._cache_loaded = False
        self._lock = threading.RLock()

    def get_equities_config(self) -> EquitiesConfig:
        """Get equities configuration for current environment.

        Returns:
            EquitiesConfig for the current environment
        """
        config_data = self._load_config()

        if "databases" not in config_data or "equities" not in config_data["databases"]:
            raise ValueError("Equities database configuration not found")

        password = self._get_database_password()

        return EquitiesConfig.from_config_data(
            config_data["databases"]["equities"], self._environment, password
        )

    def get_algorithm_config(self) -> AlgorithmConfig:
        """Get algorithm configuration for current environment.

        Returns:
            AlgorithmConfig for the current environment
        """
        config_data = self._load_config()

        if (
            "databases" not in config_data
            or "algorithm" not in config_data["databases"]
        ):
            raise ValueError("Algorithm database configuration not found")

        password = self._get_database_password()

        return AlgorithmConfig.from_config_data(
            config_data["databases"]["algorithm"], self._environment, password
        )

    def get_database_config(self, database_name: str = "equities") -> DatabaseConfig:
        """Get database configuration for current environment and database.

        Args:
            database_name: Name of the database (equities, algorithm)

        Returns:
            DatabaseConfig for the current environment and database
        """
        config_data = self._load_config()

        if "databases" not in config_data:
            raise ValueError("Config file missing 'databases' section")

        if database_name not in config_data["databases"]:
            available_dbs = list(config_data["databases"].keys())
            raise ValueError(
                f"Database '{database_name}' not found in config. Available: {available_dbs}"
            )

        db_config = config_data["databases"][database_name]
        password = self._get_database_password()

        return DatabaseConfig(
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["database"],
            username=db_config["username"],
            password=password,
            environment=self._environment,
        )

    def get_available_databases(self) -> list[str]:
        """Get list of available databases from configuration.

        Returns:
            List of database names
        """
        config_data = self._load_config()
        if "databases" not in config_data:
            return []
        return list(config_data["databases"].keys())

    def _get_database_password(self) -> str:
        """Get database password from environment variable.

        Returns:
            Database password

        Raises:
            ValueError: If password environment variable is not set
        """
        password = os.getenv("OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD")
        if password is None:
            raise ValueError(
                "Database password environment variable OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD is not set"
            )
        return password

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from JSON file with thread-safe caching.

        Returns:
            Configuration dictionary

        Raises:
            ValueError: If configuration file is not found or invalid
        """
        with self._lock:
            # Double-check pattern: check again inside the lock
            if self._cache_loaded and self._config_cache:
                return self._config_cache

            config_file = self._config_dir / f"{self._environment}.json"

            if not config_file.exists():
                raise ValueError(f"Config file not found: {config_file}")

            try:
                with open(config_file) as f:
                    self._config_cache = json.load(f)
                    self._cache_loaded = True
                    return self._config_cache
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in config file {config_file}: {e}")

    def clear_cache(self) -> None:
        """Clear the configuration cache in a thread-safe manner."""
        with self._lock:
            self._config_cache = {}
            self._cache_loaded = False

    def reload_config(self) -> None:
        """Reload configuration from file, bypassing cache in a thread-safe manner."""
        self.clear_cache()
        self._load_config()

    @property
    def environment(self) -> str:
        """Get current environment name."""
        return self._environment


# Global instance
CONFIG = ConfigurationManager()
