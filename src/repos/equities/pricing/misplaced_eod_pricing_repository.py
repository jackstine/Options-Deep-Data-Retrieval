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

    def _create_id_filter(self, id: int) -> MisplacedEodPricingDataModel:
        """Create a MisplacedEodPricing filter model for ID lookups."""
        from datetime import date as date_type
        from decimal import Decimal

        from src.database.equities.enums import DataSourceEnum

        return MisplacedEodPricingDataModel(
            symbol="",  # Will be ignored
            date=date_type(1900, 1, 1),  # Will be ignored
            open=Decimal("0"),  # Will be ignored
            high=Decimal("0"),  # Will be ignored
            low=Decimal("0"),  # Will be ignored
            close=Decimal("0"),  # Will be ignored
            adjusted_close=Decimal("0"),  # Will be ignored
            volume=0,  # Will be ignored
            source=DataSourceEnum.EODHD,  # Will be ignored
        )

    # Domain-specific methods

    def get_pricing_by_symbol(
        self,
        symbol: str,
        from_date: date | None = None,
        to_date: date | None = None,
        limit: int | None = None,
    ) -> list[MisplacedEodPricingDataModel]:
        """Get pricing data for a symbol within a date range.

        Args:
            symbol: Stock symbol
            from_date: Start date (inclusive), None for no lower bound
            to_date: End date (inclusive), None for no upper bound
            limit: Maximum number of records to return

        Returns:
            List of pricing data models, ordered by date descending
        """
        try:
            with self._SessionLocal() as session:
                query = select(MisplacedEodPricingDBModel).where(
                    MisplacedEodPricingDBModel.symbol == symbol
                )

                # Apply date filters
                if from_date:
                    query = query.where(MisplacedEodPricingDBModel.date >= from_date)
                if to_date:
                    query = query.where(MisplacedEodPricingDBModel.date <= to_date)

                # Order by date descending (most recent first)
                query = query.order_by(MisplacedEodPricingDBModel.date.desc())

                # Apply limit
                if limit:
                    query = query.limit(limit)

                result = session.execute(query)
                db_models = result.scalars().all()

                data_models = [
                    MisplacedEodPricingDataModel.from_db_model(db_model)
                    for db_model in db_models
                ]
                logger.info(
                    f"Retrieved {len(data_models)} misplaced pricing records for symbol={symbol}"
                )
                return data_models

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving misplaced pricing by symbol: {e}")
            raise

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
                    return MisplacedEodPricingDataModel.from_db_model(db_model)
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
                db_models = [pricing.to_db_model() for pricing in pricing_data]

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

    def delete_pricing_by_symbol(
        self, symbol: str, from_date: date | None = None, to_date: date | None = None
    ) -> int:
        """Delete misplaced pricing data for a symbol within an optional date range.

        Args:
            symbol: Stock symbol
            from_date: Start date (inclusive), None for no lower bound
            to_date: End date (inclusive), None for no upper bound

        Returns:
            Number of records deleted
        """
        try:
            with self._SessionLocal() as session:
                query = delete(MisplacedEodPricingDBModel).where(
                    MisplacedEodPricingDBModel.symbol == symbol
                )

                # Apply date filters
                if from_date:
                    query = query.where(MisplacedEodPricingDBModel.date >= from_date)
                if to_date:
                    query = query.where(MisplacedEodPricingDBModel.date <= to_date)

                result = session.execute(query)
                session.commit()

                deleted_count = result.rowcount
                logger.info(
                    f"Deleted {deleted_count} misplaced pricing records for symbol={symbol}"
                )
                return deleted_count

        except SQLAlchemyError as e:
            logger.error(f"Database error in delete_pricing_by_symbol: {e}")
            raise

    def get_all_symbols(self) -> list[str]:
        """Get a list of all unique symbols in the misplaced pricing table.

        Returns:
            List of unique symbols
        """
        try:
            with self._SessionLocal() as session:
                from sqlalchemy import func

                query = select(MisplacedEodPricingDBModel.symbol).distinct()
                result = session.execute(query)
                symbols = [row[0] for row in result.all()]

                logger.info(f"Found {len(symbols)} unique symbols in misplaced pricing")
                return symbols

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_all_symbols: {e}")
            raise

    def get_date_range_for_symbol(self, symbol: str) -> tuple[date | None, date | None]:
        """Get the min and max dates available for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (earliest_date, latest_date), or (None, None) if no data
        """
        try:
            with self._SessionLocal() as session:
                from sqlalchemy import func

                query = select(
                    func.min(MisplacedEodPricingDBModel.date),
                    func.max(MisplacedEodPricingDBModel.date),
                ).where(MisplacedEodPricingDBModel.symbol == symbol)

                result = session.execute(query)
                min_date, max_date = result.one()

                logger.debug(f"Date range for symbol={symbol}: {min_date} to {max_date}")
                return (min_date, max_date)

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_date_range_for_symbol: {e}")
            raise
