"""Unit tests for SystemConfig with typed getters and setters."""

import json
import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock

from src.repos.system.system_config import SystemConfig


class TestSystemConfigStringOperations(unittest.TestCase):
    """Test string get/set operations."""

    def setUp(self) -> None:
        """Set up test fixtures with mocked repository."""
        self.mock_repo = Mock()
        self.config = SystemConfig(system_name=1, repo=self.mock_repo)

    def test_get_str(self) -> None:
        """Test get_str returns string value."""
        self.mock_repo.get_value.return_value = "test_string"

        value = self.config.get_str(key=100)

        self.assertEqual(value, "test_string")
        self.mock_repo.get_value.assert_called_once_with(1, 100)

    def test_get_str_none(self) -> None:
        """Test get_str returns None when value not found."""
        self.mock_repo.get_value.return_value = None

        value = self.config.get_str(key=100)

        self.assertIsNone(value)

    def test_set_str(self) -> None:
        """Test set_str stores string value."""
        self.config.set_str(key=100, value="test_value")

        self.mock_repo.set_value.assert_called_once_with(1, 100, "test_value")


class TestSystemConfigIntegerOperations(unittest.TestCase):
    """Test integer get/set operations."""

    def setUp(self) -> None:
        """Set up test fixtures with mocked repository."""
        self.mock_repo = Mock()
        self.config = SystemConfig(system_name=1, repo=self.mock_repo)

    def test_get_int(self) -> None:
        """Test get_int parses integer value."""
        self.mock_repo.get_value.return_value = "42"

        value = self.config.get_int(key=100)

        self.assertEqual(value, 42)
        self.assertIsInstance(value, int)

    def test_get_int_none(self) -> None:
        """Test get_int returns None when value not found."""
        self.mock_repo.get_value.return_value = None

        value = self.config.get_int(key=100)

        self.assertIsNone(value)

    def test_get_int_invalid_raises_error(self) -> None:
        """Test get_int raises ValueError for invalid integer."""
        self.mock_repo.get_value.return_value = "not_an_int"

        with self.assertRaises(ValueError) as context:
            self.config.get_int(key=100)

        self.assertIn("cannot be converted to int", str(context.exception))

    def test_set_int(self) -> None:
        """Test set_int stores integer as string."""
        self.config.set_int(key=100, value=42)

        self.mock_repo.set_value.assert_called_once_with(1, 100, "42")


class TestSystemConfigFloatOperations(unittest.TestCase):
    """Test float get/set operations."""

    def setUp(self) -> None:
        """Set up test fixtures with mocked repository."""
        self.mock_repo = Mock()
        self.config = SystemConfig(system_name=1, repo=self.mock_repo)

    def test_get_float(self) -> None:
        """Test get_float parses float value."""
        self.mock_repo.get_value.return_value = "3.14"

        value = self.config.get_float(key=100)

        self.assertAlmostEqual(value, 3.14)
        self.assertIsInstance(value, float)

    def test_get_float_none(self) -> None:
        """Test get_float returns None when value not found."""
        self.mock_repo.get_value.return_value = None

        value = self.config.get_float(key=100)

        self.assertIsNone(value)

    def test_get_float_invalid_raises_error(self) -> None:
        """Test get_float raises ValueError for invalid float."""
        self.mock_repo.get_value.return_value = "not_a_float"

        with self.assertRaises(ValueError) as context:
            self.config.get_float(key=100)

        self.assertIn("cannot be converted to float", str(context.exception))

    def test_set_float(self) -> None:
        """Test set_float stores float as string."""
        self.config.set_float(key=100, value=3.14)

        self.mock_repo.set_value.assert_called_once_with(1, 100, "3.14")


class TestSystemConfigBooleanOperations(unittest.TestCase):
    """Test boolean get/set operations."""

    def setUp(self) -> None:
        """Set up test fixtures with mocked repository."""
        self.mock_repo = Mock()
        self.config = SystemConfig(system_name=1, repo=self.mock_repo)

    def test_get_bool_true_values(self) -> None:
        """Test get_bool parses various true values."""
        true_values = ["true", "True", "TRUE", "1", "yes", "YES"]

        for true_val in true_values:
            self.mock_repo.get_value.return_value = true_val
            value = self.config.get_bool(key=100)
            self.assertTrue(value, f"Failed for value: {true_val}")

    def test_get_bool_false_values(self) -> None:
        """Test get_bool parses various false values."""
        false_values = ["false", "False", "FALSE", "0", "no", "NO"]

        for false_val in false_values:
            self.mock_repo.get_value.return_value = false_val
            value = self.config.get_bool(key=100)
            self.assertFalse(value, f"Failed for value: {false_val}")

    def test_get_bool_none(self) -> None:
        """Test get_bool returns None when value not found."""
        self.mock_repo.get_value.return_value = None

        value = self.config.get_bool(key=100)

        self.assertIsNone(value)

    def test_get_bool_invalid_raises_error(self) -> None:
        """Test get_bool raises ValueError for invalid boolean."""
        self.mock_repo.get_value.return_value = "not_a_bool"

        with self.assertRaises(ValueError) as context:
            self.config.get_bool(key=100)

        self.assertIn("cannot be converted to bool", str(context.exception))

    def test_set_bool_true(self) -> None:
        """Test set_bool stores True as 'true'."""
        self.config.set_bool(key=100, value=True)

        self.mock_repo.set_value.assert_called_once_with(1, 100, "true")

    def test_set_bool_false(self) -> None:
        """Test set_bool stores False as 'false'."""
        self.config.set_bool(key=100, value=False)

        self.mock_repo.set_value.assert_called_once_with(1, 100, "false")


class TestSystemConfigDateOperations(unittest.TestCase):
    """Test date get/set operations."""

    def setUp(self) -> None:
        """Set up test fixtures with mocked repository."""
        self.mock_repo = Mock()
        self.config = SystemConfig(system_name=1, repo=self.mock_repo)

    def test_get_date(self) -> None:
        """Test get_date parses ISO date."""
        self.mock_repo.get_value.return_value = "2025-11-25"

        value = self.config.get_date(key=100)

        self.assertEqual(value, date(2025, 11, 25))
        self.assertIsInstance(value, date)

    def test_get_date_none(self) -> None:
        """Test get_date returns None when value not found."""
        self.mock_repo.get_value.return_value = None

        value = self.config.get_date(key=100)

        self.assertIsNone(value)

    def test_get_date_invalid_raises_error(self) -> None:
        """Test get_date raises ValueError for invalid date."""
        self.mock_repo.get_value.return_value = "not_a_date"

        with self.assertRaises(ValueError) as context:
            self.config.get_date(key=100)

        self.assertIn("cannot be converted to date", str(context.exception))

    def test_set_date(self) -> None:
        """Test set_date stores date in ISO format."""
        test_date = date(2025, 11, 25)
        self.config.set_date(key=100, value=test_date)

        self.mock_repo.set_value.assert_called_once_with(1, 100, "2025-11-25")


class TestSystemConfigDateTimeOperations(unittest.TestCase):
    """Test datetime get/set operations."""

    def setUp(self) -> None:
        """Set up test fixtures with mocked repository."""
        self.mock_repo = Mock()
        self.config = SystemConfig(system_name=1, repo=self.mock_repo)

    def test_get_datetime(self) -> None:
        """Test get_datetime parses ISO datetime."""
        self.mock_repo.get_value.return_value = "2025-11-25T10:30:00"

        value = self.config.get_datetime(key=100)

        self.assertEqual(value, datetime(2025, 11, 25, 10, 30, 0))
        self.assertIsInstance(value, datetime)

    def test_get_datetime_none(self) -> None:
        """Test get_datetime returns None when value not found."""
        self.mock_repo.get_value.return_value = None

        value = self.config.get_datetime(key=100)

        self.assertIsNone(value)

    def test_get_datetime_invalid_raises_error(self) -> None:
        """Test get_datetime raises ValueError for invalid datetime."""
        self.mock_repo.get_value.return_value = "not_a_datetime"

        with self.assertRaises(ValueError) as context:
            self.config.get_datetime(key=100)

        self.assertIn("cannot be converted to datetime", str(context.exception))

    def test_set_datetime(self) -> None:
        """Test set_datetime stores datetime in ISO format."""
        test_datetime = datetime(2025, 11, 25, 10, 30, 0)
        self.config.set_datetime(key=100, value=test_datetime)

        self.mock_repo.set_value.assert_called_once_with(1, 100, "2025-11-25T10:30:00")


class TestSystemConfigDecimalOperations(unittest.TestCase):
    """Test Decimal get/set operations."""

    def setUp(self) -> None:
        """Set up test fixtures with mocked repository."""
        self.mock_repo = Mock()
        self.config = SystemConfig(system_name=1, repo=self.mock_repo)

    def test_get_decimal(self) -> None:
        """Test get_decimal parses Decimal value."""
        self.mock_repo.get_value.return_value = "123.456"

        value = self.config.get_decimal(key=100)

        self.assertEqual(value, Decimal("123.456"))
        self.assertIsInstance(value, Decimal)

    def test_get_decimal_none(self) -> None:
        """Test get_decimal returns None when value not found."""
        self.mock_repo.get_value.return_value = None

        value = self.config.get_decimal(key=100)

        self.assertIsNone(value)

    def test_get_decimal_invalid_raises_error(self) -> None:
        """Test get_decimal raises ValueError for invalid Decimal."""
        self.mock_repo.get_value.return_value = "not_a_decimal"

        with self.assertRaises(ValueError) as context:
            self.config.get_decimal(key=100)

        self.assertIn("cannot be converted to Decimal", str(context.exception))

    def test_set_decimal(self) -> None:
        """Test set_decimal stores Decimal as string."""
        test_decimal = Decimal("123.456")
        self.config.set_decimal(key=100, value=test_decimal)

        self.mock_repo.set_value.assert_called_once_with(1, 100, "123.456")


class TestSystemConfigJSONOperations(unittest.TestCase):
    """Test JSON get/set operations."""

    def setUp(self) -> None:
        """Set up test fixtures with mocked repository."""
        self.mock_repo = Mock()
        self.config = SystemConfig(system_name=1, repo=self.mock_repo)

    def test_get_json_dict(self) -> None:
        """Test get_json parses dict from JSON string."""
        test_data = {"key": "value", "number": 42}
        self.mock_repo.get_value.return_value = json.dumps(test_data)

        value = self.config.get_json(key=100)

        self.assertEqual(value, test_data)
        self.assertIsInstance(value, dict)

    def test_get_json_list(self) -> None:
        """Test get_json parses list from JSON string."""
        test_data = ["item1", "item2", 3]
        self.mock_repo.get_value.return_value = json.dumps(test_data)

        value = self.config.get_json(key=100)

        self.assertEqual(value, test_data)
        self.assertIsInstance(value, list)

    def test_get_json_none(self) -> None:
        """Test get_json returns None when value not found."""
        self.mock_repo.get_value.return_value = None

        value = self.config.get_json(key=100)

        self.assertIsNone(value)

    def test_get_json_invalid_raises_error(self) -> None:
        """Test get_json raises ValueError for invalid JSON."""
        self.mock_repo.get_value.return_value = "not valid json"

        with self.assertRaises(ValueError) as context:
            self.config.get_json(key=100)

        self.assertIn("cannot be parsed as JSON", str(context.exception))

    def test_set_json_dict(self) -> None:
        """Test set_json stores dict as JSON string."""
        test_data = {"key": "value", "number": 42}
        self.config.set_json(key=100, value=test_data)

        expected_json = json.dumps(test_data)
        self.mock_repo.set_value.assert_called_once_with(1, 100, expected_json)

    def test_set_json_list(self) -> None:
        """Test set_json stores list as JSON string."""
        test_data = ["item1", "item2", 3]
        self.config.set_json(key=100, value=test_data)

        expected_json = json.dumps(test_data)
        self.mock_repo.set_value.assert_called_once_with(1, 100, expected_json)


class TestSystemConfigUtilityMethods(unittest.TestCase):
    """Test utility methods of SystemConfig."""

    def setUp(self) -> None:
        """Set up test fixtures with mocked repository."""
        self.mock_repo = Mock()
        self.config = SystemConfig(system_name=1, repo=self.mock_repo)

    def test_delete(self) -> None:
        """Test delete calls repository delete_value."""
        self.mock_repo.delete_value.return_value = True

        result = self.config.delete(key=100)

        self.assertTrue(result)
        self.mock_repo.delete_value.assert_called_once_with(1, 100)

    def test_get_all(self) -> None:
        """Test get_all returns all config values."""
        expected_data = {100: "value1", 200: "value2"}
        self.mock_repo.get_all_for_system.return_value = expected_data

        result = self.config.get_all()

        self.assertEqual(result, expected_data)
        self.mock_repo.get_all_for_system.assert_called_once_with(1)

    def test_repr(self) -> None:
        """Test __repr__ method."""
        repr_str = repr(self.config)

        self.assertIn("SystemConfig", repr_str)
        self.assertIn("system_name=1", repr_str)


class TestSystemConfigInitialization(unittest.TestCase):
    """Test SystemConfig initialization."""

    def test_init_with_repo(self) -> None:
        """Test initialization with provided repository."""
        mock_repo = Mock()
        config = SystemConfig(system_name=5, repo=mock_repo)

        self.assertEqual(config.system_name, 5)
        self.assertEqual(config._repo, mock_repo)

    def test_init_without_repo_creates_default(self) -> None:
        """Test initialization without repo creates SystemRepository."""
        with unittest.mock.patch("src.repos.system.system_config.SystemRepository") as MockRepo:
            config = SystemConfig(system_name=5)

            MockRepo.assert_called_once()
            self.assertEqual(config.system_name, 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
