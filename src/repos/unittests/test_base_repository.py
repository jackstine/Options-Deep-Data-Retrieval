"""Unit tests for BaseRepository private functions.

Run with:
    export OPTIONS_DEEP_ENV=unittest && python -m unittest src.repos.unittests.test_base_repository -v
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import date
from typing import Any
from unittest.mock import MagicMock, Mock, patch

from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import DeclarativeMeta

from src.repos.base_repository import BaseRepository


# Mock data model for testing
@dataclass
class MockDataModel:
    """Mock data model for testing."""

    id: int = 0
    name: str | None = None
    description: str | None = None
    is_active: bool = True
    count: int = 0
    price: float = 0.0
    created_date: date | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "count": self.count,
            "price": self.price,
            "created_date": self.created_date,
            "tags": self.tags,
        }

    def to_db_model(self) -> Any:
        """Convert to database model."""
        return Mock()

    @classmethod
    def from_db_model(cls, db_model: Any) -> MockDataModel:
        """Create from database model."""
        return cls()


# Mock DB model for testing
class MockDBModel:
    """Mock SQLAlchemy database model."""

    id = Mock()
    name = Mock()
    description = Mock()
    is_active = Mock()
    count = Mock()
    price = Mock()
    created_date = Mock()


# Concrete implementation of BaseRepository for testing
class ConcreteBaseRepository(BaseRepository[MockDataModel, MockDBModel]):
    """Concrete implementation of BaseRepository for testing purposes."""

    def _create_id_filter(self, id: int) -> MockDataModel:
        """Create a data model filter for ID lookups."""
        return MockDataModel(id=id)


class TestExtractFilterConditions(unittest.TestCase):
    """Test _extract_filter_conditions private method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create a mock repository instance
        mock_config_getter = Mock(return_value=Mock(database=Mock(get_connection_string=Mock(return_value="sqlite:///:memory:"))))

        with patch('src.repos.base_repository.create_engine'), \
             patch('src.repos.base_repository.sessionmaker'):
            self.repo = ConcreteBaseRepository(
                config_getter=mock_config_getter,
                data_model_class=MockDataModel,
                db_model_class=MockDBModel
            )

    def test_empty_filter_model_returns_all_non_none_defaults(self) -> None:
        """Test that filter model with default values returns all non-None fields."""
        filter_model = MockDataModel()
        result = self.repo._extract_filter_conditions(filter_model)
        # All fields with non-None defaults are included (id=0, is_active=True, etc.)
        # Note: name, description, and created_date are None by default, so they're filtered out
        expected = {
            "id": 0,
            "is_active": True,
            "count": 0,
            "price": 0.0,
        }
        self.assertEqual(result, expected)

    def test_single_valid_field(self) -> None:
        """Test extraction with single valid field set to non-default value."""
        filter_model = MockDataModel(name="test_name")
        result = self.repo._extract_filter_conditions(filter_model)
        # All non-None fields are included, not just the one we explicitly set
        # description is None, so it's filtered out
        expected = {
            "id": 0,
            "name": "test_name",
            "is_active": True,
            "count": 0,
            "price": 0.0,
        }
        self.assertEqual(result, expected)

    def test_multiple_valid_fields(self) -> None:
        """Test extraction with multiple fields set to non-default values."""
        filter_model = MockDataModel(name="test_name", count=5, price=9.99)
        result = self.repo._extract_filter_conditions(filter_model)
        # description is None, so it's filtered out
        expected = {
            "id": 0,
            "name": "test_name",
            "is_active": True,
            "count": 5,
            "price": 9.99,
        }
        self.assertEqual(result, expected)

    def test_filters_out_none_values(self) -> None:
        """Test that None values are filtered out."""
        filter_model = MockDataModel(name="test_name")
        filter_model.description = None  # type: ignore[assignment]
        result = self.repo._extract_filter_conditions(filter_model)
        # description should not be in result since it's None
        self.assertNotIn("description", result)
        # But other non-None fields should still be there
        self.assertIn("name", result)
        self.assertIn("is_active", result)

    def test_includes_empty_string(self) -> None:
        """Test that empty strings are included (they are non-None)."""
        filter_model = MockDataModel(description="")
        result = self.repo._extract_filter_conditions(filter_model)
        # Empty string is non-None, so it should be included
        # name is None by default, so it's filtered out
        self.assertIn("description", result)
        self.assertEqual(result["description"], "")
        self.assertNotIn("name", result)

    def test_includes_zero_values(self) -> None:
        """Test that zero values are included (they are non-None)."""
        filter_model = MockDataModel(count=0, price=0.0)
        result = self.repo._extract_filter_conditions(filter_model)
        # Zero is non-None, so it should be included
        self.assertIn("count", result)
        self.assertIn("price", result)
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["price"], 0.0)

    def test_excludes_none_date(self) -> None:
        """Test that None date is excluded from filter conditions."""
        filter_model = MockDataModel(created_date=None)
        result = self.repo._extract_filter_conditions(filter_model)
        # None date should be filtered out
        self.assertNotIn("created_date", result)

    def test_includes_valid_date(self) -> None:
        """Test that valid date is included."""
        test_date = date(2024, 1, 15)
        filter_model = MockDataModel(created_date=test_date)
        result = self.repo._extract_filter_conditions(filter_model)
        self.assertIn("created_date", result)
        self.assertEqual(result["created_date"], test_date)

    def test_includes_boolean_false(self) -> None:
        """Test that boolean False is included."""
        filter_model = MockDataModel(is_active=False)
        result = self.repo._extract_filter_conditions(filter_model)
        self.assertIn("is_active", result)
        self.assertEqual(result["is_active"], False)

    def test_excludes_empty_collections_not_in_db(self) -> None:
        """Test that collections (even empty) are excluded if field doesn't exist in DB."""
        filter_model = MockDataModel(tags=[])
        result = self.repo._extract_filter_conditions(filter_model)
        # tags field doesn't exist in MockDBModel, so it's excluded
        self.assertNotIn("tags", result)

    def test_excludes_collections_not_in_db(self) -> None:
        """Test that collections are excluded if field doesn't exist in DB model."""
        filter_model = MockDataModel(tags=["tag1", "tag2"])
        result = self.repo._extract_filter_conditions(filter_model)
        # tags field doesn't exist in MockDBModel, so it's excluded
        self.assertNotIn("tags", result)

    def test_id_query_with_default_boolean_true(self) -> None:
        """Test that ID query includes all non-None fields including boolean True."""
        filter_model = MockDataModel(id=123, is_active=True)
        result = self.repo._extract_filter_conditions(filter_model)
        # All non-None fields are included
        # name and description are None, so they're filtered out
        expected = {
            "id": 123,
            "is_active": True,
            "count": 0,
            "price": 0.0,
        }
        self.assertEqual(result, expected)

    def test_id_query_with_boolean_false(self) -> None:
        """Test that ID query with boolean False includes all non-None fields."""
        # Note: For ID-only lookups, use get_by_id() instead of get_filter()
        filter_model = MockDataModel(id=123, is_active=False)
        result = self.repo._extract_filter_conditions(filter_model)
        # All non-None fields are included
        # name and description are None, so they're filtered out
        expected = {
            "id": 123,
            "is_active": False,
            "count": 0,
            "price": 0.0,
        }
        self.assertEqual(result, expected)

    def test_id_with_other_fields(self) -> None:
        """Test ID with other fields includes all non-None fields."""
        # Note: For complex filters, use get_filter() instead of get_by_id()
        filter_model = MockDataModel(id=123, name="test")
        result = self.repo._extract_filter_conditions(filter_model)
        # All non-None fields are included
        # description is None, so it's filtered out
        expected = {
            "id": 123,
            "name": "test",
            "is_active": True,
            "count": 0,
            "price": 0.0,
        }
        self.assertEqual(result, expected)

    def test_excludes_fields_not_in_db_model(self) -> None:
        """Test that fields not present in DB model are excluded."""
        filter_model = MockDataModel(tags=["tag1"])
        result = self.repo._extract_filter_conditions(filter_model)
        # tags field doesn't exist in MockDBModel, so is excluded
        self.assertNotIn("tags", result)
        # But other fields that exist in DB model are included
        self.assertIn("is_active", result)

    def test_zero_id_included(self) -> None:
        """Test that ID value of 0 is included (it's non-None)."""
        filter_model = MockDataModel(id=0, name="test")
        result = self.repo._extract_filter_conditions(filter_model)
        # All non-None fields are included, including id=0
        # description is None, so it's filtered out
        self.assertIn("id", result)
        self.assertEqual(result["id"], 0)
        self.assertIn("name", result)
        self.assertEqual(result["name"], "test")
        self.assertNotIn("description", result)


class TestApplyTextSearch(unittest.TestCase):
    """Test _apply_text_search private method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create a mock repository instance
        mock_config_getter = Mock(return_value=Mock(database=Mock(get_connection_string=Mock(return_value="sqlite:///:memory:"))))

        with patch('src.repos.base_repository.create_engine'), \
             patch('src.repos.base_repository.sessionmaker'):
            self.repo = ConcreteBaseRepository(
                config_getter=mock_config_getter,
                data_model_class=MockDataModel,
                db_model_class=MockDBModel
            )

    def test_with_explicit_search_fields(self) -> None:
        """Test text search with explicitly provided search fields."""
        # We need to test that the function accesses the correct fields
        # and calls ilike with the right pattern. Since SQLAlchemy's or_
        # requires real expression objects, we'll verify the behavior indirectly

        name_column_accessed = False
        desc_column_accessed = False
        ilike_calls = []

        class TrackedColumn:
            def __init__(self, field_name: str) -> None:
                self.field_name = field_name

            def ilike(self, pattern: str) -> Mock:
                if self.field_name == "name":
                    nonlocal name_column_accessed
                    name_column_accessed = True
                elif self.field_name == "description":
                    nonlocal desc_column_accessed
                    desc_column_accessed = True
                ilike_calls.append((self.field_name, pattern))
                # Return a simple object that will fail in or_() but we can catch it
                return Mock()

        MockDBModel.name = TrackedColumn("name")
        MockDBModel.description = TrackedColumn("description")

        mock_stmt = Mock()

        try:
            self.repo._apply_text_search(
                mock_stmt,
                "search_term",
                search_fields=["name", "description"]
            )
        except Exception:
            # Expected to fail when passed to or_() since we're using Mocks
            pass

        # Verify both columns were accessed and ilike was called correctly
        self.assertTrue(name_column_accessed)
        self.assertTrue(desc_column_accessed)
        self.assertEqual(len(ilike_calls), 2)
        # Verify the pattern has wildcards
        for field_name, pattern in ilike_calls:
            self.assertEqual(pattern, "%search_term%")

    def test_with_no_search_fields_auto_discovers(self) -> None:
        """Test that text search auto-discovers String/Text fields when none provided."""
        ilike_calls = []

        class TrackedColumn:
            def __init__(self, field_name: str) -> None:
                self.field_name = field_name

            def ilike(self, pattern: str) -> Mock:
                ilike_calls.append((self.field_name, pattern))
                return Mock()

        # Create mock columns for the inspector
        mock_name_column = Mock()
        mock_name_column.type = String()
        mock_name_column.name = "name"

        mock_desc_column = Mock()
        mock_desc_column.type = Text()
        mock_desc_column.name = "description"

        mock_id_column = Mock()
        mock_id_column.type = Integer()
        mock_id_column.name = "id"

        # Mock inspector to return columns
        mock_inspector = Mock()
        mock_inspector.columns = [mock_name_column, mock_desc_column, mock_id_column]

        with patch('src.repos.base_repository.inspect', return_value=mock_inspector):
            # Set up MockDBModel columns with tracked columns
            MockDBModel.name = TrackedColumn("name")
            MockDBModel.description = TrackedColumn("description")

            mock_stmt = Mock()

            try:
                self.repo._apply_text_search(
                    mock_stmt,
                    "search_term",
                    search_fields=None
                )
            except Exception:
                # Expected to fail when passed to or_() since we're using Mocks
                pass

            # Verify ilike was called for String and Text columns only (not Integer)
            self.assertEqual(len(ilike_calls), 2)
            field_names = [call[0] for call in ilike_calls]
            self.assertIn("name", field_names)
            self.assertIn("description", field_names)

    def test_with_empty_search_fields_list(self) -> None:
        """Test with empty search fields list returns statement unchanged."""
        mock_stmt = Mock()

        # Mock inspector to return empty columns
        mock_inspector = Mock()
        mock_inspector.columns = []

        with patch('src.repos.base_repository.inspect', return_value=mock_inspector):
            result = self.repo._apply_text_search(
                mock_stmt,
                "search_term",
                search_fields=[]
            )

            # Statement should be returned unchanged (where not called)
            self.assertEqual(result, mock_stmt)

    def test_ilike_pattern_formatting(self) -> None:
        """Test that search term is formatted with % wildcards for ilike."""
        ilike_pattern = None

        class TrackedColumn:
            def ilike(self, pattern: str) -> Mock:
                nonlocal ilike_pattern
                ilike_pattern = pattern
                return Mock()

        MockDBModel.name = TrackedColumn()

        mock_stmt = Mock()

        try:
            self.repo._apply_text_search(
                mock_stmt,
                "test",
                search_fields=["name"]
            )
        except Exception:
            # Expected to fail when passed to or_() since we're using Mocks
            pass

        # Verify ilike was called with %test% pattern
        self.assertEqual(ilike_pattern, "%test%")

    def test_nonexistent_field_skipped(self) -> None:
        """Test that nonexistent fields in search_fields are skipped."""
        mock_stmt = Mock()
        original_where_count = 0

        # Field doesn't exist on MockDBModel
        result = self.repo._apply_text_search(
            mock_stmt,
            "search_term",
            search_fields=["nonexistent_field"]
        )

        # Statement should be returned unchanged since no valid fields
        self.assertEqual(result, mock_stmt)

    def test_inspector_none_returns_unchanged_statement(self) -> None:
        """Test that if inspector is None, statement is returned unchanged."""
        mock_stmt = Mock()

        with patch('src.repos.base_repository.inspect', return_value=None):
            result = self.repo._apply_text_search(
                mock_stmt,
                "search_term",
                search_fields=None
            )

            # Should return statement unchanged
            self.assertEqual(result, mock_stmt)

    def test_inspector_without_columns_returns_unchanged_statement(self) -> None:
        """Test that if inspector has no columns attribute, statement is returned unchanged."""
        mock_stmt = Mock()
        mock_inspector = Mock(spec=[])  # No 'columns' attribute

        with patch('src.repos.base_repository.inspect', return_value=mock_inspector):
            result = self.repo._apply_text_search(
                mock_stmt,
                "search_term",
                search_fields=None
            )

            # Should return statement unchanged
            self.assertEqual(result, mock_stmt)


if __name__ == "__main__":
    unittest.main()
