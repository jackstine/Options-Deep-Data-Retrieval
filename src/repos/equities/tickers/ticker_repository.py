"""Ticker repository for database operations."""

from __future__ import annotations
import logging
from typing import List, Set, Optional
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from src.config.configuration import CONFIG
from src.data_sources.models.ticker import Ticker as TickerDataModel
from src.database.equities.tables.ticker import Ticker as TickerDBModel


logger = logging.getLogger(__name__)


class TickerRepository:
    """Repository for ticker database operations."""
    
    def __init__(self) -> None:
        """Initialize ticker repository with database connection."""
        self._equities_config = CONFIG.get_equities_config()
        self._engine = create_engine(self._equities_config.database.get_connection_string())
        self._SessionLocal = sessionmaker(bind=self._engine)
    
    def get_active_ticker_symbols(self) -> Set[str]:
        """
        Get all ticker symbols from the database.
        
        Returns:
            Set of ticker symbols
        """
        try:
            with self._SessionLocal() as session:
                result = session.execute(
                    select(TickerDBModel.symbol)
                )
                symbols = {row[0] for row in result.fetchall()}
                logger.info(f"Retrieved {len(symbols)} ticker symbols from database")
                return symbols
                
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving ticker symbols: {e}")
            raise
    
    def get_tickers_for_company(self, company_id: int) -> List[TickerDataModel]:
        """
        Get all tickers for a specific company.
        
        Args:
            company_id: Company ID to get tickers for
            
        Returns:
            List of ticker data models for the company
        """
        try:
            with self._SessionLocal() as session:
                result = session.execute(
                    select(TickerDBModel)
                    .where(TickerDBModel.company_id == company_id)
                )
                db_tickers = result.scalars().all()
                tickers = [ticker.to_data_model() for ticker in db_tickers]
                logger.info(f"Retrieved {len(tickers)} tickers for company {company_id}")
                return tickers
                
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving tickers for company {company_id}: {e}")
            raise
    
    def get_ticker_by_symbol(self, symbol: str) -> Optional[TickerDataModel]:
        """
        Get ticker by symbol.
        
        Args:
            symbol: Ticker symbol to search for
            
        Returns:
            TickerDataModel if found, None otherwise
        """
        try:
            with self._SessionLocal() as session:
                result = session.execute(
                    select(TickerDBModel)
                    .where(TickerDBModel.symbol == symbol)
                )
                db_ticker = result.scalar_one_or_none()
                
                if db_ticker:
                    ticker = db_ticker.to_data_model()
                    logger.debug(f"Found ticker {symbol}")
                    return ticker
                else:
                    logger.debug(f"No ticker found for symbol {symbol}")
                    return None
                    
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving ticker {symbol}: {e}")
            raise
    
    def bulk_insert_tickers(self, tickers: List[TickerDataModel]) -> int:
        """
        Insert multiple tickers into the database in bulk.
        
        Args:
            tickers: List of ticker data models to insert
            
        Returns:
            Number of tickers successfully inserted
        """
        if not tickers:
            logger.info("No tickers to insert")
            return 0
            
        try:
            with self._SessionLocal() as session:
                db_tickers = [TickerDBModel.from_data_model(ticker) for ticker in tickers]
                session.add_all(db_tickers)
                session.commit()
                
                logger.info(f"Successfully inserted {len(db_tickers)} tickers")
                return len(db_tickers)
                
        except SQLAlchemyError as e:
            logger.error(f"Database error during bulk ticker insert: {e}")
            raise
    
    def create_ticker_for_company(self, symbol: str, company_id: int) -> TickerDataModel:
        """
        Create a new ticker for a company.
        
        Args:
            symbol: Ticker symbol
            company_id: Company ID this ticker belongs to
            
        Returns:
            Created ticker data model
        """
        ticker_data = TickerDataModel(
            symbol=symbol,
            company_id=company_id
        )
        
        try:
            with self._SessionLocal() as session:
                db_ticker = TickerDBModel.from_data_model(ticker_data)
                session.add(db_ticker)
                session.commit()
                session.refresh(db_ticker)
                
                created_ticker = db_ticker.to_data_model()
                logger.info(f"Created ticker {symbol} for company {company_id}")
                return created_ticker
                
        except SQLAlchemyError as e:
            logger.error(f"Database error creating ticker {symbol}: {e}")
            raise
    
    def delete_ticker(self, symbol: str) -> bool:
        """
        Delete a ticker symbol.
        
        Args:
            symbol: Ticker symbol to delete
            
        Returns:
            True if ticker was deleted, False if not found
        """
        try:
            with self._SessionLocal() as session:
                result = session.execute(
                    select(TickerDBModel)
                    .where(TickerDBModel.symbol == symbol)
                )
                db_ticker = result.scalar_one_or_none()
                
                if db_ticker:
                    session.delete(db_ticker)
                    session.commit()
                    logger.info(f"Deleted ticker {symbol}")
                    return True
                else:
                    logger.warning(f"No ticker found to delete: {symbol}")
                    return False
                    
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting ticker {symbol}: {e}")
            raise
    
    def update_ticker_company(self, symbol: str, new_company_id: int) -> bool:
        """
        Update the company_id for a ticker symbol.
        
        Args:
            symbol: Ticker symbol to update
            new_company_id: New company ID to assign
            
        Returns:
            True if ticker was updated, False if not found
        """
        try:
            with self._SessionLocal() as session:
                result = session.execute(
                    select(TickerDBModel)
                    .where(TickerDBModel.symbol == symbol)
                )
                db_ticker = result.scalar_one_or_none()
                
                if db_ticker:
                    db_ticker.company_id = new_company_id
                    session.commit()
                    logger.info(f"Updated ticker {symbol} to company {new_company_id}")
                    return True
                else:
                    logger.warning(f"No ticker found to update: {symbol}")
                    return False
                    
        except SQLAlchemyError as e:
            logger.error(f"Database error updating ticker {symbol}: {e}")
            raise