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

    @staticmethod
    def from_db_model(db_model: TickerHistoryStatsDBModel) -> TickerHistoryStatsDataModel:
        """Create data model from SQLAlchemy database model.

        Args:
            db_model: SQLAlchemy TickerHistoryStats instance from database

        Returns:
            TickerHistoryStats: Data model instance
        """
        from src.database.equities.tables.ticker_history_stats import PRICE_MULTIPLIER
        from decimal import Decimal

        return TickerHistoryStatsDataModel(
            id=db_model.id,
            ticker_history_id=db_model.ticker_history_id,
            data_coverage_pct=db_model.data_coverage_pct,
            min_price=Decimal(db_model.min_price) / PRICE_MULTIPLIER if db_model.min_price is not None else None,
            max_price=Decimal(db_model.max_price) / PRICE_MULTIPLIER if db_model.max_price is not None else None,
            average_price=Decimal(db_model.average_price) / PRICE_MULTIPLIER if db_model.average_price is not None else None,
            median_price=Decimal(db_model.median_price) / PRICE_MULTIPLIER if db_model.median_price is not None else None,
            has_insufficient_coverage=db_model.has_insufficient_coverage,
            low_suspicious_price=db_model.low_suspicious_price,
            high_suspicious_price=db_model.high_suspicious_price,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
        )

    @staticmethod
    def to_db_model(data_model: TickerHistoryStatsDataModel) -> TickerHistoryStatsDBModel:
        """Convert data model to SQLAlchemy database model.

        Returns:
            DBTickerHistoryStats: SQLAlchemy model instance ready for database operations
        """
        from src.database.equities.tables.ticker_history_stats import PRICE_MULTIPLIER

        return TickerHistoryStatsDBModel(
            id=data_model.id,
            ticker_history_id=data_model.ticker_history_id,
            data_coverage_pct=data_model.data_coverage_pct,
            min_price=int(data_model.min_price * PRICE_MULTIPLIER) if data_model.min_price is not None else None,
            max_price=int(data_model.max_price * PRICE_MULTIPLIER) if data_model.max_price is not None else None,
            average_price=int(data_model.average_price * PRICE_MULTIPLIER) if data_model.average_price is not None else None,
            median_price=int(data_model.median_price * PRICE_MULTIPLIER) if data_model.median_price is not None else None,
            has_insufficient_coverage=data_model.has_insufficient_coverage,
            low_suspicious_price=data_model.low_suspicious_price,
            high_suspicious_price=data_model.high_suspicious_price,
        )

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
                db_model = self.to_db_model(stats)

                # Prepare values for upsert
                values = {
                    "ticker_history_id": db_model.ticker_history_id,
                    "data_coverage_pct": db_model.data_coverage_pct,
                    "min_price": db_model.min_price,
                    "max_price": db_model.max_price,
                    "average_price": db_model.average_price,
                    "median_price": db_model.median_price,
                    "has_insufficient_coverage": db_model.has_insufficient_coverage,
                    "low_suspicious_price": db_model.low_suspicious_price,
                    "high_suspicious_price": db_model.high_suspicious_price,
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
                        "has_insufficient_coverage": stmt.excluded.has_insufficient_coverage,
                        "low_suspicious_price": stmt.excluded.low_suspicious_price,
                        "high_suspicious_price": stmt.excluded.high_suspicious_price,
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
