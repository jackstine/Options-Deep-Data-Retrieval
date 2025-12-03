"""Base repository class providing common CRUD operations."""

from __future__ import annotations

import logging
from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, fields
from datetime import date
from typing import Any, Generic, Protocol, TypeVar

from sqlalchemy import create_engine, func, inspect, or_, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import String, Text


# Protocols for type safety
class DataModelProtocol(Protocol):
    """Protocol for data model classes."""
    def to_dict(self) -> dict[str, Any]: ...

class DBModelProtocol(Protocol):
    """Protocol for SQLAlchemy model classes."""
    id: int  # All DB models have an id field

# Type variables for generic repository
TDataModel = TypeVar("TDataModel", bound=DataModelProtocol)  # Data model type (e.g., Company)
TDBModel = TypeVar("TDBModel", bound=DBModelProtocol)  # SQLAlchemy model type (e.g., CompanyTable)


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
    text_search_fields: list[str] | None = None  # Specify which fields to search
    text_search_operator: str | None = None  # 'ilike', 'like', 'match', 'fts'

    # Relationship loading
    load_relationships: bool | None = None
    relationship_filters: dict[str, Any] | None = None


class BaseRepository(Generic[TDataModel, TDBModel]):
    """Base repository providing common CRUD operations.

    Type Parameters:
        TDataModel: The data model type (e.g., Company, Ticker)
        TDBModel: The corresponding SQLAlchemy model type
    """

    def __init__(
        self,
        config_getter: Callable,
        data_model_class: type[TDataModel],
        db_model_class: type[TDBModel],
    ) -> None:
        """Initialize repository with database connection.

        Args:
            config_getter: Function to get database config (e.g., CONFIG.get_equities_config)
            data_model_class: Data model class for this repository
            db_model_class: SQLAlchemy model class for this repository
        """
        import os  # noqa: F401

        self._config = config_getter()
        connection_string = self._config.database.get_connection_string()

        # Check if we need Unix socket connection during Docker initialization
        if os.getenv("DOCKER_INIT") == "true":
            # Use connect_args to specify Unix socket host
            self._engine = create_engine(
                connection_string, connect_args={"host": "/var/run/postgresql"}
            )
        else:
            # Normal TCP connection
            self._engine = create_engine(connection_string)

        self._SessionLocal = sessionmaker(bind=self._engine)
        self._data_model_class = data_model_class
        self._db_model_class = db_model_class
        self._logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    @abstractmethod
    def from_db_model(db_model: TDBModel) -> TDataModel:
        """Convert SQLAlchemy DB model to data model.

        Args:
            db_model: SQLAlchemy model instance

        Returns:
            Data model instance

        Note:
            Subclasses must implement this method to handle model-specific conversions.
        """
        raise NotImplementedError("Subclasses must implement from_db_model()")

    @staticmethod
    @abstractmethod
    def to_db_model(data_model: TDataModel) -> TDBModel:
        """Convert data model to SQLAlchemy DB model.

        Args:
            data_model: Data model instance

        Returns:
            SQLAlchemy model instance

        Note:
            Subclasses must implement this method to handle model-specific conversions.
        """
        raise NotImplementedError("Subclasses must implement to_db_model()")

    def _model_to_dict(self, model: TDataModel) -> dict[str, Any]:
        """Convert data model to dictionary.

        Args:
            model: Data model instance

        Returns:
            Dictionary of field_name -> value
        """
        if hasattr(model, "to_dict"):
            return model.to_dict()
        else:
            # Fallback for dataclasses
            return {
                field.name: getattr(model, field.name)
                for field in fields(model)  # type: ignore[arg-type]
            }

    def _extract_valid_db_fields(self, model_dict: dict[str, Any]) -> dict[str, Any]:
        """Extract fields that exist in DB model and have non-None values.

        Args:
            model_dict: Dictionary of field_name -> value

        Returns:
            Dictionary of valid field_name -> value pairs
        """
        return {
            field_name: value
            for field_name, value in model_dict.items()
            if hasattr(self._db_model_class, field_name) and value is not None
        }

    def _extract_filter_conditions(self, filter_model: TDataModel) -> dict[str, Any]:
        """Extract non-None values from data model to create filter conditions.

        Args:
            filter_model: Data model instance with filter values

        Returns:
            Dictionary of field_name -> value for non-None fields that exist in DB
        """
        model_dict = self._model_to_dict(filter_model)
        return self._extract_valid_db_fields(model_dict)

    def _extract_update_values(self, update_data: TDataModel) -> dict[str, Any]:
        """Extract non-None values from data model to create update values.

        Args:
            update_data: Data model instance with update values

        Returns:
            Dictionary of field_name -> value for non-None fields that exist in DB
        """
        model_dict = self._model_to_dict(update_data)
        return self._extract_valid_db_fields(model_dict)

    def _apply_text_search(
        self, stmt: Any, text_query: str, search_fields: list[str] | None = None
    ) -> Any:
        """Apply text search across specified fields."""
        if not search_fields:
            # Default searchable fields based on column types
            inspector = inspect(self._db_model_class)
            if inspector is not None and hasattr(inspector, 'columns'):
                search_fields = [
                    col.name
                    for col in inspector.columns
                    if isinstance(col.type, (String, Text))
                ]
            else:
                search_fields = []

        search_conditions = []
        for field in search_fields:
            if hasattr(self._db_model_class, field):
                column = getattr(self._db_model_class, field)
                search_conditions.append(column.ilike(f"%{text_query}%"))

        if search_conditions:
            stmt = stmt.where(or_(*search_conditions))

        return stmt

    def _apply_filter_conditions(self, query: Any, filter_model: TDataModel | None) -> Any:
        """Apply filter conditions from data model to query.

        Args:
            query: SQLAlchemy query/statement
            filter_model: Data model with filter values (None = no filters)

        Returns:
            Query with filter conditions applied
        """
        if filter_model:
            conditions = self._extract_filter_conditions(filter_model)
            for field, value in conditions.items():
                if hasattr(self._db_model_class, field):
                    query = query.where(
                        getattr(self._db_model_class, field) == value
                    )
        return query

    def _convert_to_data_model(self, db_model: TDBModel) -> TDataModel:
        """Convert single DB model to data model.

        Args:
            db_model: SQLAlchemy model instance

        Returns:
            Data model instance
        """
        return self.__class__.from_db_model(db_model)  # type: ignore[return-value]

    def _convert_to_data_models(self, db_models: list[TDBModel]) -> list[TDataModel]:
        """Convert list of DB models to data models.

        Args:
            db_models: List of SQLAlchemy model instances

        Returns:
            List of data model instances
        """
        return [
            self.__class__.from_db_model(db_model)  # type: ignore[misc]
            for db_model in db_models
        ]

    def get_filter(
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
                query = self._apply_filter_conditions(query, filter_model)

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

                # Convert to data models using data model's from_db_model()
                data_models = self._convert_to_data_models(db_models)

                self._logger.info(f"Retrieved {len(data_models)} records")
                return data_models

        except SQLAlchemyError as e:
            self._logger.error(f"Database error in get_filter(): {e}")
            raise

    def get_all(self, options: QueryOptions | None = None) -> list[TDataModel]:
        """Get all records.

        Args:
            options: Query configuration options (pagination, ordering, etc.)

        Returns:
            List of all data model instances
        """
        return self.get_filter(filter_model=None, options=options)

    def get_one(self, filter_model: TDataModel) -> TDataModel | None:
        """Get single record matching filter."""
        results = self.get_filter(filter_model, QueryOptions(limit=1))
        return results[0] if results else None

    def get_by_id(self, id: int) -> TDataModel | None:
        """Get record by ID."""
        try:
            with self._SessionLocal() as session:
                query = select(self._db_model_class).where(
                    self._db_model_class.id == id  # type: ignore[arg-type]
                )
                result = session.execute(query)
                db_model = result.scalar_one_or_none()

                if db_model:
                    return self._convert_to_data_model(db_model)
                return None
        except SQLAlchemyError as e:
            self._logger.error(f"Database error in get_by_id(): {e}")
            raise

    def get_limit_offset(
        self,
        limit: int,
        offset: int,
        filter_model: TDataModel | None = None,
    ) -> list[TDataModel]:
        """Get records with pagination using limit and offset.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            filter_model: Optional data model with filter values

        Returns:
            List of data model instances
        """
        options = QueryOptions(limit=limit, offset=offset)
        return self.get_filter(filter_model, options)

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
                query = self._apply_filter_conditions(query, filter_model)

                result = session.execute(query)
                count = result.scalar()

                self._logger.debug(f"Count query returned {count} records")
                return count or 0

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
                # Convert data model to database model using repository's to_db_model()
                db_model = self.__class__.to_db_model(data_model)  # type: ignore[arg-type]
                session.add(db_model)
                session.commit()
                session.refresh(db_model)

                # Convert back using repository's from_db_model()
                result = self._convert_to_data_model(db_model)
                self._logger.info(f"Inserted record with ID {result.id}")
                return result  # type: ignore[no-any-return]

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
                # Convert data models to database models using repository's to_db_model()
                db_models = [self.__class__.to_db_model(dm) for dm in data_models]  # type: ignore[arg-type, misc]
                session.add_all(db_models)
                session.commit()

                count = len(db_models)
                self._logger.info(f"Bulk inserted {count} records")
                return count

        except SQLAlchemyError as e:
            self._logger.error(f"Database error in insert_many(): {e}")
            raise

    def insert_many_returning(self, data_models: list[TDataModel]) -> list[TDataModel]:
        """Insert multiple records in bulk and return them with populated IDs.

        Args:
            data_models: List of data model instances to insert

        Returns:
            List of data models with populated IDs and timestamps
        """
        if not data_models:
            self._logger.info("No records to insert")
            return []

        try:
            with self._SessionLocal() as session:
                # Convert data models to database models using repository's to_db_model()
                db_models = [self.__class__.to_db_model(dm) for dm in data_models]  # type: ignore[arg-type, misc]
                session.add_all(db_models)
                session.flush()  # Flush to get IDs without committing

                # Refresh each model to populate IDs and timestamps
                for db_model in db_models:
                    session.refresh(db_model)

                session.commit()

                # Convert back to data models using repository's from_db_model()
                result_models = self._convert_to_data_models(db_models)

                self._logger.info(f"Bulk inserted {len(result_models)} records with IDs")
                return result_models

        except SQLAlchemyError as e:
            self._logger.error(f"Database error in insert_many_returning(): {e}")
            raise

    def update_filter(self, filter_model: TDataModel, update_data: TDataModel) -> int:
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
                update_values = self._extract_update_values(update_data)
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
            self._logger.error(f"Database error in update_filter(): {e}")
            raise

    def update_by_id(self, id: int, update_data: TDataModel) -> bool:
        """Update single record by ID."""
        try:
            with self._SessionLocal() as session:
                # Build update query
                query = update(self._db_model_class).where(
                    self._db_model_class.id == id  # type: ignore[arg-type]
                )

                # Apply update values
                update_values = self._extract_update_values(update_data)
                if not update_values:
                    self._logger.warning("No valid update values provided")
                    return False

                query = query.values(**update_values)
                result = session.execute(query)
                session.commit()

                updated = result.rowcount > 0
                if updated:
                    self._logger.info(f"Updated record with ID {id}")
                return updated
        except SQLAlchemyError as e:
            self._logger.error(f"Database error in update_by_id(): {e}")
            raise

    def delete_filter(self, filter_model: TDataModel) -> int:
        """Delete records matching filter.

        Args:
            filter_model: Data model specifying which records to delete

        Returns:
            Number of records deleted
        """
        try:
            with self._SessionLocal() as session:
                # Build base query
                query = select(self._db_model_class)

                # Apply filter conditions
                query = self._apply_filter_conditions(query, filter_model)

                # Get the records to delete
                result = session.execute(query)
                records_to_delete = result.scalars().all()

                # Delete them
                for record in records_to_delete:
                    session.delete(record)

                session.commit()

                deleted_count = len(records_to_delete)
                self._logger.info(f"Deleted {deleted_count} records")
                return deleted_count

        except SQLAlchemyError as e:
            self._logger.error(f"Database error in delete_filter(): {e}")
            raise

    def delete_by_id(self, id: int) -> bool:
        """Delete single record by ID."""
        try:
            with self._SessionLocal() as session:
                query = select(self._db_model_class).where(
                    self._db_model_class.id == id  # type: ignore[arg-type]
                )
                result = session.execute(query)
                record = result.scalar_one_or_none()

                if record:
                    session.delete(record)
                    session.commit()
                    self._logger.info(f"Deleted record with ID {id}")
                    return True
                return False
        except SQLAlchemyError as e:
            self._logger.error(f"Database error in delete_by_id(): {e}")
            raise
