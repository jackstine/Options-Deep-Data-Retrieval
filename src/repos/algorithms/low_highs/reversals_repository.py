"""Reversals repository for database operations."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.algorithms.low_highs.models.reversal import Reversal as ReversalDataModel
from src.config.configuration import CONFIG
from src.database.algorithms.tables.low_highs.reversals import Reversal as ReversalDBModel
from src.pipelines.algorithms.base.interfaces import CompletedPatternRepository
from src.repos.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ReversalsRepository(
    BaseRepository[ReversalDataModel, ReversalDBModel],
    CompletedPatternRepository[ReversalDataModel],
):
    """Repository for reversals pattern database operations.

    Implements both BaseRepository and CompletedPatternRepository interfaces.
    """

    def __init__(self) -> None:
        """Initialize reversals repository."""
        super().__init__(
            config_getter=CONFIG.get_algorithm_config,
            data_model_class=ReversalDataModel,
            db_model_class=ReversalDBModel,
        )

    @staticmethod
    def from_db_model(db_model: ReversalDBModel) -> ReversalDataModel:
        """Create data model from SQLAlchemy database model.

        Args:
            db_model: SQLAlchemy Reversal instance from database

        Returns:
            Reversal: Data model instance
        """
        from src.database.algorithms.tables.low_highs.reversals import PRICE_MULTIPLIER

        # Convert threshold from basis points to decimal (2000 -> 0.20)
        threshold = Decimal(db_model.threshold) / Decimal("10000")

        return ReversalDataModel(
            id=db_model.id,
            ticker_history_id=db_model.ticker_history_id,
            threshold=threshold,
            low_start_price=Decimal(db_model.low_start_price) / PRICE_MULTIPLIER,
            low_start_date=db_model.low_start_date,
            high_threshold_price=Decimal(db_model.high_threshold_price)
            / PRICE_MULTIPLIER,
            high_threshold_date=db_model.high_threshold_date,
            highest_price=Decimal(db_model.highest_price) / PRICE_MULTIPLIER,
            highest_date=db_model.highest_date,
            low_threshold_price=Decimal(db_model.low_threshold_price)
            / PRICE_MULTIPLIER,
            low_threshold_date=db_model.low_threshold_date,
            reversal_price=Decimal(db_model.reversal_price) / PRICE_MULTIPLIER,
            reversal_date=db_model.reversal_date,
            number_of_low_thresholds=db_model.number_of_low_thresholds,
        )

    @staticmethod
    def to_db_model(data_model: ReversalDataModel) -> ReversalDBModel:
        """Convert data model to SQLAlchemy database model.

        Args:
            data_model: Reversal data model instance

        Returns:
            ReversalDBModel: SQLAlchemy model instance ready for database operations
        """
        from src.database.algorithms.tables.low_highs.reversals import PRICE_MULTIPLIER

        # Convert threshold from decimal to basis points (0.20 -> 2000)
        threshold_bp = int(data_model.threshold * Decimal("10000"))

        db_model = ReversalDBModel(
            ticker_history_id=data_model.ticker_history_id,
            threshold=threshold_bp,
            low_start_price=int(data_model.low_start_price * PRICE_MULTIPLIER),
            low_start_date=data_model.low_start_date,
            high_threshold_price=int(data_model.high_threshold_price * PRICE_MULTIPLIER),
            high_threshold_date=data_model.high_threshold_date,
            highest_price=int(data_model.highest_price * PRICE_MULTIPLIER),
            highest_date=data_model.highest_date,
            low_threshold_price=int(data_model.low_threshold_price * PRICE_MULTIPLIER),
            low_threshold_date=data_model.low_threshold_date,
            reversal_price=int(data_model.reversal_price * PRICE_MULTIPLIER),
            reversal_date=data_model.reversal_date,
            number_of_low_thresholds=data_model.number_of_low_thresholds,
        )

        if data_model.id is not None:
            db_model.id = data_model.id

        return db_model

    def bulk_insert_reversals(self, reversals: list[ReversalDataModel]) -> int:
        """Bulk insert reversal patterns using base repository.

        Args:
            reversals: List of Reversal data models to insert

        Returns:
            Number of records inserted
        """
        return self.insert_many(reversals)

    # =========================================================================
    # CompletedPatternRepository Interface Implementation
    # =========================================================================

    def bulk_insert(self, patterns: list[ReversalDataModel]) -> int:
        """Bulk insert completed patterns.

        Unified interface method that delegates to bulk_insert_reversals().

        Args:
            patterns: List of completed patterns to insert

        Returns:
            Count of patterns inserted
        """
        return self.bulk_insert_reversals(patterns)
