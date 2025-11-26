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

    def _create_id_filter(self, id: int) -> TickerHistoryDataModel:
        """Create a TickerHistory filter model for ID lookups."""
        return TickerHistoryDataModel(
            symbol="",  # Will be ignored
            company_id=0,  # Will be ignored
            valid_from=date.today(),  # Will be ignored
            id=id,  # Will be used as filter
        )

    # Domain-specific methods using base repository functionality
    def get_ticker_history_for_company(
        self, company_id: int
    ) -> list[TickerHistoryDataModel]:
        """Get all ticker history records for a specific company using base repository."""
        company_filter = TickerHistoryDataModel(
            symbol="", company_id=company_id, valid_from=date.today()
        )
        options = QueryOptions(order_by="valid_from")
        return self.get(company_filter, options)

    def get_ticker_history_by_symbol(self, symbol: str) -> list[TickerHistoryDataModel]:
        """Get all ticker history records for a symbol using base repository."""
        symbol_filter = TickerHistoryDataModel(
            symbol=symbol, company_id=0, valid_from=date.today()
        )
        options = QueryOptions(order_by="valid_from")
        return self.get(symbol_filter, options)

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
        return self.get()  # Uses base repository get() method

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

    def deactivate_ticker_history(
        self, symbol: str, company_id: int, end_date: date | None = None
    ) -> bool:
        """Set the end date for a ticker history record using base repository update."""
        if end_date is None:
            end_date = date.today()

        filter_data = TickerHistoryDataModel(
            symbol=symbol,
            company_id=company_id,
            valid_from=date.today(),  # Will be ignored in filter
        )

        update_data = TickerHistoryDataModel(
            symbol="",  # Will be ignored
            company_id=0,  # Will be ignored
            valid_from=date.today(),  # Will be ignored
            valid_to=end_date,  # Will be used to update
        )

        return self.update(filter_data, update_data) > 0
