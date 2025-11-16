"""Ticker history stats repository for database operations."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from src.config.configuration import CONFIG
from src.database.equities.tables.ticker_history_stats import (
    TickerHistoryStats as TickerHistoryStatsDBModel,
)
from src.models.ticker_history_stats import (
    TickerHistoryStats as TickerHistoryStatsDataModel,
)
from src.repos.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class TickerHistoryStatsRepository(
    BaseRepository[TickerHistoryStatsDataModel, TickerHistoryStatsDBModel]
):
    """Repository for ticker history stats database operations."""

    def __init__(self) -> None:
        """Initialize ticker history stats repository."""
        super().__init__(
            config_getter=CONFIG.get_equities_config,
            data_model_class=TickerHistoryStatsDataModel,
            db_model_class=TickerHistoryStatsDBModel,
        )

    def _create_id_filter(self, id: int) -> TickerHistoryStatsDataModel:
        """Create a TickerHistoryStats filter model for ID lookups."""
        return TickerHistoryStatsDataModel(
            ticker_history_id=0,  # Will be ignored
            id=id,  # Will be used as filter
        )

    # Domain-specific methods

    def get_stats_by_ticker_history_id(
        self, ticker_history_id: int
    ) -> TickerHistoryStatsDataModel | None:
        """Get stats for a ticker history.

        Args:
            ticker_history_id: ID of the ticker history

        Returns:
            Stats data model, or None if no stats exist
        """
        try:
            with self._SessionLocal() as session:
                query = select(TickerHistoryStatsDBModel).where(
                    TickerHistoryStatsDBModel.ticker_history_id == ticker_history_id
                )

                result = session.execute(query)
                db_model = result.scalar_one_or_none()

                if db_model:
                    logger.debug(f"Found stats for ticker_history_id={ticker_history_id}")
                    return TickerHistoryStatsDataModel.from_db_model(db_model)
                else:
                    logger.debug(f"No stats found for ticker_history_id={ticker_history_id}")
                    return None

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving stats by ticker history ID: {e}")
            raise

    def upsert_stats(
        self, stats: TickerHistoryStatsDataModel
    ) -> TickerHistoryStatsDataModel:
        """Insert or update ticker history stats.

        Uses PostgreSQL's ON CONFLICT DO UPDATE to handle duplicates.
        If a record with the same ticker_history_id exists, it will be updated.

        Args:
            stats: Stats data model to upsert

        Returns:
            The upserted stats data model with updated timestamps
        """
        try:
            with self._SessionLocal() as session:
                # Convert data model to DB model
                db_model = stats.to_db_model()

                # Prepare values for upsert
                values = {
                    "ticker_history_id": db_model.ticker_history_id,
                    "data_coverage_pct": db_model.data_coverage_pct,
                    "min_price": db_model.min_price,
                    "max_price": db_model.max_price,
                    "average_price": db_model.average_price,
                    "median_price": db_model.median_price,
                }

                # Create upsert statement
                stmt = insert(TickerHistoryStatsDBModel).values(values)

                # On conflict, update all fields except ticker_history_id
                stmt = stmt.on_conflict_do_update(
                    constraint="uq_ticker_history_stats",
                    set_={
                        "data_coverage_pct": stmt.excluded.data_coverage_pct,
                        "min_price": stmt.excluded.min_price,
                        "max_price": stmt.excluded.max_price,
                        "average_price": stmt.excluded.average_price,
                        "median_price": stmt.excluded.median_price,
                    },
                )

                # Execute and return the ID
                stmt = stmt.returning(TickerHistoryStatsDBModel.id)
                result = session.execute(stmt)
                upserted_id = result.scalar_one()
                session.commit()

                logger.info(
                    f"Upserted stats for ticker_history_id={stats.ticker_history_id}, id={upserted_id}"
                )

                # Fetch the complete record to get timestamps
                return self.get_by_id(upserted_id)

        except SQLAlchemyError as e:
            logger.error(f"Database error in upsert_stats: {e}")
            raise

    def delete_stats_by_ticker_history_id(self, ticker_history_id: int) -> bool:
        """Delete stats for a ticker history.

        Args:
            ticker_history_id: ID of the ticker history

        Returns:
            True if stats were deleted, False if no stats existed
        """
        filter_data = TickerHistoryStatsDataModel(
            ticker_history_id=ticker_history_id
        )
        deleted_count = self.delete(filter_data)

        if deleted_count > 0:
            logger.info(f"Deleted stats for ticker_history_id={ticker_history_id}")
            return True
        else:
            logger.debug(f"No stats to delete for ticker_history_id={ticker_history_id}")
            return False
