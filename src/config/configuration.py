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
from src.config.models.environment_variables import ENV_VARS
from src.config.models.equities import EquitiesConfig


class ConfigurationManager:
    """Generic configuration manager for multiple environments."""

    def __init__(self) -> None:
        """Initialize configuration manager.

        Loads environment variables from environment-specific .env files based on
        the OPTIONS_DEEP_ENV variable. If OPTIONS_DEEP_ENV is not set, loads .env.

        Raises:
            ValueError: If required environment variables are missing
            FileNotFoundError: If the specified .env file doesn't exist
        """
        self._load_environment_file()
        self._load_and_validate_env_vars()
        self._environment = os.getenv(ENV_VARS.OP_ENVIRONMENT, "local").lower()
        self._config_dir = Path(__file__).parent / "environment_configs"
        self._config_cache: dict[str, Any] = {}
        self._cache_loaded = False
        self._lock = threading.RLock()

    def _load_environment_file(self) -> None:
        """Load environment variables from the appropriate .env file.

        Uses OPTIONS_DEEP_ENV to determine which .env file to load:
        - Not set: loads .env
        - 'local': loads .env.local
        - 'dev': loads .env.dev
        - 'qa': loads .env.qa
        - 'prod': loads .env.prod

        Raises:
            ValueError: If OPTIONS_DEEP_ENV has an invalid value
            FileNotFoundError: If the specified .env file doesn't exist
        """
        options_deep_env = os.getenv("OPTIONS_DEEP_ENV")
        valid_envs = ["local", "dev", "qa", "prod"]

        if options_deep_env is None:
            env_file = ".env"
        elif options_deep_env.lower() in valid_envs:
            env_file = f".env.{options_deep_env.lower()}"
        else:
            raise ValueError(
                f"Invalid OPTIONS_DEEP_ENV value: {options_deep_env}. "
                f"Valid values are: {', '.join(valid_envs)}"
            )

        env_path = Path.cwd() / env_file

        if not env_path.exists():
            raise FileNotFoundError(
                f"Environment file not found: {env_path}. "
                f"OPTIONS_DEEP_ENV={options_deep_env or 'not set'}"
            )

        load_dotenv(env_path)

    def _load_and_validate_env_vars(self) -> None:
        """Validate that all required environment variables are set.

        Raises:
            ValueError: If any required environment variable is missing
        """
        required_vars = [
            ENV_VARS.OP_ENVIRONMENT,
            ENV_VARS.DB_PASSWORD,
            ENV_VARS.NASDAQ_API_KEY,
        ]

        missing_vars = []
        for var in required_vars:
            if os.getenv(var) is None:
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

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

    def get_environment(self) -> str:
        """Get the current environment name.

        Returns:
            Environment name (local, dev, qa, prod)
        """
        env = os.getenv(ENV_VARS.OP_ENVIRONMENT, "local")
        return env.lower()

    def get_database_password(self) -> str:
        """Get database password from environment variable.

        Returns:
            Database password

        Raises:
            ValueError: If password environment variable is not set
        """
        password = os.getenv(ENV_VARS.DB_PASSWORD)
        if password is None:
            raise ValueError(
                f"Database password environment variable {ENV_VARS.DB_PASSWORD} is not set"
            )
        return password

    def get_nasdaq_api_key(self) -> str:
        """Get NASDAQ API key from environment variable.

        Returns:
            NASDAQ API key

        Raises:
            ValueError: If NASDAQ API key environment variable is not set
        """
        api_key = os.getenv(ENV_VARS.NASDAQ_API_KEY)
        if api_key is None:
            raise ValueError(
                f"NASDAQ API key environment variable {ENV_VARS.NASDAQ_API_KEY} is not set"
            )
        return api_key

    def get_eodhd_api_key(self) -> str:
        """Get EODHD API key from environment variable.

        Returns:
            EODHD API key

        Raises:
            ValueError: If EODHD API key environment variable is not set
        """
        api_key = os.getenv(ENV_VARS.EODHD_API_KEY)
        if api_key is None:
            raise ValueError(
                f"EODHD API key environment variable {ENV_VARS.EODHD_API_KEY} is not set"
            )
        return api_key

    def get_test_limits(self) -> int | None:
        """Get test limits from environment variable.

        This is an optional environment variable used for testing to limit
        the number of companies/symbols processed in ingestion pipelines.

        Returns:
            Test limit count or None if not set

        Raises:
            No exceptions - returns None if not set or invalid
        """
        limit_str = os.getenv(ENV_VARS.TEST_LIMITS)
        if limit_str is None:
            return None

        try:
            limit = int(limit_str)
            if limit <= 0:
                return None
            return limit
        except ValueError:
            return None

    def _get_database_password(self) -> str:
        """Get database password from environment variable.

        Deprecated: Use get_database_password() instead.

        Returns:
            Database password

        Raises:
            ValueError: If password environment variable is not set
        """
        return self.get_database_password()

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
