"""Company repository for database operations."""

from __future__ import annotations
import logging
from typing import List, Optional, Set
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from src.config.configuration import CONFIG
from src.database.equities.tables.company import Company as CompanyTable
from src.data_sources.models.company import Company as CompanyDataModel


logger = logging.getLogger(__name__)


class CompanyRepository:
    """Repository for company database operations."""
    
    def __init__(self) -> None:
        """Initialize company repository."""
        self._equities_config = CONFIG.get_equities_config()
        self._engine = create_engine(self._equities_config.database.get_connection_string())
        self._SessionLocal = sessionmaker(bind=self._engine)
    
    def get_active_company_symbols(self) -> Set[str]:
        """
        Retrieve all active company symbols from the database.
        
        Returns:
            Set of ticker symbols for active companies
            
        Raises:
            SQLAlchemyError: If database connection or query fails
        """
        try:
            with self._SessionLocal() as session:
                # Query for active company symbols
                result = session.execute(
                    select(CompanyTable.ticker).where(CompanyTable.active == True)
                )
                
                active_symbols = {row[0] for row in result.fetchall()}
                
                logger.info(f"Retrieved {len(active_symbols)} active company symbols from database")
                return active_symbols
                
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving active symbols: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving active company symbols: {e}")
            raise
    
    def get_all_companies(self) -> List[CompanyDataModel]:
        """
        Retrieve all companies from the database.
        
        Returns:
            List of CompanyDataModel objects
            
        Raises:
            SQLAlchemyError: If database connection or query fails
        """
        try:
            with self._SessionLocal() as session:
                result = session.execute(select(CompanyTable))
                companies = [row[0].to_data_model() for row in result.fetchall()]
                
                logger.info(f"Retrieved {len(companies)} companies from database")
                return companies
                
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving companies: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving companies: {e}")
            raise
    
    def get_active_companies(self) -> List[CompanyDataModel]:
        """
        Retrieve all active companies from the database.
        
        Returns:
            List of active CompanyDataModel objects
            
        Raises:
            SQLAlchemyError: If database connection or query fails
        """
        try:
            with self._SessionLocal() as session:
                result = session.execute(
                    select(CompanyTable).where(CompanyTable.active == True)
                )
                companies = [row[0].to_data_model() for row in result.fetchall()]
                
                logger.info(f"Retrieved {len(companies)} active companies from database")
                return companies
                
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving active companies: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving active companies: {e}")
            raise
    
    def get_company_by_ticker(self, ticker: str) -> Optional[CompanyDataModel]:
        """
        Retrieve a company by ticker symbol.
        
        Args:
            ticker: Ticker symbol to search for
            
        Returns:
            CompanyDataModel if found, None otherwise
            
        Raises:
            SQLAlchemyError: If database connection or query fails
        """
        try:
            with self._SessionLocal() as session:
                result = session.execute(
                    select(CompanyTable).where(CompanyTable.ticker == ticker.upper())
                )
                company_row = result.fetchone()
                
                if company_row:
                    return company_row[0].to_data_model()
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving company {ticker}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving company {ticker}: {e}")
            raise
    
    def bulk_insert_companies(self, companies: List[CompanyDataModel]) -> int:
        """
        Bulk insert companies into the database.
        
        Args:
            companies: List of CompanyDataModel objects to insert
            
        Returns:
            Number of companies successfully inserted
            
        Raises:
            SQLAlchemyError: If bulk insert fails
        """
        if not companies:
            logger.info("No companies to insert")
            return 0
        
        try:
            with self._SessionLocal() as session:
                # Convert data models to SQLAlchemy models
                db_companies = [
                    CompanyTable.from_data_model(company) 
                    for company in companies
                ]
                
                # Bulk insert
                session.add_all(db_companies)
                session.commit()
                
                inserted_count = len(db_companies)
                logger.info(f"Successfully inserted {inserted_count} companies into database")
                
                return inserted_count
                
        except SQLAlchemyError as e:
            logger.error(f"Database error during bulk insert: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during bulk insert: {e}")
            raise
    
    def update_company(self, ticker: str, company_data: CompanyDataModel) -> bool:
        """
        Update an existing company in the database.
        
        Args:
            ticker: Ticker symbol of company to update
            company_data: Updated company data
            
        Returns:
            True if company was updated, False if not found
            
        Raises:
            SQLAlchemyError: If database update fails
        """
        try:
            with self._SessionLocal() as session:
                result = session.execute(
                    select(CompanyTable).where(CompanyTable.ticker == ticker.upper())
                )
                company_row = result.fetchone()
                
                if company_row:
                    company = company_row[0]
                    company.update_from_data_model(company_data)
                    session.commit()
                    logger.info(f"Updated company {ticker}")
                    return True
                else:
                    logger.warning(f"Company {ticker} not found for update")
                    return False
                
        except SQLAlchemyError as e:
            logger.error(f"Database error updating company {ticker}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating company {ticker}: {e}")
            raise
    
    def deactivate_company(self, ticker: str) -> bool:
        """
        Mark a company as inactive in the database.
        
        Args:
            ticker: Ticker symbol of company to deactivate
            
        Returns:
            True if company was deactivated, False if not found
            
        Raises:
            SQLAlchemyError: If database update fails
        """
        try:
            with self._SessionLocal() as session:
                result = session.execute(
                    select(CompanyTable).where(CompanyTable.ticker == ticker.upper())
                )
                company_row = result.fetchone()
                
                if company_row:
                    company = company_row[0]
                    company.active = False
                    session.commit()
                    logger.info(f"Deactivated company {ticker}")
                    return True
                else:
                    logger.warning(f"Company {ticker} not found for deactivation")
                    return False
                
        except SQLAlchemyError as e:
            logger.error(f"Database error deactivating company {ticker}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error deactivating company {ticker}: {e}")
            raise