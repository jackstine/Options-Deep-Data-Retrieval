"""Environment variable configuration management."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class EnvironmentVariables:
    _NASDAQ_API_KEY: str = "NASDAQ_API_KEY"

    def __post_init__(self):
        # need to load the environment variables from the .env file.
        load_dotenv()

    @classmethod
    def get_nasdaq_api_key(cls):
        """Get the Nasdaq API Key"""
        return cls._get_value(cls._NASDAQ_API_KEY)

    @staticmethod
    def _get_value(key):
        """Load environment variables after initialization."""
        value = os.getenv(key)
        if value == None:
            raise BaseException(f"Was not able to get the environment variable {key}")
        else:
            return value


# Global instance
ENVIRONMENT_VARIABLES = EnvironmentVariables()
