"""Reversals repository for database operations."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.config.configuration import CONFIG
from src.database.algorithms.tables.reversals import Reversal as ReversalDBModel
from src.models.reversal import Reversal as ReversalDataModel
from src.repos.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ReversalsRepository(BaseRepository[ReversalDataModel, ReversalDBModel]):
    """Repository for reversals pattern database operations."""

    def __init__(self) -> None:
        """Initialize reversals repository."""
        super().__init__(
            config_getter=CONFIG.get_algorithm_config,
            data_model_class=ReversalDataModel,
            db_model_class=ReversalDBModel,
        )

    def _create_id_filter(self, id: int) -> ReversalDataModel:
        """Create a Reversal filter model for ID lookups."""
        return ReversalDataModel(
            ticker_history_id=0,  # Will be ignored
            threshold=Decimal("0"),  # Will be ignored
            low_start_price=Decimal("0"),  # Will be ignored
            low_start_date=date(1900, 1, 1),  # Will be ignored
            high_threshold_price=Decimal("0"),  # Will be ignored
            high_threshold_date=date(1900, 1, 1),  # Will be ignored
            highest_price=Decimal("0"),  # Will be ignored
            highest_date=date(1900, 1, 1),  # Will be ignored
            low_threshold_price=Decimal("0"),  # Will be ignored
            low_threshold_date=date(1900, 1, 1),  # Will be ignored
            reversal_price=Decimal("0"),  # Will be ignored
            reversal_date=date(1900, 1, 1),  # Will be ignored
            id=id,  # Will be used as filter
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

    def get_reversals_by_ticker(
        self, ticker_history_id: int, threshold: Decimal | None = None
    ) -> list[ReversalDataModel]:
        """Get all reversals for a ticker.

        Args:
            ticker_history_id: ID of ticker_history record
            threshold: Optional threshold filter (e.g., Decimal("0.20") for 20%)

        Returns:
            List of Reversal patterns
        """
        try:
            with self._SessionLocal() as session:
                stmt = select(ReversalDBModel).where(
                    ReversalDBModel.ticker_history_id == ticker_history_id
                )

                if threshold is not None:
                    # Convert threshold to basis points
                    threshold_bp = int(threshold * Decimal("10000"))
                    stmt = stmt.where(ReversalDBModel.threshold == threshold_bp)

                # Order by reversal date descending (most recent first)
                stmt = stmt.order_by(ReversalDBModel.reversal_date.desc())

                result = session.execute(stmt)
                db_models = result.scalars().all()

                return [
                    ReversalDataModel.from_db_model(db_model) for db_model in db_models
                ]

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving reversals for ticker_history_id {ticker_history_id}: {e}"
            )
            raise

    def get_reversals_by_date_range(
        self, from_date: date, to_date: date, threshold: Decimal | None = None
    ) -> list[ReversalDataModel]:
        """Get reversals that completed within a date range.

        Args:
            from_date: Start date (inclusive)
            to_date: End date (inclusive)
            threshold: Optional threshold filter

        Returns:
            List of Reversal patterns within the date range
        """
        try:
            with self._SessionLocal() as session:
                stmt = select(ReversalDBModel).where(
                    ReversalDBModel.reversal_date >= from_date,
                    ReversalDBModel.reversal_date <= to_date,
                )

                if threshold is not None:
                    # Convert threshold to basis points
                    threshold_bp = int(threshold * Decimal("10000"))
                    stmt = stmt.where(ReversalDBModel.threshold == threshold_bp)

                # Order by reversal date
                stmt = stmt.order_by(ReversalDBModel.reversal_date)

                result = session.execute(stmt)
                db_models = result.scalars().all()

                return [
                    ReversalDataModel.from_db_model(db_model) for db_model in db_models
                ]

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving reversals for date range {from_date} to {to_date}: {e}"
            )
            raise

    def get_recent_reversals(self, days_back: int = 30) -> list[ReversalDataModel]:
        """Get reversals that completed in the last N days.

        Args:
            days_back: Number of days to look back from today

        Returns:
            List of recent Reversal patterns
        """
        from datetime import timedelta

        to_date = date.today()
        from_date = to_date - timedelta(days=days_back)

        return self.get_reversals_by_date_range(from_date, to_date)

    # TODO when writing to Postgres do we lose precision?  can we trust that we can search a
    # decimal value in a Postgres Database?
    def get_reversals_by_ticker_and_threshold(
        self, ticker_history_id: int, threshold: Decimal
    ) -> list[ReversalDataModel]:
        """Get all reversals for a specific ticker and threshold.

        Args:
            ticker_history_id: ID of ticker_history record
            threshold: Threshold as decimal (e.g., Decimal("0.20") for 20%)

        Returns:
            List of Reversal patterns matching criteria
        """
        try:
            with self._SessionLocal() as session:
                # Convert threshold to basis points
                threshold_bp = int(threshold * Decimal("10000"))

                stmt = select(ReversalDBModel).where(
                    ReversalDBModel.ticker_history_id == ticker_history_id,
                    ReversalDBModel.threshold == threshold_bp,
                )

                # Order by reversal date descending
                stmt = stmt.order_by(ReversalDBModel.reversal_date.desc())

                result = session.execute(stmt)
                db_models = result.scalars().all()

                return [
                    ReversalDataModel.from_db_model(db_model) for db_model in db_models
                ]

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving reversals for ticker {ticker_history_id}, threshold {threshold}: {e}"
            )
            raise

    def count_reversals_by_ticker(
        self, ticker_history_id: int, threshold: Decimal | None = None
    ) -> int:
        """Count reversals for a ticker.

        Args:
            ticker_history_id: ID of ticker_history record
            threshold: Optional threshold filter

        Returns:
            Number of reversals for the ticker
        """
        try:
            with self._SessionLocal() as session:
                stmt = select(ReversalDBModel).where(
                    ReversalDBModel.ticker_history_id == ticker_history_id
                )

                if threshold is not None:
                    # Convert threshold to basis points
                    threshold_bp = int(threshold * Decimal("10000"))
                    stmt = stmt.where(ReversalDBModel.threshold == threshold_bp)

                result = session.execute(stmt)
                return len(result.scalars().all())

        except SQLAlchemyError as e:
            logger.error(
                f"Database error counting reversals for ticker_history_id {ticker_history_id}: {e}"
            )
            raise
