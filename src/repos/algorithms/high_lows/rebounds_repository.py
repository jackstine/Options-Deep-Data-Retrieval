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
                db_models = [rebound.to_db_model() for rebound in rebounds]
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
