"""Historical EOD pricing repository for database operations."""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import and_, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from src.config.configuration import CONFIG
from src.data_sources.models.historical_eod_pricing import (
    HistoricalEndOfDayPricing as HistoricalEodPricingDataModel,
)
from src.database.equities.tables.historical_eod_pricing import (
    HistoricalEodPricing as HistoricalEodPricingDBModel,
)
from src.repos.base_repository import BaseRepository, QueryOptions

logger = logging.getLogger(__name__)


class HistoricalEodPricingRepository(
    BaseRepository[HistoricalEodPricingDataModel, HistoricalEodPricingDBModel]
):
    """Repository for historical EOD pricing database operations."""

    def __init__(self) -> None:
        """Initialize historical EOD pricing repository."""
        super().__init__(
            config_getter=CONFIG.get_equities_config,
            db_model_class=HistoricalEodPricingDBModel,
        )

    def _create_id_filter(self, id: int) -> HistoricalEodPricingDataModel:
        """Create a HistoricalEodPricing filter model for ID lookups."""
        from decimal import Decimal
        from datetime import date as date_type

        return HistoricalEodPricingDataModel(
            date=date_type(1900, 1, 1),  # Will be ignored
            open=Decimal("0"),  # Will be ignored
            high=Decimal("0"),  # Will be ignored
            low=Decimal("0"),  # Will be ignored
            close=Decimal("0"),  # Will be ignored
            adjusted_close=Decimal("0"),  # Will be ignored
            volume=0,  # Will be ignored
            id=id,  # Will be used as filter
        )

    # Domain-specific methods

    def get_pricing_by_ticker(
        self,
        ticker_id: int,
        from_date: date | None = None,
        to_date: date | None = None,
        limit: int | None = None,
    ) -> list[HistoricalEodPricingDataModel]:
        """Get pricing data for a ticker within a date range.

        Args:
            ticker_id: ID of the ticker
            from_date: Start date (inclusive), None for no lower bound
            to_date: End date (inclusive), None for no upper bound
            limit: Maximum number of records to return

        Returns:
            List of pricing data models, ordered by date descending
        """
        try:
            with self._SessionLocal() as session:
                query = select(HistoricalEodPricingDBModel).where(
                    HistoricalEodPricingDBModel.ticker_id == ticker_id
                )

                # Apply date filters
                if from_date:
                    query = query.where(
                        HistoricalEodPricingDBModel.date >= from_date
                    )
                if to_date:
                    query = query.where(
                        HistoricalEodPricingDBModel.date <= to_date
                    )

                # Order by date descending (most recent first)
                query = query.order_by(HistoricalEodPricingDBModel.date.desc())

                # Apply limit
                if limit:
                    query = query.limit(limit)

                result = session.execute(query)
                db_models = result.scalars().all()

                data_models = [db_model.to_data_model() for db_model in db_models]
                logger.info(
                    f"Retrieved {len(data_models)} pricing records for ticker_id={ticker_id}"
                )
                return data_models

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving pricing by ticker: {e}")
            raise

    def get_latest_pricing(
        self, ticker_id: int
    ) -> HistoricalEodPricingDataModel | None:
        """Get the most recent pricing data for a ticker.

        Args:
            ticker_id: ID of the ticker

        Returns:
            Most recent pricing data model, or None if no data exists
        """
        results = self.get_pricing_by_ticker(ticker_id, limit=1)
        return results[0] if results else None

    def get_pricing_for_date(
        self, ticker_id: int, target_date: date
    ) -> HistoricalEodPricingDataModel | None:
        """Get pricing data for a specific ticker and date.

        Args:
            ticker_id: ID of the ticker
            target_date: The specific date

        Returns:
            Pricing data model for that date, or None if not found
        """
        try:
            with self._SessionLocal() as session:
                query = select(HistoricalEodPricingDBModel).where(
                    and_(
                        HistoricalEodPricingDBModel.ticker_id == ticker_id,
                        HistoricalEodPricingDBModel.date == target_date,
                    )
                )

                result = session.execute(query)
                db_model = result.scalar_one_or_none()

                if db_model:
                    logger.debug(
                        f"Found pricing for ticker_id={ticker_id} on {target_date}"
                    )
                    return db_model.to_data_model()
                else:
                    logger.debug(
                        f"No pricing found for ticker_id={ticker_id} on {target_date}"
                    )
                    return None

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving pricing for date: {e}")
            raise

    def bulk_upsert_pricing(
        self,
        ticker_id: int,
        pricing_data: list[HistoricalEodPricingDataModel],
    ) -> dict[str, int]:
        """Bulk insert or update pricing data for a ticker.

        Uses PostgreSQL's ON CONFLICT DO UPDATE to handle duplicates.
        If a record with the same ticker_id and date exists, it will be updated.

        Args:
            ticker_id: ID of the ticker
            pricing_data: List of pricing data models to upsert

        Returns:
            Dictionary with 'inserted' and 'updated' counts
        """
        if not pricing_data:
            logger.info("No pricing data to upsert")
            return {"inserted": 0, "updated": 0}

        try:
            with self._SessionLocal() as session:
                # Convert data models to DB models
                db_models = [
                    HistoricalEodPricingDBModel.from_data_model(pricing, ticker_id)
                    for pricing in pricing_data
                ]

                # Prepare values for upsert
                values = [
                    {
                        "ticker_id": db_model.ticker_id,
                        "date": db_model.date,
                        "open": db_model.open,
                        "high": db_model.high,
                        "low": db_model.low,
                        "close": db_model.close,
                        "adjusted_close": db_model.adjusted_close,
                        "volume": db_model.volume,
                    }
                    for db_model in db_models
                ]

                # Create upsert statement
                stmt = insert(HistoricalEodPricingDBModel).values(values)

                # On conflict, update all fields except ticker_id and date
                stmt = stmt.on_conflict_do_update(
                    constraint="uq_ticker_date",
                    set_={
                        "open": stmt.excluded.open,
                        "high": stmt.excluded.high,
                        "low": stmt.excluded.low,
                        "close": stmt.excluded.close,
                        "adjusted_close": stmt.excluded.adjusted_close,
                        "volume": stmt.excluded.volume,
                    },
                )

                result = session.execute(stmt)
                session.commit()

                # PostgreSQL doesn't provide separate insert/update counts easily
                # So we'll just return the total as inserted
                total = len(pricing_data)
                logger.info(f"Upserted {total} pricing records for ticker_id={ticker_id}")

                return {"inserted": total, "updated": 0}

        except SQLAlchemyError as e:
            logger.error(f"Database error in bulk_upsert_pricing: {e}")
            raise

    def delete_pricing_by_ticker(
        self, ticker_id: int, from_date: date | None = None, to_date: date | None = None
    ) -> int:
        """Delete pricing data for a ticker within an optional date range.

        Args:
            ticker_id: ID of the ticker
            from_date: Start date (inclusive), None for no lower bound
            to_date: End date (inclusive), None for no upper bound

        Returns:
            Number of records deleted
        """
        try:
            with self._SessionLocal() as session:
                query = delete(HistoricalEodPricingDBModel).where(
                    HistoricalEodPricingDBModel.ticker_id == ticker_id
                )

                # Apply date filters
                if from_date:
                    query = query.where(
                        HistoricalEodPricingDBModel.date >= from_date
                    )
                if to_date:
                    query = query.where(
                        HistoricalEodPricingDBModel.date <= to_date
                    )

                result = session.execute(query)
                session.commit()

                deleted_count = result.rowcount
                logger.info(
                    f"Deleted {deleted_count} pricing records for ticker_id={ticker_id}"
                )
                return deleted_count

        except SQLAlchemyError as e:
            logger.error(f"Database error in delete_pricing_by_ticker: {e}")
            raise

    def get_date_range_for_ticker(self, ticker_id: int) -> tuple[date | None, date | None]:
        """Get the min and max dates available for a ticker.

        Args:
            ticker_id: ID of the ticker

        Returns:
            Tuple of (earliest_date, latest_date), or (None, None) if no data
        """
        try:
            with self._SessionLocal() as session:
                from sqlalchemy import func

                query = select(
                    func.min(HistoricalEodPricingDBModel.date),
                    func.max(HistoricalEodPricingDBModel.date),
                ).where(HistoricalEodPricingDBModel.ticker_id == ticker_id)

                result = session.execute(query)
                min_date, max_date = result.one()

                logger.debug(
                    f"Date range for ticker_id={ticker_id}: {min_date} to {max_date}"
                )
                return (min_date, max_date)

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_date_range_for_ticker: {e}")
            raise
