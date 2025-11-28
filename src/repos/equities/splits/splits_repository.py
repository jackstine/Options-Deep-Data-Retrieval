"""Splits repository for database operations.

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
from src.database.equities.tables.splits import Split as SplitDBModel
from src.models.split import Split as SplitDataModel
from src.repos.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SplitsRepository(BaseRepository[SplitDataModel, SplitDBModel]):
    """Repository for stock splits database operations.

    Note: Uses ticker_history_id to reference ticker_history table, supporting
    both active and delisted symbols.
    """

    def __init__(self) -> None:
        """Initialize splits repository."""
        super().__init__(
            config_getter=CONFIG.get_equities_config,
            data_model_class=SplitDataModel,
            db_model_class=SplitDBModel,
        )

    def get_splits_by_ticker(
        self,
        ticker_history_id: int,
        from_date: date | None = None,
        to_date: date | None = None,
        limit: int | None = None,
    ) -> list[SplitDataModel]:
        """Get split data for a ticker_history within a date range.

        Args:
            ticker_history_id: ID of the ticker_history record
            from_date: Start date (inclusive), None for no lower bound
            to_date: End date (inclusive), None for no upper bound
            limit: Maximum number of records to return

        Returns:
            List of split data models, ordered by date descending
        """
        try:
            with self._SessionLocal() as session:
                query = select(SplitDBModel).where(
                    SplitDBModel.ticker_history_id == ticker_history_id
                )

                # Apply date filters
                if from_date:
                    query = query.where(SplitDBModel.date >= from_date)
                if to_date:
                    query = query.where(SplitDBModel.date <= to_date)

                # Order by date descending (most recent first)
                query = query.order_by(SplitDBModel.date.desc())

                # Apply limit
                if limit:
                    query = query.limit(limit)

                result = session.execute(query)
                db_models = result.scalars().all()

                data_models = [
                    SplitDataModel.from_db_model(db_model) for db_model in db_models
                ]
                logger.info(
                    f"Retrieved {len(data_models)} split records for ticker_history_id={ticker_history_id}"
                )
                return data_models

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving splits by ticker: {e}")
            raise

    def bulk_upsert_splits(
        self,
        ticker_history_id: int,
        splits_data: list[SplitDataModel],
    ) -> dict[str, int]:
        """Bulk insert or update split data for a ticker_history.

        Uses PostgreSQL's ON CONFLICT DO UPDATE to handle duplicates.
        If a record with the same ticker_history_id and date exists, it will be updated.

        Args:
            ticker_history_id: ID of the ticker_history record
            splits_data: List of split data models to upsert

        Returns:
            Dictionary with 'inserted' and 'updated' counts
        """
        if not splits_data:
            logger.info("No split data to upsert")
            return {"inserted": 0, "updated": 0}

        try:
            with self._SessionLocal() as session:
                # Set ticker_history_id on each split data model
                for split in splits_data:
                    split.ticker_history_id = ticker_history_id

                # Convert data models to DB models
                db_models = [split.to_db_model() for split in splits_data]

                # Prepare values for upsert
                values = [
                    {
                        "ticker_history_id": db_model.ticker_history_id,
                        "date": db_model.date,
                        "split_ratio": db_model.split_ratio,
                    }
                    for db_model in db_models
                ]

                # Create upsert statement
                stmt = insert(SplitDBModel).values(values)

                # On conflict, update split_ratio
                stmt = stmt.on_conflict_do_update(
                    constraint="uq_splits_ticker_history_date",
                    set_={
                        "split_ratio": stmt.excluded.split_ratio,
                    },
                )

                session.execute(stmt)
                session.commit()

                # PostgreSQL doesn't provide separate insert/update counts easily
                # So we'll just return the total as inserted
                total = len(splits_data)
                logger.info(
                    f"Upserted {total} split records for ticker_history_id={ticker_history_id}"
                )

                return {"inserted": total, "updated": 0}

        except SQLAlchemyError as e:
            logger.error(f"Database error in bulk_upsert_splits: {e}")
            raise
