"""Lows repository for database operations."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from src.algorithms.high_lows.models.low import Low as LowDataModel
from src.config.configuration import CONFIG
from src.database.equities.tables.algorithms.lows import Low as LowDBModel
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
            config_getter=CONFIG.get_equities_config,
            data_model_class=LowDataModel,
            db_model_class=LowDBModel,
        )

    @staticmethod
    def from_db_model(db_model: LowDBModel) -> LowDataModel:
        """Create data model from SQLAlchemy database model.

        Args:
            db_model: SQLAlchemy Low instance from database

        Returns:
            Low: Data model instance
        """
        from src.database.equities.tables.algorithms.lows import PRICE_MULTIPLIER

        # Convert threshold from basis points to decimal (2000 -> 0.20)
        threshold = Decimal(db_model.threshold) / Decimal("10000")

        return LowDataModel(
            id=db_model.id,
            ticker_history_id=db_model.ticker_history_id,
            threshold=threshold,
            high_start_price=Decimal(db_model.high_start_price) / PRICE_MULTIPLIER,
            high_start_date=db_model.high_start_date,
            low_threshold_price=(
                Decimal(db_model.low_threshold_price) / PRICE_MULTIPLIER
                if db_model.low_threshold_price is not None
                else None
            ),
            low_threshold_date=db_model.low_threshold_date,
            lowest_price=(
                Decimal(db_model.lowest_price) / PRICE_MULTIPLIER
                if db_model.lowest_price is not None
                else None
            ),
            lowest_date=db_model.lowest_date,
            high_threshold_price=(
                Decimal(db_model.high_threshold_price) / PRICE_MULTIPLIER
                if db_model.high_threshold_price is not None
                else None
            ),
            high_threshold_date=db_model.high_threshold_date,
            number_of_high_thresholds=db_model.number_of_high_thresholds,
            last_updated=db_model.last_updated,
            spawned=db_model.spawned,
            expired=db_model.expired,
        )

    @staticmethod
    def to_db_model(data_model: LowDataModel) -> LowDBModel:
        """Convert data model to SQLAlchemy database model.

        Args:
            data_model: Low data model instance

        Returns:
            LowDBModel: SQLAlchemy model instance ready for database operations
        """
        from src.database.equities.tables.algorithms.lows import PRICE_MULTIPLIER

        # Convert threshold from decimal to basis points (0.20 -> 2000)
        threshold_bp = int(data_model.threshold * Decimal("10000"))

        db_model = LowDBModel(
            ticker_history_id=data_model.ticker_history_id,
            threshold=threshold_bp,
            high_start_price=int(data_model.high_start_price * PRICE_MULTIPLIER),
            high_start_date=data_model.high_start_date,
            low_threshold_price=(
                int(data_model.low_threshold_price * PRICE_MULTIPLIER)
                if data_model.low_threshold_price is not None
                else None
            ),
            low_threshold_date=data_model.low_threshold_date,
            lowest_price=(
                int(data_model.lowest_price * PRICE_MULTIPLIER)
                if data_model.lowest_price is not None
                else None
            ),
            lowest_date=data_model.lowest_date,
            high_threshold_price=(
                int(data_model.high_threshold_price * PRICE_MULTIPLIER)
                if data_model.high_threshold_price is not None
                else None
            ),
            high_threshold_date=data_model.high_threshold_date,
            number_of_high_thresholds=data_model.number_of_high_thresholds,
            last_updated=data_model.last_updated,
            spawned=data_model.spawned,
            expired=data_model.expired,
        )

        if data_model.id is not None:
            db_model.id = data_model.id

        return db_model

    @staticmethod
    def _update_db_model(data_model: LowDataModel, db_model: LowDBModel) -> None:
        """Update existing SQLAlchemy database model with data from data model.

        Note: Does not update id or ticker_history_id as they are immutable.

        Args:
            data_model: Low data model instance with new values
            db_model: SQLAlchemy Low instance to update
        """
        from src.database.equities.tables.algorithms.lows import PRICE_MULTIPLIER

        # Convert threshold from decimal to basis points
        threshold_bp = int(data_model.threshold * Decimal("10000"))

        db_model.threshold = threshold_bp
        db_model.high_start_price = int(data_model.high_start_price * PRICE_MULTIPLIER)
        db_model.high_start_date = data_model.high_start_date
        db_model.low_threshold_price = (
            int(data_model.low_threshold_price * PRICE_MULTIPLIER)
            if data_model.low_threshold_price is not None
            else None
        )
        db_model.low_threshold_date = data_model.low_threshold_date
        db_model.lowest_price = (
            int(data_model.lowest_price * PRICE_MULTIPLIER)
            if data_model.lowest_price is not None
            else None
        )
        db_model.lowest_date = data_model.lowest_date
        db_model.high_threshold_price = (
            int(data_model.high_threshold_price * PRICE_MULTIPLIER)
            if data_model.high_threshold_price is not None
            else None
        )
        db_model.high_threshold_date = data_model.high_threshold_date
        db_model.number_of_high_thresholds = data_model.number_of_high_thresholds
        db_model.last_updated = data_model.last_updated
        db_model.spawned = data_model.spawned
        db_model.expired = data_model.expired

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

                return [self.from_db_model(db_model) for db_model in db_models]

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
                        db_model = self.to_db_model(low)
                        session.add(db_model)
                        inserted_count += 1
                    else:
                        # Update existing record
                        existing = session.get(LowDBModel, low.id)
                        if existing:
                            self._update_db_model(low, existing)
                            updated_count += 1
                        else:
                            # TODO either we do this or we do not,  we need to make this a standard
                            # and if we do generate the ids, then it should be done by that standard
                            # else we need to not do it at all and throw an error.
                            # ID was set but record doesn't exist, insert anyway
                            db_model = self.to_db_model(low)
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

    def mark_as_expired(self, pattern_ids: list[int]) -> int:
        """Mark low patterns as expired.

        Args:
            low_ids: List of low IDs to mark as expired

        Returns:
            Number of records updated
        """
        if not pattern_ids:
            return 0

        try:
            with self._SessionLocal() as session:
                stmt = (
                    LowDBModel.__table__.update()
                    .where(LowDBModel.id.in_(pattern_ids))
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

    def get_by_ticker_history_id(self, ticker_history_id: int) -> list[LowDataModel]:
        """Get all low patterns for a specific ticker history.

        Args:
            ticker_history_id: The ticker history ID to filter by

        Returns:
            List of Low patterns for the specified ticker history
        """
        try:
            with self._SessionLocal() as session:
                stmt = select(LowDBModel).where(
                    LowDBModel.ticker_history_id == ticker_history_id
                )
                result = session.execute(stmt)
                db_models = result.scalars().all()

                return [self.from_db_model(db_model) for db_model in db_models]

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving lows for ticker_history_id={ticker_history_id}: {e}"
            )
            raise
