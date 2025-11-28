"""Misplaced EOD pricing repository for database operations.

This repository handles pricing data that does not currently have an association
with ticker_history records.
"""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import and_, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from src.config.configuration import CONFIG
from src.database.equities.tables.misplaced_eod_pricing import (
    MisplacedEodPricing as MisplacedEodPricingDBModel,
)
from src.models.misplaced_eod_pricing import (
    MisplacedEndOfDayPricing as MisplacedEodPricingDataModel,
)
from src.repos.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class MisplacedEodPricingRepository(
    BaseRepository[MisplacedEodPricingDataModel, MisplacedEodPricingDBModel]
):
    """Repository for misplaced EOD pricing database operations.

    Handles pricing data without ticker_history associations.
    """

    def __init__(self) -> None:
        """Initialize misplaced EOD pricing repository."""
        super().__init__(
            config_getter=CONFIG.get_equities_config,
            data_model_class=MisplacedEodPricingDataModel,
            db_model_class=MisplacedEodPricingDBModel,
        )

    @staticmethod
    def from_db_model(db_model: MisplacedEodPricingDBModel) -> MisplacedEodPricingDataModel:
        """Create data model from SQLAlchemy database model.

        Args:
            db_model: SQLAlchemy MisplacedEodPricing instance from database

        Returns:
            MisplacedEndOfDayPricing: Data model instance
        """
        from src.database.equities.tables.misplaced_eod_pricing import PRICE_MULTIPLIER
        from decimal import Decimal

        return MisplacedEodPricingDataModel(
            symbol=db_model.symbol,
            date=db_model.date,
            open=Decimal(db_model.open) / PRICE_MULTIPLIER,
            high=Decimal(db_model.high) / PRICE_MULTIPLIER,
            low=Decimal(db_model.low) / PRICE_MULTIPLIER,
            close=Decimal(db_model.close) / PRICE_MULTIPLIER,
            adjusted_close=Decimal(db_model.adjusted_close) / PRICE_MULTIPLIER,
            volume=db_model.volume,
            source=db_model.source,
        )

    @staticmethod
    def to_db_model(data_model: MisplacedEodPricingDataModel) -> MisplacedEodPricingDBModel:
        """Convert data model to SQLAlchemy database model.

        Returns:
            DBMisplacedEodPricing: SQLAlchemy model instance ready for database operations
        """
        from src.database.equities.tables.misplaced_eod_pricing import PRICE_MULTIPLIER

        return MisplacedEodPricingDBModel(
            symbol=data_model.symbol,
            date=data_model.date,
            open=int(data_model.open * PRICE_MULTIPLIER),
            high=int(data_model.high * PRICE_MULTIPLIER),
            low=int(data_model.low * PRICE_MULTIPLIER),
            close=int(data_model.close * PRICE_MULTIPLIER),
            adjusted_close=int(data_model.adjusted_close * PRICE_MULTIPLIER),
            volume=data_model.volume,
            source=data_model.source,
        )

    def get_pricing_for_date(
        self, symbol: str, target_date: date
    ) -> MisplacedEodPricingDataModel | None:
        """Get pricing data for a specific symbol and date.

        Args:
            symbol: Stock symbol
            target_date: The specific date

        Returns:
            Pricing data model for that date, or None if not found
        """
        try:
            with self._SessionLocal() as session:
                query = select(MisplacedEodPricingDBModel).where(
                    and_(
                        MisplacedEodPricingDBModel.symbol == symbol,
                        MisplacedEodPricingDBModel.date == target_date,
                    )
                )

                result = session.execute(query)
                db_model = result.scalar_one_or_none()

                if db_model:
                    logger.debug(f"Found misplaced pricing for {symbol} on {target_date}")
                    return self.from_db_model(db_model)
                else:
                    logger.debug(
                        f"No misplaced pricing found for {symbol} on {target_date}"
                    )
                    return None

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving misplaced pricing for date: {e}")
            raise

    def bulk_upsert_pricing(
        self, pricing_data: list[MisplacedEodPricingDataModel]
    ) -> dict[str, int]:
        """Bulk insert or update misplaced pricing data.

        Uses PostgreSQL's ON CONFLICT DO UPDATE to handle duplicates.
        If a record with the same symbol and date exists, it will be updated.

        Args:
            pricing_data: List of pricing data models to upsert

        Returns:
            Dictionary with 'inserted' and 'updated' counts
        """
        if not pricing_data:
            logger.info("No misplaced pricing data to upsert")
            return {"inserted": 0, "updated": 0}

        try:
            with self._SessionLocal() as session:
                # Convert data models to DB models
                db_models = [self.to_db_model(pricing) for pricing in pricing_data]

                # Prepare values for upsert
                values = [
                    {
                        "symbol": db_model.symbol,
                        "date": db_model.date,
                        "open": db_model.open,
                        "high": db_model.high,
                        "low": db_model.low,
                        "close": db_model.close,
                        "adjusted_close": db_model.adjusted_close,
                        "volume": db_model.volume,
                        "source": db_model.source,
                    }
                    for db_model in db_models
                ]

                # Create upsert statement
                stmt = insert(MisplacedEodPricingDBModel).values(values)

                # On conflict, update all fields except symbol and date
                stmt = stmt.on_conflict_do_update(
                    constraint="pk_misplaced_symbol_date",
                    set_={
                        "open": stmt.excluded.open,
                        "high": stmt.excluded.high,
                        "low": stmt.excluded.low,
                        "close": stmt.excluded.close,
                        "adjusted_close": stmt.excluded.adjusted_close,
                        "volume": stmt.excluded.volume,
                        "source": stmt.excluded.source,
                    },
                )

                session.execute(stmt)
                session.commit()

                total = len(pricing_data)
                logger.info(f"Upserted {total} misplaced pricing records")

                return {"inserted": total, "updated": 0}

        except SQLAlchemyError as e:
            logger.error(f"Database error in bulk_upsert_pricing: {e}")
            raise
