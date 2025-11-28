"""Historical EOD pricing repository for database operations.

Note: This repository uses ticker_history_id (not ticker_id) to support both
active and delisted symbols. The ticker_history table tracks all symbols,
while the ticker table only contains currently active symbols.
"""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import and_, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from src.config.configuration import CONFIG
from src.database.equities.tables.historical_eod_pricing import (
    HistoricalEodPricing as HistoricalEodPricingDBModel,
)
from src.models.historical_eod_pricing import (
    HistoricalEndOfDayPricing as HistoricalEodPricingDataModel,
)
from src.repos.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class HistoricalEodPricingRepository(
    BaseRepository[HistoricalEodPricingDataModel, HistoricalEodPricingDBModel]
):
    """Repository for historical EOD pricing database operations.

    Note: Uses ticker_history_id to reference ticker_history table, supporting
    both active and delisted symbols.
    """

    def __init__(self) -> None:
        """Initialize historical EOD pricing repository."""
        super().__init__(
            config_getter=CONFIG.get_equities_config,
            data_model_class=HistoricalEodPricingDataModel,
            db_model_class=HistoricalEodPricingDBModel,
        )

    def get_pricing_by_ticker(
        self,
        ticker_history_id: int,
        from_date: date | None = None,
        to_date: date | None = None,
        limit: int | None = None,
    ) -> list[HistoricalEodPricingDataModel]:
        """Get pricing data for a ticker_history within a date range.

        Args:
            ticker_history_id: ID of the ticker_history record
            from_date: Start date (inclusive), None for no lower bound
            to_date: End date (inclusive), None for no upper bound
            limit: Maximum number of records to return

        Returns:
            List of pricing data models, ordered by date descending
        """
        try:
            with self._SessionLocal() as session:
                query = select(HistoricalEodPricingDBModel).where(
                    HistoricalEodPricingDBModel.ticker_history_id == ticker_history_id
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

                data_models = [
                    HistoricalEodPricingDataModel.from_db_model(db_model)
                    for db_model in db_models
                ]
                logger.info(
                    f"Retrieved {len(data_models)} pricing records for ticker_history_id={ticker_history_id}"
                )
                return data_models

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving pricing by ticker: {e}")
            raise

    def get_pricing_for_date(
        self, ticker_history_id: int, target_date: date
    ) -> HistoricalEodPricingDataModel | None:
        """Get pricing data for a specific ticker_history and date.

        Args:
            ticker_history_id: ID of the ticker_history record
            target_date: The specific date

        Returns:
            Pricing data model for that date, or None if not found
        """
        try:
            with self._SessionLocal() as session:
                query = select(HistoricalEodPricingDBModel).where(
                    and_(
                        HistoricalEodPricingDBModel.ticker_history_id == ticker_history_id,
                        HistoricalEodPricingDBModel.date == target_date,
                    )
                )

                result = session.execute(query)
                db_model = result.scalar_one_or_none()

                if db_model:
                    logger.debug(
                        f"Found pricing for ticker_history_id={ticker_history_id} on {target_date}"
                    )
                    return HistoricalEodPricingDataModel.from_db_model(db_model)
                else:
                    logger.debug(
                        f"No pricing found for ticker_history_id={ticker_history_id} on {target_date}"
                    )
                    return None

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving pricing for date: {e}")
            raise

    def bulk_upsert_pricing(
        self,
        ticker_history_id: int,
        pricing_data: list[HistoricalEodPricingDataModel],
    ) -> dict[str, int]:
        """Bulk insert or update pricing data for a ticker_history.

        Uses PostgreSQL's ON CONFLICT DO UPDATE to handle duplicates.
        If a record with the same ticker_history_id and date exists, it will be updated.

        Args:
            ticker_history_id: ID of the ticker_history record
            pricing_data: List of pricing data models to upsert

        Returns:
            Dictionary with 'inserted' and 'updated' counts
        """
        if not pricing_data:
            logger.info("No pricing data to upsert")
            return {"inserted": 0, "updated": 0}

        try:
            with self._SessionLocal() as session:
                # Set ticker_history_id on each pricing data model
                for pricing in pricing_data:
                    pricing.ticker_history_id = ticker_history_id

                # Convert data models to DB models
                db_models = [pricing.to_db_model() for pricing in pricing_data]

                # Prepare values for upsert
                values = [
                    {
                        "ticker_history_id": db_model.ticker_history_id,
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

                # On conflict, update all fields except ticker_history_id and date
                stmt = stmt.on_conflict_do_update(
                    constraint="pk_ticker_history_date",
                    set_={
                        "open": stmt.excluded.open,
                        "high": stmt.excluded.high,
                        "low": stmt.excluded.low,
                        "close": stmt.excluded.close,
                        "adjusted_close": stmt.excluded.adjusted_close,
                        "volume": stmt.excluded.volume,
                    },
                )

                session.execute(stmt)
                session.commit()

                # PostgreSQL doesn't provide separate insert/update counts easily
                # So we'll just return the total as inserted
                total = len(pricing_data)
                logger.info(f"Upserted {total} pricing records for ticker_history_id={ticker_history_id}")

                return {"inserted": total, "updated": 0}

        except SQLAlchemyError as e:
            logger.error(f"Database error in bulk_upsert_pricing: {e}")
            raise
