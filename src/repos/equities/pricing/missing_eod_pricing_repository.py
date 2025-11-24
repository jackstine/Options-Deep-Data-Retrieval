"""Missing EOD pricing repository for database operations.

This repository tracks which dates are missing pricing data for specific tickers.
"""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import and_, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from src.config.configuration import CONFIG
from src.database.equities.tables.missing_eod_pricing import (
    MissingEodPricing as MissingEodPricingDBModel,
)
from src.models.missing_eod_pricing import (
    MissingEndOfDayPricing as MissingEodPricingDataModel,
)
from src.repos.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class MissingEodPricingRepository(
    BaseRepository[MissingEodPricingDataModel, MissingEodPricingDBModel]
):
    """Repository for missing EOD pricing database operations.

    Tracks missing pricing dates for tickers to facilitate data backfilling.
    """

    def __init__(self) -> None:
        """Initialize missing EOD pricing repository."""
        super().__init__(
            config_getter=CONFIG.get_equities_config,
            data_model_class=MissingEodPricingDataModel,
            db_model_class=MissingEodPricingDBModel,
        )

    def _create_id_filter(self, id: int) -> MissingEodPricingDataModel:
        """Create a MissingEodPricing filter model for ID lookups."""
        from datetime import date as date_type

        return MissingEodPricingDataModel(
            company_id=0,  # Will be ignored
            ticker_history_id=0,  # Will be ignored
            date=date_type(1900, 1, 1),  # Will be ignored
        )

    # Domain-specific methods

    def get_missing_dates_by_ticker(
        self,
        ticker_history_id: int,
        from_date: date | None = None,
        to_date: date | None = None,
        limit: int | None = None,
    ) -> list[MissingEodPricingDataModel]:
        """Get missing pricing dates for a ticker_history within a date range.

        Args:
            ticker_history_id: ID of the ticker_history record
            from_date: Start date (inclusive), None for no lower bound
            to_date: End date (inclusive), None for no upper bound
            limit: Maximum number of records to return

        Returns:
            List of missing pricing data models, ordered by date ascending
        """
        try:
            with self._SessionLocal() as session:
                query = select(MissingEodPricingDBModel).where(
                    MissingEodPricingDBModel.ticker_history_id == ticker_history_id
                )

                # Apply date filters
                if from_date:
                    query = query.where(MissingEodPricingDBModel.date >= from_date)
                if to_date:
                    query = query.where(MissingEodPricingDBModel.date <= to_date)

                # Order by date ascending (oldest first)
                query = query.order_by(MissingEodPricingDBModel.date.asc())

                # Apply limit
                if limit:
                    query = query.limit(limit)

                result = session.execute(query)
                db_models = result.scalars().all()

                data_models = [
                    MissingEodPricingDataModel.from_db_model(db_model)
                    for db_model in db_models
                ]
                logger.info(
                    f"Retrieved {len(data_models)} missing pricing dates for ticker_history_id={ticker_history_id}"
                )
                return data_models

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving missing dates by ticker_history: {e}"
            )
            raise

    def get_missing_dates_by_company(
        self,
        company_id: int,
        from_date: date | None = None,
        to_date: date | None = None,
        limit: int | None = None,
    ) -> list[MissingEodPricingDataModel]:
        """Get missing pricing dates for a company within a date range.

        Args:
            company_id: ID of the company record
            from_date: Start date (inclusive), None for no lower bound
            to_date: End date (inclusive), None for no upper bound
            limit: Maximum number of records to return

        Returns:
            List of missing pricing data models, ordered by date ascending
        """
        try:
            with self._SessionLocal() as session:
                query = select(MissingEodPricingDBModel).where(
                    MissingEodPricingDBModel.company_id == company_id
                )

                # Apply date filters
                if from_date:
                    query = query.where(MissingEodPricingDBModel.date >= from_date)
                if to_date:
                    query = query.where(MissingEodPricingDBModel.date <= to_date)

                # Order by date ascending (oldest first)
                query = query.order_by(MissingEodPricingDBModel.date.asc())

                # Apply limit
                if limit:
                    query = query.limit(limit)

                result = session.execute(query)
                db_models = result.scalars().all()

                data_models = [
                    MissingEodPricingDataModel.from_db_model(db_model)
                    for db_model in db_models
                ]
                logger.info(
                    f"Retrieved {len(data_models)} missing pricing dates for company_id={company_id}"
                )
                return data_models

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving missing dates by company: {e}")
            raise

    def check_missing_date(
        self, company_id: int, ticker_history_id: int, target_date: date
    ) -> bool:
        """Check if a specific date is marked as missing for a ticker.

        Args:
            company_id: ID of the company record
            ticker_history_id: ID of the ticker_history record
            target_date: The specific date to check

        Returns:
            True if the date is marked as missing, False otherwise
        """
        try:
            with self._SessionLocal() as session:
                query = select(MissingEodPricingDBModel).where(
                    and_(
                        MissingEodPricingDBModel.company_id == company_id,
                        MissingEodPricingDBModel.ticker_history_id == ticker_history_id,
                        MissingEodPricingDBModel.date == target_date,
                    )
                )

                result = session.execute(query)
                db_model = result.scalar_one_or_none()

                return db_model is not None

        except SQLAlchemyError as e:
            logger.error(f"Database error checking missing date: {e}")
            raise

    def bulk_insert_missing_dates(
        self, missing_data: list[MissingEodPricingDataModel]
    ) -> dict[str, int]:
        """Bulk insert missing pricing dates.

        Uses PostgreSQL's ON CONFLICT DO NOTHING to ignore duplicates.

        Args:
            missing_data: List of missing pricing data models to insert

        Returns:
            Dictionary with 'inserted' count
        """
        if not missing_data:
            logger.info("No missing pricing data to insert")
            return {"inserted": 0}

        try:
            with self._SessionLocal() as session:
                # Convert data models to DB models
                db_models = [data.to_db_model() for data in missing_data]

                # Prepare values for insert
                values = [
                    {
                        "company_id": db_model.company_id,
                        "ticker_history_id": db_model.ticker_history_id,
                        "date": db_model.date,
                    }
                    for db_model in db_models
                ]

                # Create insert statement with ON CONFLICT DO NOTHING
                stmt = insert(MissingEodPricingDBModel).values(values)
                stmt = stmt.on_conflict_do_nothing(
                    constraint="pk_missing_pricing_composite"
                )

                session.execute(stmt)
                session.commit()

                total = len(missing_data)
                logger.info(f"Inserted {total} missing pricing date records")

                return {"inserted": total}

        except SQLAlchemyError as e:
            logger.error(f"Database error in bulk_insert_missing_dates: {e}")
            raise

    def delete_missing_dates_by_ticker(
        self,
        ticker_history_id: int,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> int:
        """Delete missing pricing dates for a ticker_history within an optional date range.

        Args:
            ticker_history_id: ID of the ticker_history record
            from_date: Start date (inclusive), None for no lower bound
            to_date: End date (inclusive), None for no upper bound

        Returns:
            Number of records deleted
        """
        try:
            with self._SessionLocal() as session:
                query = delete(MissingEodPricingDBModel).where(
                    MissingEodPricingDBModel.ticker_history_id == ticker_history_id
                )

                # Apply date filters
                if from_date:
                    query = query.where(MissingEodPricingDBModel.date >= from_date)
                if to_date:
                    query = query.where(MissingEodPricingDBModel.date <= to_date)

                result = session.execute(query)
                session.commit()

                deleted_count = result.rowcount
                logger.info(
                    f"Deleted {deleted_count} missing pricing records for ticker_history_id={ticker_history_id}"
                )
                return deleted_count

        except SQLAlchemyError as e:
            logger.error(f"Database error in delete_missing_dates_by_ticker: {e}")
            raise

    def delete_specific_missing_date(
        self, company_id: int, ticker_history_id: int, target_date: date
    ) -> int:
        """Delete a specific missing pricing date record.

        Args:
            company_id: ID of the company record
            ticker_history_id: ID of the ticker_history record
            target_date: The specific date to delete

        Returns:
            Number of records deleted (0 or 1)
        """
        try:
            with self._SessionLocal() as session:
                query = delete(MissingEodPricingDBModel).where(
                    and_(
                        MissingEodPricingDBModel.company_id == company_id,
                        MissingEodPricingDBModel.ticker_history_id == ticker_history_id,
                        MissingEodPricingDBModel.date == target_date,
                    )
                )

                result = session.execute(query)
                session.commit()

                deleted_count = result.rowcount
                logger.debug(
                    f"Deleted missing pricing record for company_id={company_id}, "
                    f"ticker_history_id={ticker_history_id}, date={target_date}"
                )
                return deleted_count

        except SQLAlchemyError as e:
            logger.error(f"Database error in delete_specific_missing_date: {e}")
            raise

    def get_count_by_ticker(self, ticker_history_id: int) -> int:
        """Get count of missing pricing dates for a ticker_history.

        Args:
            ticker_history_id: ID of the ticker_history record

        Returns:
            Count of missing dates
        """
        try:
            with self._SessionLocal() as session:
                from sqlalchemy import func

                query = select(func.count()).where(
                    MissingEodPricingDBModel.ticker_history_id == ticker_history_id
                )

                result = session.execute(query)
                count = result.scalar()

                logger.debug(
                    f"Count of missing dates for ticker_history_id={ticker_history_id}: {count}"
                )
                return count or 0

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_count_by_ticker: {e}")
            raise
