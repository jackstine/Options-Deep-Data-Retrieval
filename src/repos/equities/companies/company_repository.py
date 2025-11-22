"""Company repository for database operations."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.config.configuration import CONFIG
from src.database.equities.tables.company import Company as CompanyTable
from src.models.company import Company as CompanyDataModel
from src.repos.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class CompanyRepository(BaseRepository[CompanyDataModel, CompanyTable]):
    """Repository for company database operations."""

    def __init__(self) -> None:
        """Initialize company repository."""
        super().__init__(
            config_getter=CONFIG.get_equities_config,
            data_model_class=CompanyDataModel,
            db_model_class=CompanyTable,
        )

    def _create_id_filter(self, id: int) -> CompanyDataModel:
        """Create a Company filter model for ID lookups."""
        return CompanyDataModel(
            company_name="",  # Will be ignored
            exchange="",  # Will be ignored
            id=id,  # Will be used as filter
        )

    # Domain-specific methods using base repository functionality
    def get_active_company_symbols(self) -> set[str]:
        """Get set of active company ticker symbols."""
        try:
            with self._SessionLocal() as session:
                from src.database.equities.tables.ticker import Ticker as TickerTable

                # Query for active company symbols by joining with ticker table
                result = session.execute(
                    select(TickerTable.symbol)
                    .join(CompanyTable, TickerTable.company_id == CompanyTable.id)
                    .where(CompanyTable.active)
                )

                active_symbols = {row[0] for row in result.fetchall()}

                logger.info(
                    f"Retrieved {len(active_symbols)} active company symbols from database"
                )
                return active_symbols

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving active symbols: {e}")
            raise

    def get_all_companies(self) -> list[CompanyDataModel]:
        """Retrieve all companies from the database using base repository."""
        return self.get()  # Uses base repository get() method

    def get_active_companies(self) -> list[CompanyDataModel]:
        """Retrieve all active companies using base repository filtering."""
        active_filter = CompanyDataModel(active=True, company_name="", exchange="")
        return self.get(active_filter)

    def get_company_by_ticker(self, ticker: str) -> CompanyDataModel | None:
        """Get company by ticker symbol.

        Queries by joining with ticker_history table to find companies
        associated with the given ticker symbol (active or delisted).

        Args:
            ticker: Ticker symbol to search for

        Returns:
            Company data model or None if not found
        """
        try:
            with self._SessionLocal() as session:
                from src.database.equities.tables.ticker_history import (
                    TickerHistory as TickerHistoryTable,
                )

                # Join Company with TickerHistory and filter by symbol
                result = session.execute(
                    select(CompanyTable)
                    .join(TickerHistoryTable, CompanyTable.id == TickerHistoryTable.company_id)
                    .where(TickerHistoryTable.symbol == ticker.upper())
                    .limit(1)
                )

                db_model = result.scalar_one_or_none()

                if db_model:
                    return CompanyDataModel.from_db_model(db_model)
                return None

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving company by ticker {ticker}: {e}")
            raise

    def bulk_insert_companies(self, companies: list[CompanyDataModel]) -> list[CompanyDataModel]:
        """Bulk insert companies and return them with populated IDs.

        Also updates the input companies list with database-generated IDs,
        preserving any additional fields (like ticker) from the data source.

        Args:
            companies: List of company data models to insert

        Returns:
            List of company data models with populated IDs and timestamps
        """
        inserted_companies = self.insert_many_returning(companies)

        # Update original companies with database-generated IDs
        # This preserves ticker info from data source while adding IDs from DB
        for original, inserted in zip(companies, inserted_companies):
            original.id = inserted.id

        return inserted_companies

    def update_company(self, ticker: str, company_data: CompanyDataModel) -> bool:
        """Update company by ticker symbol.

        Args:
            ticker: Ticker symbol to find the company
            company_data: Company data to update

        Returns:
            True if company was updated, False otherwise
        """
        # First find the company by ticker to get its ID
        existing_company = self.get_company_by_ticker(ticker)
        if not existing_company or not existing_company.id:
            return False

        # Update by ID
        return self.update_by_id(existing_company.id, company_data)

    def deactivate_company(self, ticker: str) -> bool:
        """Deactivate company by ticker symbol.

        Args:
            ticker: Ticker symbol to find the company

        Returns:
            True if company was deactivated, False otherwise
        """
        # First find the company by ticker to get its ID
        existing_company = self.get_company_by_ticker(ticker)
        if not existing_company or not existing_company.id:
            return False

        # Update by ID
        deactivate_data = CompanyDataModel(active=False, company_name="", exchange="")
        return self.update_by_id(existing_company.id, deactivate_data)
