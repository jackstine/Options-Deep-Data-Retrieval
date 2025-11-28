"""TickerHistory repository for database operations."""

from __future__ import annotations

import logging
from datetime import date

from src.config.configuration import CONFIG
from src.database.equities.tables.ticker_history import (
    TickerHistory as TickerHistoryDBModel,
)
from src.models.ticker_history import (
    TickerHistory as TickerHistoryDataModel,
)
from src.repos.base_repository import BaseRepository, QueryOptions

logger = logging.getLogger(__name__)


class TickerHistoryRepository(
    BaseRepository[TickerHistoryDataModel, TickerHistoryDBModel]
):
    """Repository for ticker history database operations."""

    def __init__(self) -> None:
        """Initialize ticker history repository."""
        super().__init__(
            config_getter=CONFIG.get_equities_config,
            data_model_class=TickerHistoryDataModel,
            db_model_class=TickerHistoryDBModel,
        )

    def get_ticker_history_for_company(
        self, company_id: int
    ) -> list[TickerHistoryDataModel]:
        """Get all ticker history records for a specific company using base repository."""
        company_filter = TickerHistoryDataModel(
           company_id=company_id
        )
        options = QueryOptions(order_by="valid_from")
        return self.get_filter(company_filter, options)

    def get_ticker_history_by_symbol(self, symbol: str) -> list[TickerHistoryDataModel]:
        """Get all ticker history records for a symbol using base repository."""
        symbol_filter = TickerHistoryDataModel(
            symbol=symbol, valid_from=date.today()
        )
        options = QueryOptions(order_by="valid_from")
        return self.get_filter(symbol_filter, options)

    def bulk_insert_ticker_histories(
        self, ticker_histories: list[TickerHistoryDataModel]
    ) -> list[TickerHistoryDataModel]:
        """Bulk insert ticker histories and return them with populated IDs.

        Args:
            ticker_histories: List of ticker history data models to insert

        Returns:
            List of ticker history data models with populated IDs and timestamps
        """
        return self.insert_many_returning(ticker_histories)

    def get_all_ticker_histories(self) -> list[TickerHistoryDataModel]:
        """Retrieve all ticker histories from the database using base repository."""
        return self.get_filter()  # Uses base repository get_filter() method

    def create_ticker_history_for_company(
        self,
        symbol: str,
        company_id: int,
        valid_from: date | None = None,
        valid_to: date | None = None,
    ) -> TickerHistoryDataModel:
        """Create a new ticker history record for a company using base repository."""
        if valid_from is None:
            valid_from = date.today()

        ticker_history_data = TickerHistoryDataModel(
            symbol=symbol,
            company_id=company_id,
            valid_from=valid_from,
            valid_to=valid_to,
        )
        return self.insert(ticker_history_data)

