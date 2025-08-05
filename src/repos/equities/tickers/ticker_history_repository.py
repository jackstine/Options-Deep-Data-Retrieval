"""TickerHistory repository for database operations."""

from __future__ import annotations
import logging
from datetime import date
from typing import List, Set, Optional
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from src.config.configuration import CONFIG
from src.data_sources.models.ticker_history import TickerHistory as TickerHistoryDataModel
from src.database.equities.tables.ticker_history import TickerHistory as TickerHistoryDBModel


logger = logging.getLogger(__name__)


class TickerHistoryRepository:
    """Repository for ticker history database operations."""
    
    def __init__(self) -> None:
        """Initialize ticker history repository with database connection."""
        self._equities_config = CONFIG.get_equities_config()
        self._engine = create_engine(self._equities_config.database.get_connection_string())
        self._SessionLocal = sessionmaker(bind=self._engine)
    
    def get_active_ticker_history_symbols(self) -> Set[str]:
        """
        Get all currently active ticker symbols from ticker history.
        
        Returns:
            Set of currently active ticker symbols
        """
        try:
            with self._SessionLocal() as session:
                today = date.today()
                result = session.execute(
                    select(TickerHistoryDBModel.symbol)
                    .where(
                        (TickerHistoryDBModel.valid_from <= today) &
                        ((TickerHistoryDBModel.valid_to.is_(None)) | (TickerHistoryDBModel.valid_to >= today)) &
                        (TickerHistoryDBModel.active == True)
                    )
                )
                symbols = {row[0] for row in result.fetchall()}
                logger.info(f"Retrieved {len(symbols)} active ticker history symbols from database")
                return symbols
                
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving active ticker history symbols: {e}")
            raise
    
    def get_ticker_history_for_company(self, company_id: int) -> List[TickerHistoryDataModel]:
        """
        Get all ticker history records for a specific company.
        
        Args:
            company_id: Company ID to get ticker history for
            
        Returns:
            List of ticker history data models for the company
        """
        try:
            with self._SessionLocal() as session:
                result = session.execute(
                    select(TickerHistoryDBModel)
                    .where(TickerHistoryDBModel.company_id == company_id)
                    .order_by(TickerHistoryDBModel.valid_from)
                )
                db_ticker_histories = result.scalars().all()
                ticker_histories = [th.to_data_model() for th in db_ticker_histories]
                logger.info(f"Retrieved {len(ticker_histories)} ticker history records for company {company_id}")
                return ticker_histories
                
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving ticker history for company {company_id}: {e}")
            raise
    
    def get_ticker_history_by_symbol(self, symbol: str) -> List[TickerHistoryDataModel]:
        """
        Get all ticker history records for a symbol.
        
        Args:
            symbol: Ticker symbol to search for
            
        Returns:
            List of ticker history data models for the symbol
        """
        try:
            with self._SessionLocal() as session:
                result = session.execute(
                    select(TickerHistoryDBModel)
                    .where(TickerHistoryDBModel.symbol == symbol)
                    .order_by(TickerHistoryDBModel.valid_from)
                )
                db_ticker_histories = result.scalars().all()
                ticker_histories = [th.to_data_model() for th in db_ticker_histories]
                logger.debug(f"Found {len(ticker_histories)} ticker history records for symbol {symbol}")
                return ticker_histories
                
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving ticker history for symbol {symbol}: {e}")
            raise
    
    def bulk_insert_ticker_histories(self, ticker_histories: List[TickerHistoryDataModel]) -> int:
        """
        Insert multiple ticker history records into the database in bulk.
        
        Args:
            ticker_histories: List of ticker history data models to insert
            
        Returns:
            Number of ticker history records successfully inserted
        """
        if not ticker_histories:
            logger.info("No ticker histories to insert")
            return 0
            
        try:
            with self._SessionLocal() as session:
                db_ticker_histories = [TickerHistoryDBModel.from_data_model(th) for th in ticker_histories]
                session.add_all(db_ticker_histories)
                session.commit()
                
                logger.info(f"Successfully inserted {len(db_ticker_histories)} ticker history records")
                return len(db_ticker_histories)
                
        except SQLAlchemyError as e:
            logger.error(f"Database error during bulk ticker history insert: {e}")
            raise
    
    def create_ticker_history_for_company(self, symbol: str, company_id: int, 
                                        valid_from: date = None, 
                                        valid_to: Optional[date] = None,
                                        active: bool = True) -> TickerHistoryDataModel:
        """
        Create a new ticker history record for a company.
        
        Args:
            symbol: Ticker symbol
            company_id: Company ID this ticker belongs to
            valid_from: Date from which ticker is valid (defaults to today)
            valid_to: Date until which ticker is valid (None for indefinite)
            active: Whether the ticker is active
            
        Returns:
            Created ticker history data model
        """
        if valid_from is None:
            valid_from = date.today()
            
        ticker_history_data = TickerHistoryDataModel(
            symbol=symbol,
            company_id=company_id,
            valid_from=valid_from,
            valid_to=valid_to,
            active=active
        )
        
        try:
            with self._SessionLocal() as session:
                db_ticker_history = TickerHistoryDBModel.from_data_model(ticker_history_data)
                session.add(db_ticker_history)
                session.commit()
                session.refresh(db_ticker_history)
                
                created_ticker_history = db_ticker_history.to_data_model()
                logger.info(f"Created ticker history {symbol} for company {company_id}")
                return created_ticker_history
                
        except SQLAlchemyError as e:
            logger.error(f"Database error creating ticker history {symbol}: {e}")
            raise
    
    def update_ticker_history_validity(self, symbol: str, company_id: int, 
                                     new_valid_to: date) -> bool:
        """
        Update the valid_to date for an active ticker history record.
        
        Args:
            symbol: Ticker symbol
            company_id: Company ID
            new_valid_to: New valid_to date
            
        Returns:
            True if ticker history was updated, False if not found
        """
        try:
            with self._SessionLocal() as session:
                result = session.execute(
                    select(TickerHistoryDBModel)
                    .where(
                        (TickerHistoryDBModel.symbol == symbol) &
                        (TickerHistoryDBModel.company_id == company_id) &
                        (TickerHistoryDBModel.valid_to.is_(None))
                    )
                )
                db_ticker_history = result.scalar_one_or_none()
                
                if db_ticker_history:
                    db_ticker_history.valid_to = new_valid_to
                    session.commit()
                    logger.info(f"Updated ticker history {symbol} valid_to to {new_valid_to}")
                    return True
                else:
                    logger.warning(f"No active ticker history found to update: {symbol}")
                    return False
                    
        except SQLAlchemyError as e:
            logger.error(f"Database error updating ticker history {symbol}: {e}")
            raise
    
    def deactivate_ticker_history(self, symbol: str, company_id: int, 
                                end_date: date = None) -> bool:
        """
        Deactivate a ticker history record by setting valid_to and active=False.
        
        Args:
            symbol: Ticker symbol to deactivate
            company_id: Company ID
            end_date: Date to end validity (defaults to today)
            
        Returns:
            True if ticker history was deactivated, False if not found
        """
        if end_date is None:
            end_date = date.today()
            
        try:
            with self._SessionLocal() as session:
                result = session.execute(
                    select(TickerHistoryDBModel)
                    .where(
                        (TickerHistoryDBModel.symbol == symbol) &
                        (TickerHistoryDBModel.company_id == company_id) &
                        (TickerHistoryDBModel.valid_to.is_(None))
                    )
                )
                db_ticker_history = result.scalar_one_or_none()
                
                if db_ticker_history:
                    db_ticker_history.valid_to = end_date
                    db_ticker_history.active = False
                    session.commit()
                    logger.info(f"Deactivated ticker history {symbol} on {end_date}")
                    return True
                else:
                    logger.warning(f"No active ticker history found to deactivate: {symbol}")
                    return False
                    
        except SQLAlchemyError as e:
            logger.error(f"Database error deactivating ticker history {symbol}: {e}")
            raise