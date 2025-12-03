"""Ticker repository for database operations."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.config.configuration import CONFIG
from src.database.equities.tables.ticker import Ticker as TickerDBModel
from src.models.ticker import Ticker as TickerDataModel
from src.repos.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class TickerRepository(BaseRepository[TickerDataModel, TickerDBModel]):
    """Repository for ticker database operations."""

    def __init__(self) -> None:
        """Initialize ticker repository."""
        super().__init__(
            config_getter=CONFIG.get_equities_config,
            data_model_class=TickerDataModel,
            db_model_class=TickerDBModel,
        )

    @staticmethod
    def from_db_model(db_model: TickerDBModel) -> TickerDataModel:
        """Create data model from SQLAlchemy database model.

        Args:
            db_model: SQLAlchemy Ticker instance from database

        Returns:
            Ticker: Data model instance
        """
        return TickerDataModel(
            id=db_model.id,
            symbol=db_model.symbol,
            company_id=db_model.company_id,
            ticker_history_id=db_model.ticker_history_id,
        )

    @staticmethod
    def to_db_model(data_model: TickerDataModel) -> TickerDBModel:
        """Convert data model to SQLAlchemy database model.

        Args:
            data_model: Ticker data model instance

        Returns:
            DBTicker: SQLAlchemy model instance ready for database operations

        Raises:
            ValueError: If ticker_history_id is None
        """
        if data_model.ticker_history_id is None:
            raise ValueError(
                "ticker_history_id must be set before converting to database model"
            )

        return TickerDBModel(
            symbol=data_model.symbol,
            company_id=data_model.company_id,
            ticker_history_id=data_model.ticker_history_id,
        )

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
        company_filter = TickerDataModel(company_id=company_id)
        return self.get_filter(company_filter)

    def get_ticker_by_symbol(self, symbol: str) -> TickerDataModel | None:
        """Get ticker by symbol using base repository."""
        symbol_filter = TickerDataModel(symbol=symbol)
        return self.get_one(symbol_filter)

    def bulk_insert_tickers(self, tickers: list[TickerDataModel]) -> int:
        """Bulk insert tickers using base repository."""
        return self.insert_many(tickers)

    def get_all_tickers(self) -> list[TickerDataModel]:
        """Retrieve all tickers from the database using base repository."""
        return self.get_filter()  # Uses base repository get_filter() method

    def create_ticker_for_company(
        self, symbol: str, company_id: int, ticker_history_id: int
    ) -> TickerDataModel:
        """Create a new ticker for a company using base repository.

        Args:
            symbol: Ticker symbol
            company_id: ID of the company
            ticker_history_id: ID of the ticker_history record (required FK)

        Returns:
            Created TickerDataModel with database ID

        Raises:
            ValueError: If ticker_history_id is None when converting to DB model
        """
        ticker_data = TickerDataModel(
            symbol=symbol, company_id=company_id, ticker_history_id=ticker_history_id
        )
        return self.insert(ticker_data)

