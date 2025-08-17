"""Ticker repository for database operations."""

from __future__ import annotations

import logging

from src.config.configuration import CONFIG
from src.data_sources.models.ticker import Ticker as TickerDataModel
from src.database.equities.tables.ticker import Ticker as TickerDBModel
from src.repos.base_repository import BaseRepository

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class TickerRepository(BaseRepository[TickerDataModel, TickerDBModel]):
    """Repository for ticker database operations."""

    def __init__(self) -> None:
        """Initialize ticker repository."""
        super().__init__(
            config_getter=CONFIG.get_equities_config, db_model_class=TickerDBModel
        )

    def _create_id_filter(self, id: int) -> TickerDataModel:
        """Create a Ticker filter model for ID lookups."""
        return TickerDataModel(
            symbol="",  # Will be ignored
            company_id=0,  # Will be ignored
            id=id,  # Will be used as filter
        )

    # Domain-specific methods using base repository functionality
    def get_active_ticker_symbols(self) -> set[str]:
        """Get all ticker symbols from the database.

        Returns:
            Set of ticker symbols
        """
        try:
            with self._SessionLocal() as session:
                result = session.execute(select(TickerDBModel.symbol))
                symbols = {row[0] for row in result.fetchall()}
                logger.info(f"Retrieved {len(symbols)} ticker symbols from database")
                return symbols

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving ticker symbols: {e}")
            raise

    def get_tickers_for_company(self, company_id: int) -> list[TickerDataModel]:
        """Get all tickers for a specific company using base repository."""
        company_filter = TickerDataModel(symbol="", company_id=company_id)
        return self.get(company_filter)

    def get_ticker_by_symbol(self, symbol: str) -> TickerDataModel | None:
        """Get ticker by symbol using base repository."""
        symbol_filter = TickerDataModel(symbol=symbol, company_id=0)
        return self.get_one(symbol_filter)

    def bulk_insert_tickers(self, tickers: list[TickerDataModel]) -> int:
        """Bulk insert tickers using base repository."""
        return self.insert_many(tickers)

    def get_all_tickers(self) -> list[TickerDataModel]:
        """Retrieve all tickers from the database using base repository."""
        return self.get()  # Uses base repository get() method

    def create_ticker_for_company(
        self, symbol: str, company_id: int
    ) -> TickerDataModel:
        """Create a new ticker for a company using base repository."""
        ticker_data = TickerDataModel(symbol=symbol, company_id=company_id)
        return self.insert(ticker_data)

    def update_ticker_company(self, symbol: str, new_company_id: int) -> bool:
        """Update the company_id for a ticker symbol using base repository."""
        symbol_filter = TickerDataModel(symbol=symbol, company_id=0)
        update_data = TickerDataModel(symbol="", company_id=new_company_id)
        return self.update(symbol_filter, update_data) > 0
