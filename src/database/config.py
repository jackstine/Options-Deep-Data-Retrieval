"""Database configuration management.

This module provides database configuration loading functionality that is
independent of the main application configuration. This allows the database
module to be self-contained and not depend on src.config.

The configuration is loaded from JSON files in src/database/configs/environments/
and uses environment variables for sensitive data like passwords.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.database.models.database_config import DatabaseConfig


def get_database_config(database_name: str = "equities") -> DatabaseConfig:
    """Get database configuration for current environment and database.

    This function loads database configuration from JSON files and environment
    variables. It's designed to be independent of the main config system.

    Args:
        database_name: Name of the database (equities, algorithm)

    Returns:
        DatabaseConfig for the current environment and database

    Raises:
        ValueError: If configuration is invalid or required variables are missing
        FileNotFoundError: If configuration file doesn't exist

    Environment Variables Required:
        ENVIRONMENT: Current environment (local, dev, qa, prod)
        OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD: Database password

    Example:
        >>> config = get_database_config("equities")
        >>> connection_string = config.get_connection_string(driver="psycopg2")
    """
    # Get environment name
    environment = os.getenv("ENVIRONMENT", "local").lower()

    # Get database password
    password = os.getenv("OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD")
    if password is None:
        raise ValueError(
            "OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD environment variable is not set"
        )

    # Load config from JSON file
    config_dir = Path(__file__).parent / "configs" / "environments"
    config_file = config_dir / f"{environment}.json"

    if not config_file.exists():
        raise FileNotFoundError(
            f"Database config file not found: {config_file}. "
            f"Environment: {environment}"
        )

    try:
        with open(config_file) as f:
            config_data: dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file {config_file}: {e}")

    # Validate structure
    if "databases" not in config_data:
        raise ValueError(f"Config file missing 'databases' section: {config_file}")

    if database_name not in config_data["databases"]:
        available_dbs = list(config_data["databases"].keys())
        raise ValueError(
            f"Database '{database_name}' not found in config. "
            f"Available: {available_dbs}"
        )

    # Extract database config
    db_config = config_data["databases"][database_name]

    return DatabaseConfig(
        host=db_config["host"],
        port=db_config["port"],
        database=db_config["database"],
        username=db_config["username"],
        password=password,
        environment=environment,
    )


def get_available_databases() -> list[str]:
    """Get list of available databases from configuration.

    Returns:
        List of database names

    Raises:
        ValueError: If configuration file is invalid
        FileNotFoundError: If configuration file doesn't exist
    """
    environment = os.getenv("ENVIRONMENT", "local").lower()
    config_dir = Path(__file__).parent / "configs" / "environments"
    config_file = config_dir / f"{environment}.json"

    if not config_file.exists():
        raise FileNotFoundError(f"Database config file not found: {config_file}")

    try:
        with open(config_file) as f:
            config_data: dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file {config_file}: {e}")

    if "databases" not in config_data:
        return []

    return list(config_data["databases"].keys())
