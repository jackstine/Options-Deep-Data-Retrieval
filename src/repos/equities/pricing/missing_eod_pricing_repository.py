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
