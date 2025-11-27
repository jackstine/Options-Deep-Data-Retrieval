"""System configuration object with typed getters and setters."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from decimal import Decimal

from src.repos.system.system_repository import SystemRepository

logger = logging.getLogger(__name__)


class SystemConfig:
    """Stateful system configuration object with typed getters and setters.

    Provides type-safe access to system configuration values stored in the database.
    Values are stored as strings and converted to the appropriate type on retrieval.

    Example:
        config = SystemConfig(system_name=1, repo=SystemRepository())
        config.set_int(key=100, value=42)
        value = config.get_int(key=100)  # Returns 42

    Args:
        system_name: The system identifier
        repo: Optional SystemRepository instance (creates new one if not provided)
    """

    def __init__(self, system_name: int, repo: SystemRepository | None = None) -> None:
        """Initialize SystemConfig.

        Args:
            system_name: The system identifier
            repo: Optional SystemRepository instance
        """
        self.system_name = system_name
        self._repo = repo if repo is not None else SystemRepository()

    # String operations

    def get_str(self, key: int) -> str | None:
        """Get a string value.

        Args:
            key: The configuration key

        Returns:
            The string value, or None if not found
        """
        return self._repo.get_value(self.system_name, key)

    def set_str(self, key: int, value: str) -> None:
        """Set a string value.

        Args:
            key: The configuration key
            value: The string value to store
        """
        self._repo.set_value(self.system_name, key, value)

    # Integer operations

    def get_int(self, key: int) -> int | None:
        """Get an integer value.

        Args:
            key: The configuration key

        Returns:
            The integer value, or None if not found

        Raises:
            ValueError: If the stored value cannot be converted to int
        """
        value = self._repo.get_value(self.system_name, key)
        if value is None:
            return None
        try:
            return int(value)
        except ValueError as e:
            logger.error(f"Failed to parse int for system={self.system_name}, key={key}: {e}")
            raise ValueError(f"Value '{value}' cannot be converted to int") from e

    def set_int(self, key: int, value: int) -> None:
        """Set an integer value.

        Args:
            key: The configuration key
            value: The integer value to store
        """
        self._repo.set_value(self.system_name, key, str(value))

    # Float operations

    def get_float(self, key: int) -> float | None:
        """Get a float value.

        Args:
            key: The configuration key

        Returns:
            The float value, or None if not found

        Raises:
            ValueError: If the stored value cannot be converted to float
        """
        value = self._repo.get_value(self.system_name, key)
        if value is None:
            return None
        try:
            return float(value)
        except ValueError as e:
            logger.error(f"Failed to parse float for system={self.system_name}, key={key}: {e}")
            raise ValueError(f"Value '{value}' cannot be converted to float") from e

    def set_float(self, key: int, value: float) -> None:
        """Set a float value.

        Args:
            key: The configuration key
            value: The float value to store
        """
        self._repo.set_value(self.system_name, key, str(value))

    # Boolean operations

    def get_bool(self, key: int) -> bool | None:
        """Get a boolean value.

        Accepts: 'true', 'false', '1', '0', 'yes', 'no' (case-insensitive)

        Args:
            key: The configuration key

        Returns:
            The boolean value, or None if not found

        Raises:
            ValueError: If the stored value cannot be converted to bool
        """
        value = self._repo.get_value(self.system_name, key)
        if value is None:
            return None

        value_lower = value.lower().strip()
        if value_lower in ("true", "1", "yes"):
            return True
        elif value_lower in ("false", "0", "no"):
            return False
        else:
            logger.error(f"Failed to parse bool for system={self.system_name}, key={key}")
            raise ValueError(
                f"Value '{value}' cannot be converted to bool. "
                "Expected: 'true', 'false', '1', '0', 'yes', or 'no'"
            )

    def set_bool(self, key: int, value: bool) -> None:
        """Set a boolean value.

        Stores as 'true' or 'false'.

        Args:
            key: The configuration key
            value: The boolean value to store
        """
        self._repo.set_value(self.system_name, key, "true" if value else "false")

    # Date operations

    def get_date(self, key: int) -> date | None:
        """Get a date value.

        Expects ISO format: YYYY-MM-DD

        Args:
            key: The configuration key

        Returns:
            The date value, or None if not found

        Raises:
            ValueError: If the stored value cannot be converted to date
        """
        value = self._repo.get_value(self.system_name, key)
        if value is None:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError as e:
            logger.error(f"Failed to parse date for system={self.system_name}, key={key}: {e}")
            raise ValueError(
                f"Value '{value}' cannot be converted to date. Expected ISO format (YYYY-MM-DD)"
            ) from e

    def set_date(self, key: int, value: date) -> None:
        """Set a date value.

        Stores in ISO format: YYYY-MM-DD

        Args:
            key: The configuration key
            value: The date value to store
        """
        self._repo.set_value(self.system_name, key, value.isoformat())

    # DateTime operations

    def get_datetime(self, key: int) -> datetime | None:
        """Get a datetime value.

        Expects ISO format with optional timezone

        Args:
            key: The configuration key

        Returns:
            The datetime value, or None if not found

        Raises:
            ValueError: If the stored value cannot be converted to datetime
        """
        value = self._repo.get_value(self.system_name, key)
        if value is None:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError as e:
            logger.error(f"Failed to parse datetime for system={self.system_name}, key={key}: {e}")
            raise ValueError(
                f"Value '{value}' cannot be converted to datetime. Expected ISO format"
            ) from e

    def set_datetime(self, key: int, value: datetime) -> None:
        """Set a datetime value.

        Stores in ISO format with timezone if available

        Args:
            key: The configuration key
            value: The datetime value to store
        """
        self._repo.set_value(self.system_name, key, value.isoformat())

    # Decimal operations

    def get_decimal(self, key: int) -> Decimal | None:
        """Get a Decimal value.

        Args:
            key: The configuration key

        Returns:
            The Decimal value, or None if not found

        Raises:
            ValueError: If the stored value cannot be converted to Decimal
        """
        value = self._repo.get_value(self.system_name, key)
        if value is None:
            return None
        try:
            return Decimal(value)
        except (ValueError, ArithmeticError) as e:
            logger.error(f"Failed to parse Decimal for system={self.system_name}, key={key}: {e}")
            raise ValueError(f"Value '{value}' cannot be converted to Decimal") from e

    def set_decimal(self, key: int, value: Decimal) -> None:
        """Set a Decimal value.

        Args:
            key: The configuration key
            value: The Decimal value to store
        """
        self._repo.set_value(self.system_name, key, str(value))

    # JSON operations

    def get_json(self, key: int) -> dict | list | None:
        """Get a JSON value (dict or list).

        Args:
            key: The configuration key

        Returns:
            The parsed JSON value (dict or list), or None if not found

        Raises:
            ValueError: If the stored value cannot be parsed as JSON
        """
        value = self._repo.get_value(self.system_name, key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for system={self.system_name}, key={key}: {e}")
            raise ValueError(f"Value '{value}' cannot be parsed as JSON") from e

    def set_json(self, key: int, value: dict | list) -> None:
        """Set a JSON value (dict or list).

        Args:
            key: The configuration key
            value: The dict or list to store as JSON

        Raises:
            TypeError: If value cannot be serialized to JSON
        """
        try:
            json_str = json.dumps(value)
            self._repo.set_value(self.system_name, key, json_str)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize JSON for system={self.system_name}, key={key}: {e}")
            raise TypeError(f"Value cannot be serialized to JSON: {e}") from e

    # Utility methods

    def delete(self, key: int) -> bool:
        """Delete a configuration value.

        Args:
            key: The configuration key

        Returns:
            True if a value was deleted, False if no value existed
        """
        return self._repo.delete_value(self.system_name, key)

    def get_all(self) -> dict[int, str]:
        """Get all configuration values for this system as strings.

        Returns:
            Dictionary mapping keys to string values
        """
        return self._repo.get_all_for_system(self.system_name)

    def __repr__(self) -> str:
        """String representation of SystemConfig."""
        return f"<SystemConfig(system_name={self.system_name})>"
