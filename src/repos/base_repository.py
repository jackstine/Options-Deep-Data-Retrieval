"""Base repository class providing common CRUD operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, fields
from datetime import date
import logging
from typing import Any, Generic, TypeVar

from sqlalchemy import create_engine, func, inspect, or_, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import String, Text

# Type variables for generic repository
TDataModel = TypeVar("TDataModel")  # Data model type (e.g., Company)
TDBModel = TypeVar("TDBModel")  # SQLAlchemy model type (e.g., CompanyTable)


@dataclass
class QueryOptions:
    """Configuration options for repository queries."""

    limit: int | None = None
    offset: int | None = None
    order_by: str | None = None
    order_desc: bool = False
    include_inactive: bool = False  # For soft-delete support

    # Advanced filtering
    date_range: tuple[date, date] | None = None
    text_search: str | None = None  # For full-text search
    text_search_fields: list[str] = None  # Specify which fields to search
    text_search_operator: str = "ilike"  # 'ilike', 'like', 'match', 'fts'

    # Relationship loading
    load_relationships: bool = False
    relationship_filters: dict[str, Any] | None = None


class BaseRepository(Generic[TDataModel, TDBModel], ABC):
    """Abstract base repository providing common CRUD operations.

    Type Parameters:
        TDataModel: The data model type (e.g., Company, Ticker)
        TDBModel: The corresponding SQLAlchemy model type
    """

    def __init__(self, config_getter: Callable, db_model_class: type[TDBModel]) -> None:
        """Initialize repository with database connection.

        Args:
            config_getter: Function to get database config (e.g., CONFIG.get_equities_config)
            db_model_class: SQLAlchemy model class for this repository
        """
        self._config = config_getter()
        self._engine = create_engine(self._config.database.get_connection_string())
        self._SessionLocal = sessionmaker(bind=self._engine)
        self._db_model_class = db_model_class
        self._logger = logging.getLogger(self.__class__.__name__)

    def _extract_filter_conditions(self, filter_model: TDataModel) -> dict[str, Any]:
        """Extract non-empty values from data model to create filter conditions.

        Args:
            filter_model: Data model instance with filter values

        Returns:
            Dictionary of field_name -> value for non-empty fields
        """
        conditions = {}

        if hasattr(filter_model, "to_dict"):
            model_dict = filter_model.to_dict()
        else:
            # Fallback for dataclasses
            model_dict = {
                field.name: getattr(filter_model, field.name)
                for field in fields(filter_model)
            }

        for field_name, value in model_dict.items():
            if self._is_valid_filter_value(value):
                conditions[field_name] = value

        return conditions

    def _is_valid_filter_value(self, value: Any) -> bool:
        """Check if a value should be used as a filter condition."""
        if value is None:
            return False
        if isinstance(value, str) and value == "":
            return False
        if isinstance(value, (int, float)) and value == 0:
            return False
        if isinstance(value, (list, dict, set)) and len(value) == 0:
            return False
        return True

    def _apply_text_search(
        self, stmt, text_query: str, search_fields: list[str] = None
    ):
        """Apply text search across specified fields."""
        if not search_fields:
            # Default searchable fields based on column types
            search_fields = [
                col.name
                for col in inspect(self._db_model_class).columns
                if isinstance(col.type, (String, Text))
            ]

        search_conditions = []
        for field in search_fields:
            if hasattr(self._db_model_class, field):
                column = getattr(self._db_model_class, field)
                search_conditions.append(column.ilike(f"%{text_query}%"))

        if search_conditions:
            stmt = stmt.where(or_(*search_conditions))

        return stmt

    @abstractmethod
    def _create_id_filter(self, id: int) -> TDataModel:
        """Create a data model filter for ID lookups.
        Must be implemented by concrete repositories.

        Args:
            id: Record ID

        Returns:
            Data model instance with ID set for filtering
        """
        pass

    def get(
        self,
        filter_model: TDataModel | None = None,
        options: QueryOptions | None = None,
    ) -> list[TDataModel]:
        """Get records based on data model filter.

        Args:
            filter_model: Data model with filter values (None = get all)
            options: Query configuration options

        Returns:
            List of data model instances
        """
        options = options or QueryOptions()

        try:
            with self._SessionLocal() as session:
                query = select(self._db_model_class)

                # Apply filters from data model
                if filter_model:
                    conditions = self._extract_filter_conditions(filter_model)
                    for field, value in conditions.items():
                        if hasattr(self._db_model_class, field):
                            query = query.where(
                                getattr(self._db_model_class, field) == value
                            )

                # Apply text search
                if options.text_search:
                    query = self._apply_text_search(
                        query, options.text_search, options.text_search_fields
                    )

                # Apply ordering
                if options.order_by and hasattr(self._db_model_class, options.order_by):
                    order_column = getattr(self._db_model_class, options.order_by)
                    if options.order_desc:
                        query = query.order_by(order_column.desc())
                    else:
                        query = query.order_by(order_column)

                # Apply pagination
                if options.offset:
                    query = query.offset(options.offset)
                if options.limit:
                    query = query.limit(options.limit)

                result = session.execute(query)
                db_models = result.scalars().all()

                # Convert to data models
                data_models = [db_model.to_data_model() for db_model in db_models]

                self._logger.info(f"Retrieved {len(data_models)} records")
                return data_models

        except SQLAlchemyError as e:
            self._logger.error(f"Database error in get(): {e}")
            raise

    def get_one(self, filter_model: TDataModel) -> TDataModel | None:
        """Get single record matching filter."""
        results = self.get(filter_model, QueryOptions(limit=1))
        return results[0] if results else None

    def get_by_id(self, id: int) -> TDataModel | None:
        """Get record by ID."""
        filter_model = self._create_id_filter(id)
        return self.get_one(filter_model)

    def count(self, filter_model: TDataModel | None = None) -> int:
        """Count records matching filter.

        Args:
            filter_model: Data model with filter values (None = count all)

        Returns:
            Number of matching records
        """
        try:
            with self._SessionLocal() as session:
                query = select(func.count()).select_from(self._db_model_class)

                # Apply filters
                if filter_model:
                    conditions = self._extract_filter_conditions(filter_model)
                    for field, value in conditions.items():
                        if hasattr(self._db_model_class, field):
                            query = query.where(
                                getattr(self._db_model_class, field) == value
                            )

                result = session.execute(query)
                count = result.scalar()

                self._logger.debug(f"Count query returned {count} records")
                return count

        except SQLAlchemyError as e:
            self._logger.error(f"Database error in count(): {e}")
            raise

    def insert(self, data_model: TDataModel) -> TDataModel:
        """Insert single record.

        Args:
            data_model: Data model instance to insert

        Returns:
            Data model with populated ID and timestamps
        """
        try:
            with self._SessionLocal() as session:
                db_model = self._db_model_class.from_data_model(data_model)
                session.add(db_model)
                session.commit()
                session.refresh(db_model)

                result = db_model.to_data_model()
                self._logger.info(f"Inserted record with ID {result.id}")
                return result

        except SQLAlchemyError as e:
            self._logger.error(f"Database error in insert(): {e}")
            raise

    def insert_many(self, data_models: list[TDataModel]) -> int:
        """Insert multiple records in bulk.

        Args:
            data_models: List of data model instances to insert

        Returns:
            Number of records successfully inserted
        """
        if not data_models:
            self._logger.info("No records to insert")
            return 0

        try:
            with self._SessionLocal() as session:
                db_models = [
                    self._db_model_class.from_data_model(dm) for dm in data_models
                ]
                session.add_all(db_models)
                session.commit()

                count = len(db_models)
                self._logger.info(f"Bulk inserted {count} records")
                return count

        except SQLAlchemyError as e:
            self._logger.error(f"Database error in insert_many(): {e}")
            raise

    def update(self, filter_model: TDataModel, update_data: TDataModel) -> int:
        """Update records matching filter with new data.

        Args:
            filter_model: Data model specifying which records to update
            update_data: Data model with new values (only non-empty values used)

        Returns:
            Number of records updated
        """
        try:
            with self._SessionLocal() as session:
                # Build base query
                query = update(self._db_model_class)

                # Apply filter conditions
                filter_conditions = self._extract_filter_conditions(filter_model)
                for field, value in filter_conditions.items():
                    if hasattr(self._db_model_class, field):
                        query = query.where(
                            getattr(self._db_model_class, field) == value
                        )

                # Apply update values
                update_values = self._extract_filter_conditions(update_data)
                if not update_values:
                    self._logger.warning("No valid update values provided")
                    return 0

                query = query.values(**update_values)

                result = session.execute(query)
                session.commit()

                updated_count = result.rowcount
                self._logger.info(f"Updated {updated_count} records")
                return updated_count

        except SQLAlchemyError as e:
            self._logger.error(f"Database error in update(): {e}")
            raise

    def update_by_id(self, id: int, update_data: TDataModel) -> bool:
        """Update single record by ID."""
        filter_model = self._create_id_filter(id)
        return self.update(filter_model, update_data) > 0
