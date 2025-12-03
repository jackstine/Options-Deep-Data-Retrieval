"""Environment variable type definitions and constants."""

from __future__ import annotations

from typing import NotRequired, TypedDict


class EnvironmentVariables(TypedDict):
    """Type definition for all environment variables used in the application.

    This TypedDict provides type safety for environment variable access throughout
    the codebase. All environment variables should be defined here.
    """

    ENVIRONMENT: str
    OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD: str
    NASDAQ_API_KEY: str
    EODHD_API_KEY: str
    OPTIONS_DEEP_TEST_DB_PORT: NotRequired[str]  # Optional: testcontainers dynamic port


class ENV_VARS:
    """Constants for environment variable names.

    Use these constants for IDE autocomplete and type checking when accessing
    environment variables. This prevents typos and enables better refactoring.

    Example:
        password = os.getenv(ENV_VARS.DB_PASSWORD)
    """

    OP_ENVIRONMENT = "ENVIRONMENT"
    DB_PASSWORD = "OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD"
    NASDAQ_API_KEY = "NASDAQ_API_KEY"
    EODHD_API_KEY = "EODHD_API_KEY"
    TEST_LIMITS = "OPTIONS_DEEP_TEST_LIMITS"
    TEST_DB_PORT = "OPTIONS_DEEP_TEST_DB_PORT"
