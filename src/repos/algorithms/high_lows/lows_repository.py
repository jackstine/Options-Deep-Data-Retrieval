"""Lows repository for database operations."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from src.algorithms.high_lows.models.low import Low as LowDataModel
from src.config.configuration import CONFIG
from src.database.algorithms.tables.high_lows.lows import Low as LowDBModel
from src.pipelines.algorithms.base.interfaces import ActivePatternRepository
from src.repos.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class LowsRepository(
    BaseRepository[LowDataModel, LowDBModel],
    ActivePatternRepository[LowDataModel],
):
    """Repository for lows pattern database operations.

    Implements both BaseRepository and ActivePatternRepository interfaces.
    """

    def __init__(self) -> None:
        """Initialize lows repository."""
        super().__init__(
            config_getter=CONFIG.get_algorithm_config,
            data_model_class=LowDataModel,
            db_model_class=LowDBModel,
        )

    def _create_id_filter(self, id: int) -> LowDataModel:
        """Create a Low filter model for ID lookups."""
        return LowDataModel(
            ticker_history_id=0,  # Will be ignored
            threshold=Decimal("0"),  # Will be ignored
            high_start_price=Decimal("0"),  # Will be ignored
            high_start_date=date(1900, 1, 1),  # Will be ignored
            last_updated=date(1900, 1, 1),  # Will be ignored
            id=id,  # Will be used as filter
        )

    def get_active_lows_by_ticker(
        self, ticker_history_id: int, threshold: Decimal | None = None
    ) -> list[LowDataModel]:
        """Get all active (non-expired) lows for a ticker.

        Args:
            ticker_history_id: ID of ticker_history record
            threshold: Optional threshold filter (e.g., Decimal("0.20") for 20%)

        Returns:
            List of active Low patterns
        """
        try:
            with self._SessionLocal() as session:
                stmt = select(LowDBModel).where(
                    LowDBModel.ticker_history_id == ticker_history_id,
                    LowDBModel.expired == False,  # noqa: E712
                )

                if threshold is not None:
                    # Convert threshold to basis points
                    threshold_bp = int(threshold * Decimal("10000"))
                    stmt = stmt.where(LowDBModel.threshold == threshold_bp)

                result = session.execute(stmt)
                db_models = result.scalars().all()

                return [LowDataModel.from_db_model(db_model) for db_model in db_models]

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving active lows for ticker_history_id {ticker_history_id}: {e}"
            )
            raise

    def get_all_active_lows(self) -> list[LowDataModel]:
        """Get all active (non-expired) low patterns.

        Returns:
            List of all active Low patterns
        """
        try:
            with self._SessionLocal() as session:
                stmt = select(LowDBModel).where(
                    LowDBModel.expired == False  # noqa: E712
                )
                result = session.execute(stmt)
                db_models = result.scalars().all()

                return [LowDataModel.from_db_model(db_model) for db_model in db_models]

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving all active lows: {e}")
            raise

    def bulk_upsert_lows(self, lows: list[LowDataModel]) -> dict[str, int]:
        """Bulk insert or update low patterns.

        Args:
            lows: List of Low data models to upsert

        Returns:
            Dict with counts: {"inserted": int, "updated": int}
        """
        inserted_count = 0
        updated_count = 0

        try:
            with self._SessionLocal() as session:
                for low in lows:
                    if low.id is None:
                        # Insert new record
                        db_model = low.to_db_model()
                        session.add(db_model)
                        inserted_count += 1
                    else:
                        # Update existing record
                        existing = session.get(LowDBModel, low.id)
                        if existing:
                            low.update_db_model(existing)
                            updated_count += 1
                        else:
                            # TODO either we do this or we do not,  we need to make this a standard
                            # and if we do generate the ids, then it should be done by that standard
                            # else we need to not do it at all and throw an error.
                            # ID was set but record doesn't exist, insert anyway
                            db_model = low.to_db_model()
                            session.add(db_model)
                            inserted_count += 1

                session.commit()
                logger.info(
                    f"Bulk upserted {len(lows)} lows: {inserted_count} inserted, {updated_count} updated"
                )

        except SQLAlchemyError as e:
            logger.error(f"Database error during bulk upsert: {e}")
            raise

        return {"inserted": inserted_count, "updated": updated_count}

    def delete_lows_by_ids(self, low_ids: list[int]) -> int:
        """Delete low patterns by their IDs.

        Args:
            low_ids: List of low IDs to delete

        Returns:
            Number of records deleted
        """
        if not low_ids:
            return 0

        try:
            with self._SessionLocal() as session:
                stmt = delete(LowDBModel).where(LowDBModel.id.in_(low_ids))
                result = session.execute(stmt)
                session.commit()

                deleted_count: int = getattr(result, "rowcount", 0) or 0
                logger.info(f"Deleted {deleted_count} low patterns")
                return deleted_count

        except SQLAlchemyError as e:
            logger.error(f"Database error deleting lows: {e}")
            raise

    def mark_as_expired(self, low_ids: list[int]) -> int:
        """Mark low patterns as expired.

        Args:
            low_ids: List of low IDs to mark as expired

        Returns:
            Number of records updated
        """
        if not low_ids:
            return 0

        try:
            with self._SessionLocal() as session:
                stmt = (
                    LowDBModel.__table__.update()
                    .where(LowDBModel.id.in_(low_ids))
                    .values(expired=True)
                )
                result = session.execute(stmt)
                session.commit()

                updated_count: int = getattr(result, "rowcount", 0) or 0
                logger.info(f"Marked {updated_count} lows as expired")
                return updated_count

        except SQLAlchemyError as e:
            logger.error(f"Database error marking lows as expired: {e}")
            raise

    def get_lows_by_ticker_and_threshold(
        self, ticker_history_id: int, threshold: Decimal
    ) -> list[LowDataModel]:
        """Get all lows for a specific ticker and threshold.

        Args:
            ticker_history_id: ID of ticker_history record
            threshold: Threshold as decimal (e.g., Decimal("0.20") for 20%)

        Returns:
            List of Low patterns matching criteria
        """
        try:
            with self._SessionLocal() as session:
                # Convert threshold to basis points
                threshold_bp = int(threshold * Decimal("10000"))

                stmt = select(LowDBModel).where(
                    LowDBModel.ticker_history_id == ticker_history_id,
                    LowDBModel.threshold == threshold_bp,
                )

                result = session.execute(stmt)
                db_models = result.scalars().all()

                return [LowDataModel.from_db_model(db_model) for db_model in db_models]

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving lows for ticker {ticker_history_id}, threshold {threshold}: {e}"
            )
            raise

    def get_lows_updated_before(self, before_date: date) -> list[LowDataModel]:
        """Get all lows last updated before a specific date.

        Useful for finding stale patterns that need reprocessing.

        Args:
            before_date: Date to compare against last_updated

        Returns:
            List of Low patterns last updated before the date
        """
        try:
            with self._SessionLocal() as session:
                stmt = select(LowDBModel).where(
                    LowDBModel.last_updated < before_date,
                    LowDBModel.expired == False,  # noqa: E712
                )

                result = session.execute(stmt)
                db_models = result.scalars().all()

                return [LowDataModel.from_db_model(db_model) for db_model in db_models]

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving lows updated before {before_date}: {e}"
            )
            raise

    # =========================================================================
    # ActivePatternRepository Interface Implementation
    # =========================================================================

    def get_all_active(self) -> list[LowDataModel]:
        """Get all non-expired active patterns.

        Unified interface method that delegates to get_all_active_lows().

        Returns:
            List of all active Low patterns
        """
        return self.get_all_active_lows()

    def bulk_upsert(self, patterns: list[LowDataModel]) -> dict[str, int]:
        """Insert or update multiple patterns.

        Unified interface method that delegates to bulk_upsert_lows().

        Args:
            patterns: List of patterns to upsert

        Returns:
            Dict with 'inserted' and 'updated' counts
        """
        return self.bulk_upsert_lows(patterns)

    def delete_by_ids(self, pattern_ids: list[int]) -> int:
        """Delete patterns by their IDs.

        Unified interface method that delegates to delete_lows_by_ids().

        Args:
            pattern_ids: List of pattern IDs to delete

        Returns:
            Count of patterns deleted
        """
        return self.delete_lows_by_ids(pattern_ids)
