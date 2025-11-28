"""Highs repository for database operations."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from src.algorithms.low_highs.models.high import High as HighDataModel
from src.config.configuration import CONFIG
from src.database.algorithms.tables.low_highs.highs import High as HighDBModel
from src.pipelines.algorithms.base.interfaces import ActivePatternRepository
from src.repos.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class HighsRepository(
    BaseRepository[HighDataModel, HighDBModel],
    ActivePatternRepository[HighDataModel],
):
    """Repository for highs pattern database operations.

    Implements both BaseRepository and ActivePatternRepository interfaces.
    """

    def __init__(self) -> None:
        """Initialize highs repository."""
        super().__init__(
            config_getter=CONFIG.get_algorithm_config,
            data_model_class=HighDataModel,
            db_model_class=HighDBModel,
        )

    def get_all_active_highs(self) -> list[HighDataModel]:
        """Get all active (non-expired) high patterns.

        Returns:
            List of all active High patterns
        """
        try:
            with self._SessionLocal() as session:
                stmt = select(HighDBModel).where(
                    HighDBModel.expired == False  # noqa: E712
                )
                result = session.execute(stmt)
                db_models = result.scalars().all()

                return [HighDataModel.from_db_model(db_model) for db_model in db_models]

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving all active highs: {e}")
            raise

    def bulk_upsert_highs(self, highs: list[HighDataModel]) -> dict[str, int]:
        """Bulk insert or update high patterns.

        Args:
            highs: List of High data models to upsert

        Returns:
            Dict with counts: {"inserted": int, "updated": int}
        """
        inserted_count = 0
        updated_count = 0

        try:
            with self._SessionLocal() as session:
                for high in highs:
                    if high.id is None:
                        # Insert new record
                        db_model = high.to_db_model()
                        session.add(db_model)
                        inserted_count += 1
                    else:
                        # Update existing record
                        existing = session.get(HighDBModel, high.id)
                        if existing:
                            high.update_db_model(existing)
                            updated_count += 1
                        else:
                            # TODO either we do this or we do not,  we need to make this a standard
                            # and if we do generate the ids, then it should be done by that standard
                            # else we need to not do it at all and throw an error.
                            # ID was set but record doesn't exist, insert anyway
                            db_model = high.to_db_model()
                            session.add(db_model)
                            inserted_count += 1

                session.commit()
                logger.info(
                    f"Bulk upserted {len(highs)} highs: {inserted_count} inserted, {updated_count} updated"
                )

        except SQLAlchemyError as e:
            logger.error(f"Database error during bulk upsert: {e}")
            raise

        return {"inserted": inserted_count, "updated": updated_count}

    def delete_highs_by_ids(self, high_ids: list[int]) -> int:
        """Delete high patterns by their IDs.

        Args:
            high_ids: List of high IDs to delete

        Returns:
            Number of records deleted
        """
        if not high_ids:
            return 0

        try:
            with self._SessionLocal() as session:
                stmt = delete(HighDBModel).where(HighDBModel.id.in_(high_ids))
                result = session.execute(stmt)
                session.commit()

                deleted_count: int = getattr(result, "rowcount", 0) or 0
                logger.info(f"Deleted {deleted_count} high patterns")
                return deleted_count

        except SQLAlchemyError as e:
            logger.error(f"Database error deleting highs: {e}")
            raise

    def mark_as_expired(self, pattern_ids: list[int]) -> int:
        """Mark high patterns as expired.

        Args:
            high_ids: List of high IDs to mark as expired

        Returns:
            Number of records updated
        """
        if not pattern_ids:
            return 0

        try:
            with self._SessionLocal() as session:
                stmt = (
                    HighDBModel.__table__.update()
                    .where(HighDBModel.id.in_(pattern_ids))
                    .values(expired=True)
                )
                result = session.execute(stmt)
                session.commit()

                updated_count: int = getattr(result, "rowcount", 0) or 0
                logger.info(f"Marked {updated_count} highs as expired")
                return updated_count

        except SQLAlchemyError as e:
            logger.error(f"Database error marking highs as expired: {e}")
            raise

    # =========================================================================
    # ActivePatternRepository Interface Implementation
    # =========================================================================

    def get_all_active(self) -> list[HighDataModel]:
        """Get all non-expired active patterns.

        Unified interface method that delegates to get_all_active_highs().

        Returns:
            List of all active High patterns
        """
        return self.get_all_active_highs()

    def bulk_upsert(self, patterns: list[HighDataModel]) -> dict[str, int]:
        """Insert or update multiple patterns.

        Unified interface method that delegates to bulk_upsert_highs().

        Args:
            patterns: List of patterns to upsert

        Returns:
            Dict with 'inserted' and 'updated' counts
        """
        return self.bulk_upsert_highs(patterns)

    def delete_by_ids(self, pattern_ids: list[int]) -> int:
        """Delete patterns by their IDs.

        Unified interface method that delegates to delete_highs_by_ids().

        Args:
            pattern_ids: List of pattern IDs to delete

        Returns:
            Count of patterns deleted
        """
        return self.delete_highs_by_ids(pattern_ids)
