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

    def _create_id_filter(self, id: int) -> ReboundDataModel:
        """Create a Rebound filter model for ID lookups."""
        return ReboundDataModel(
            ticker_history_id=0,  # Will be ignored
            threshold=Decimal("0"),  # Will be ignored
            high_start_price=Decimal("0"),  # Will be ignored
            high_start_date=date(1900, 1, 1),  # Will be ignored
            low_threshold_price=Decimal("0"),  # Will be ignored
            low_threshold_date=date(1900, 1, 1),  # Will be ignored
            lowest_price=Decimal("0"),  # Will be ignored
            lowest_date=date(1900, 1, 1),  # Will be ignored
            high_threshold_price=Decimal("0"),  # Will be ignored
            high_threshold_date=date(1900, 1, 1),  # Will be ignored
            rebound_price=Decimal("0"),  # Will be ignored
            rebound_date=date(1900, 1, 1),  # Will be ignored
            id=id,  # Will be used as filter
        )

    # TODO I thought this was handeled by the base class?
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

    def get_rebounds_by_ticker(
        self, ticker_history_id: int, threshold: Decimal | None = None
    ) -> list[ReboundDataModel]:
        """Get all rebounds for a ticker.

        Args:
            ticker_history_id: ID of ticker_history record
            threshold: Optional threshold filter (e.g., Decimal("0.20") for 20%)

        Returns:
            List of Rebound patterns
        """
        try:
            with self._SessionLocal() as session:
                stmt = select(ReboundDBModel).where(
                    ReboundDBModel.ticker_history_id == ticker_history_id
                )

                if threshold is not None:
                    # Convert threshold to basis points
                    threshold_bp = int(threshold * Decimal("10000"))
                    stmt = stmt.where(ReboundDBModel.threshold == threshold_bp)

                # Order by rebound date descending (most recent first)
                stmt = stmt.order_by(ReboundDBModel.rebound_date.desc())

                result = session.execute(stmt)
                db_models = result.scalars().all()

                return [
                    ReboundDataModel.from_db_model(db_model) for db_model in db_models
                ]

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving rebounds for ticker_history_id {ticker_history_id}: {e}"
            )
            raise

    def get_rebounds_by_date_range(
        self, from_date: date, to_date: date, threshold: Decimal | None = None
    ) -> list[ReboundDataModel]:
        """Get rebounds that completed within a date range.

        Args:
            from_date: Start date (inclusive)
            to_date: End date (inclusive)
            threshold: Optional threshold filter

        Returns:
            List of Rebound patterns within the date range
        """
        try:
            with self._SessionLocal() as session:
                stmt = select(ReboundDBModel).where(
                    ReboundDBModel.rebound_date >= from_date,
                    ReboundDBModel.rebound_date <= to_date,
                )

                if threshold is not None:
                    # Convert threshold to basis points
                    threshold_bp = int(threshold * Decimal("10000"))
                    stmt = stmt.where(ReboundDBModel.threshold == threshold_bp)

                # Order by rebound date
                stmt = stmt.order_by(ReboundDBModel.rebound_date)

                result = session.execute(stmt)
                db_models = result.scalars().all()

                return [
                    ReboundDataModel.from_db_model(db_model) for db_model in db_models
                ]

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving rebounds for date range {from_date} to {to_date}: {e}"
            )
            raise

    def get_recent_rebounds(self, days_back: int = 30) -> list[ReboundDataModel]:
        """Get rebounds that completed in the last N days.

        Args:
            days_back: Number of days to look back from today

        Returns:
            List of recent Rebound patterns
        """
        from datetime import timedelta

        to_date = date.today()
        from_date = to_date - timedelta(days=days_back)

        return self.get_rebounds_by_date_range(from_date, to_date)

    # TODO when writing to Postgres do we lose precision?  can we trust that we can search a
    # decimal value in a Postgres Database?
    def get_rebounds_by_ticker_and_threshold(
        self, ticker_history_id: int, threshold: Decimal
    ) -> list[ReboundDataModel]:
        """Get all rebounds for a specific ticker and threshold.

        Args:
            ticker_history_id: ID of ticker_history record
            threshold: Threshold as decimal (e.g., Decimal("0.20") for 20%)

        Returns:
            List of Rebound patterns matching criteria
        """
        try:
            with self._SessionLocal() as session:
                # Convert threshold to basis points
                threshold_bp = int(threshold * Decimal("10000"))

                stmt = select(ReboundDBModel).where(
                    ReboundDBModel.ticker_history_id == ticker_history_id,
                    ReboundDBModel.threshold == threshold_bp,
                )

                # Order by rebound date descending
                stmt = stmt.order_by(ReboundDBModel.rebound_date.desc())

                result = session.execute(stmt)
                db_models = result.scalars().all()

                return [
                    ReboundDataModel.from_db_model(db_model) for db_model in db_models
                ]

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving rebounds for ticker {ticker_history_id}, threshold {threshold}: {e}"
            )
            raise

    def count_rebounds_by_ticker(
        self, ticker_history_id: int, threshold: Decimal | None = None
    ) -> int:
        """Count rebounds for a ticker.

        Args:
            ticker_history_id: ID of ticker_history record
            threshold: Optional threshold filter

        Returns:
            Number of rebounds for the ticker
        """
        try:
            with self._SessionLocal() as session:
                stmt = select(ReboundDBModel).where(
                    ReboundDBModel.ticker_history_id == ticker_history_id
                )

                if threshold is not None:
                    # Convert threshold to basis points
                    threshold_bp = int(threshold * Decimal("10000"))
                    stmt = stmt.where(ReboundDBModel.threshold == threshold_bp)

                result = session.execute(stmt)
                return len(result.scalars().all())

        except SQLAlchemyError as e:
            logger.error(
                f"Database error counting rebounds for ticker_history_id {ticker_history_id}: {e}"
            )
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
