"""Highs repository for database operations."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from src.config.configuration import CONFIG
from src.database.algorithms.tables.highs import High as HighDBModel
from src.models.high import High as HighDataModel
from src.repos.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class HighsRepository(BaseRepository[HighDataModel, HighDBModel]):
    """Repository for highs pattern database operations."""

    def __init__(self) -> None:
        """Initialize highs repository."""
        super().__init__(
            config_getter=CONFIG.get_algorithm_config,
            data_model_class=HighDataModel,
            db_model_class=HighDBModel,
        )

    def _create_id_filter(self, id: int) -> HighDataModel:
        """Create a High filter model for ID lookups."""
        return HighDataModel(
            ticker_history_id=0,  # Will be ignored
            threshold=Decimal("0"),  # Will be ignored
            low_start_price=Decimal("0"),  # Will be ignored
            low_start_date=date(1900, 1, 1),  # Will be ignored
            last_updated=date(1900, 1, 1),  # Will be ignored
            id=id,  # Will be used as filter
        )

    def get_active_highs_by_ticker(
        self, ticker_history_id: int, threshold: Decimal | None = None
    ) -> list[HighDataModel]:
        """Get all active (non-expired) highs for a ticker.

        Args:
            ticker_history_id: ID of ticker_history record
            threshold: Optional threshold filter (e.g., Decimal("0.20") for 20%)

        Returns:
            List of active High patterns
        """
        try:
            with self._SessionLocal() as session:
                stmt = select(HighDBModel).where(
                    HighDBModel.ticker_history_id == ticker_history_id,
                    HighDBModel.expired == False,  # noqa: E712
                )

                if threshold is not None:
                    # Convert threshold to basis points
                    threshold_bp = int(threshold * Decimal("10000"))
                    stmt = stmt.where(HighDBModel.threshold == threshold_bp)

                result = session.execute(stmt)
                db_models = result.scalars().all()

                return [HighDataModel.from_db_model(db_model) for db_model in db_models]

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving active highs for ticker_history_id {ticker_history_id}: {e}"
            )
            raise

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

    def mark_as_expired(self, high_ids: list[int]) -> int:
        """Mark high patterns as expired.

        Args:
            high_ids: List of high IDs to mark as expired

        Returns:
            Number of records updated
        """
        if not high_ids:
            return 0

        try:
            with self._SessionLocal() as session:
                stmt = (
                    HighDBModel.__table__.update()
                    .where(HighDBModel.id.in_(high_ids))
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

    def get_highs_by_ticker_and_threshold(
        self, ticker_history_id: int, threshold: Decimal
    ) -> list[HighDataModel]:
        """Get all highs for a specific ticker and threshold.

        Args:
            ticker_history_id: ID of ticker_history record
            threshold: Threshold as decimal (e.g., Decimal("0.20") for 20%)

        Returns:
            List of High patterns matching criteria
        """
        try:
            with self._SessionLocal() as session:
                # Convert threshold to basis points
                threshold_bp = int(threshold * Decimal("10000"))

                stmt = select(HighDBModel).where(
                    HighDBModel.ticker_history_id == ticker_history_id,
                    HighDBModel.threshold == threshold_bp,
                )

                result = session.execute(stmt)
                db_models = result.scalars().all()

                return [HighDataModel.from_db_model(db_model) for db_model in db_models]

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving highs for ticker {ticker_history_id}, threshold {threshold}: {e}"
            )
            raise

    def get_highs_updated_before(self, before_date: date) -> list[HighDataModel]:
        """Get all highs last updated before a specific date.

        Useful for finding stale patterns that need reprocessing.

        Args:
            before_date: Date to compare against last_updated

        Returns:
            List of High patterns last updated before the date
        """
        try:
            with self._SessionLocal() as session:
                stmt = select(HighDBModel).where(
                    HighDBModel.last_updated < before_date,
                    HighDBModel.expired == False,  # noqa: E712
                )

                result = session.execute(stmt)
                db_models = result.scalars().all()

                return [HighDataModel.from_db_model(db_model) for db_model in db_models]

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving highs updated before {before_date}: {e}"
            )
            raise
