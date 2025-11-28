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

    # TODO I thought this was handeled by the base class?
    def bulk_insert_reversals(self, reversals: list[ReversalDataModel]) -> int:
        """Bulk insert reversal patterns.

        Args:
            reversals: List of Reversal data models to insert

        Returns:
            Number of records inserted
        """
        if not reversals:
            return 0

        try:
            with self._SessionLocal() as session:
                db_models = [reversal.to_db_model() for reversal in reversals]
                session.add_all(db_models)
                session.commit()

                logger.info(f"Bulk inserted {len(reversals)} reversals")
                return len(reversals)

        except SQLAlchemyError as e:
            logger.error(f"Database error during bulk insert of reversals: {e}")
            raise

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
