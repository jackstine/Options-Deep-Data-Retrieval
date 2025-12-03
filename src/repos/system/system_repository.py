"""System configuration repository for database operations."""

from __future__ import annotations

import logging

from sqlalchemy import and_, create_engine, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from src.config.configuration import CONFIG
from src.database.equities.tables.system import System as SystemDBModel

logger = logging.getLogger(__name__)


class SystemRepository:
    """Repository for system configuration database operations.

    Provides low-level database operations for the system key-value store.
    Use SystemConfig for typed getter/setter operations.
    """

    def __init__(self) -> None:
        """Initialize system repository."""
        config = CONFIG.get_equities_config()
        engine = create_engine(config.database.get_connection_string())
        self._SessionLocal: sessionmaker[Session] = sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )

    def get_value(self, system_name: int, key: int) -> str | None:
        """Get a configuration value for a system and key.

        Args:
            system_name: The system name identifier
            key: The configuration key identifier

        Returns:
            The value if found, None otherwise
        """
        try:
            with self._SessionLocal() as session:
                query = select(SystemDBModel).where(
                    and_(
                        SystemDBModel.system_name == system_name,
                        SystemDBModel.key == key,
                    )
                )

                result = session.execute(query)
                db_model = result.scalar_one_or_none()

                if db_model:
                    logger.debug(f"Found value for system={system_name}, key={key}")
                    return db_model.value
                else:
                    logger.debug(f"No value found for system={system_name}, key={key}")
                    return None

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving system config: {e}")
            raise

    def set_value(self, system_name: int, key: int, value: str) -> None:
        """Set a configuration value (insert or update).

        Args:
            system_name: The system name identifier
            key: The configuration key identifier
            value: The value to store
        """
        try:
            with self._SessionLocal() as session:
                stmt = insert(SystemDBModel).values(
                    system_name=system_name,
                    key=key,
                    value=value,
                )

                stmt = stmt.on_conflict_do_update(
                    constraint="uq_system_name_key",
                    set_={"value": stmt.excluded.value},
                )

                session.execute(stmt)
                session.commit()

                logger.info(f"Set system={system_name}, key={key}, value_length={len(value)}")

        except SQLAlchemyError as e:
            logger.error(f"Database error setting system config: {e}")
            raise

    def get_all_for_system(self, system_name: int) -> dict[int, str]:
        """Get all configuration values for a system.

        Args:
            system_name: The system name identifier

        Returns:
            Dictionary mapping keys to values for the system
        """
        try:
            with self._SessionLocal() as session:
                query = select(SystemDBModel).where(
                    SystemDBModel.system_name == system_name
                )

                result = session.execute(query)
                db_models = result.scalars().all()

                config_dict = {db_model.key: db_model.value for db_model in db_models}

                logger.debug(
                    f"Retrieved {len(config_dict)} config entries for system={system_name}"
                )
                return config_dict

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving all configs for system: {e}")
            raise

    def delete_value(self, system_name: int, key: int) -> bool:
        """Delete a configuration value.

        Args:
            system_name: The system name identifier
            key: The configuration key identifier

        Returns:
            True if a value was deleted, False if no value existed
        """
        try:
            with self._SessionLocal() as session:
                query = select(SystemDBModel).where(
                    and_(
                        SystemDBModel.system_name == system_name,
                        SystemDBModel.key == key,
                    )
                )

                result = session.execute(query)
                db_model = result.scalar_one_or_none()

                if db_model:
                    session.delete(db_model)
                    session.commit()
                    logger.info(f"Deleted system={system_name}, key={key}")
                    return True
                else:
                    logger.debug(f"No value to delete for system={system_name}, key={key}")
                    return False

        except SQLAlchemyError as e:
            logger.error(f"Database error deleting system config: {e}")
            raise
