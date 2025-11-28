"""Rebounds repository for database operations."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.algorithms.high_lows.models.rebound import Rebound as ReboundDataModel
from src.config.configuration import CONFIG
from src.database.algorithms.tables.high_lows.rebounds import Rebound as ReboundDBModel
from src.pipelines.algorithms.base.interfaces import CompletedPatternRepository
from src.repos.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ReboundsRepository(
    BaseRepository[ReboundDataModel, ReboundDBModel],
    CompletedPatternRepository[ReboundDataModel],
):
    """Repository for rebounds pattern database operations.

    Implements both BaseRepository and CompletedPatternRepository interfaces.
    """

    def __init__(self) -> None:
        """Initialize rebounds repository."""
        super().__init__(
            config_getter=CONFIG.get_algorithm_config,
            data_model_class=ReboundDataModel,
            db_model_class=ReboundDBModel,
        )

    @staticmethod
    def from_db_model(db_model: ReboundDBModel) -> ReboundDataModel:
        """Create data model from SQLAlchemy database model.

        Args:
            db_model: SQLAlchemy Rebound instance from database

        Returns:
            Rebound: Data model instance
        """
        from src.database.algorithms.tables.high_lows.rebounds import PRICE_MULTIPLIER

        # Convert threshold from basis points to decimal (2000 -> 0.20)
        threshold = Decimal(db_model.threshold) / Decimal("10000")

        return ReboundDataModel(
            id=db_model.id,
            ticker_history_id=db_model.ticker_history_id,
            threshold=threshold,
            high_start_price=Decimal(db_model.high_start_price) / PRICE_MULTIPLIER,
            high_start_date=db_model.high_start_date,
            low_threshold_price=Decimal(db_model.low_threshold_price)
            / PRICE_MULTIPLIER,
            low_threshold_date=db_model.low_threshold_date,
            lowest_price=Decimal(db_model.lowest_price) / PRICE_MULTIPLIER,
            lowest_date=db_model.lowest_date,
            high_threshold_price=Decimal(db_model.high_threshold_price)
            / PRICE_MULTIPLIER,
            high_threshold_date=db_model.high_threshold_date,
            rebound_price=Decimal(db_model.rebound_price) / PRICE_MULTIPLIER,
            rebound_date=db_model.rebound_date,
            number_of_high_thresholds=db_model.number_of_high_thresholds,
        )

    @staticmethod
    def to_db_model(data_model: ReboundDataModel) -> ReboundDBModel:
        """Convert data model to SQLAlchemy database model.

        Args:
            data_model: Rebound data model instance

        Returns:
            ReboundDBModel: SQLAlchemy model instance ready for database operations
        """
        from src.database.algorithms.tables.high_lows.rebounds import PRICE_MULTIPLIER

        # Convert threshold from decimal to basis points (0.20 -> 2000)
        threshold_bp = int(data_model.threshold * Decimal("10000"))

        db_model = ReboundDBModel(
            ticker_history_id=data_model.ticker_history_id,
            threshold=threshold_bp,
            high_start_price=int(data_model.high_start_price * PRICE_MULTIPLIER),
            high_start_date=data_model.high_start_date,
            low_threshold_price=int(data_model.low_threshold_price * PRICE_MULTIPLIER),
            low_threshold_date=data_model.low_threshold_date,
            lowest_price=int(data_model.lowest_price * PRICE_MULTIPLIER),
            lowest_date=data_model.lowest_date,
            high_threshold_price=int(data_model.high_threshold_price * PRICE_MULTIPLIER),
            high_threshold_date=data_model.high_threshold_date,
            rebound_price=int(data_model.rebound_price * PRICE_MULTIPLIER),
            rebound_date=data_model.rebound_date,
            number_of_high_thresholds=data_model.number_of_high_thresholds,
        )

        if data_model.id is not None:
            db_model.id = data_model.id

        return db_model

    def bulk_insert_rebounds(self, rebounds: list[ReboundDataModel]) -> int:
        """Bulk insert rebound patterns.

        Args:
            rebounds: List of Rebound data models to insert

        Returns:
            Number of records inserted
        """
        if not rebounds:
            return 0

        try:
            with self._SessionLocal() as session:
                db_models = [self.to_db_model(rebound) for rebound in rebounds]
                session.add_all(db_models)
                session.commit()

                logger.info(f"Bulk inserted {len(rebounds)} rebounds")
                return len(rebounds)

        except SQLAlchemyError as e:
            logger.error(f"Database error during bulk insert of rebounds: {e}")
            raise

    # =========================================================================
    # CompletedPatternRepository Interface Implementation
    # =========================================================================

    def bulk_insert(self, patterns: list[ReboundDataModel]) -> int:
        """Bulk insert completed patterns.

        Unified interface method that delegates to bulk_insert_rebounds().

        Args:
            patterns: List of completed patterns to insert

        Returns:
            Count of patterns inserted
        """
        return self.bulk_insert_rebounds(patterns)
