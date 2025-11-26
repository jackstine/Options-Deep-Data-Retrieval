"""Company service for cross-repository operations."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.database.equities.tables.company import Company as CompanyTable
from src.database.equities.tables.ticker import Ticker as TickerTable
from src.database.equities.tables.ticker_history import (
    TickerHistory as TickerHistoryTable,
)
from src.models.company import Company as CompanyDataModel
from src.models.company_with_ticker import CompanyWithTickerDataModel
from src.models.ticker_history import TickerHistory
from src.repos.equities.companies.company_repository import CompanyRepository
from src.repos.equities.tickers.ticker_history_repository import (
    TickerHistoryRepository,
)

logger = logging.getLogger(__name__)


class CompanyService:
    """Service layer for company operations involving multiple repositories."""

    def __init__(
        self,
        company_repository: CompanyRepository,
        ticker_history_repository: TickerHistoryRepository,
    ) -> None:
        """Initialize company service with required repositories.

        Args:
            company_repository: Repository for company operations
            ticker_history_repository: Repository for ticker history operations
        """
        self._company_repo = company_repository
        self._ticker_history_repo = ticker_history_repository

    def get_active_company_symbols(self) -> set[str]:
        """Get set of active company ticker symbols.

        Joins companies with tickers to retrieve symbols for active companies.

        Returns:
            Set of active company ticker symbols
        """
        try:
            with self._company_repo._SessionLocal() as session:
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

    def get_company_by_ticker(self, ticker: str) -> CompanyWithTickerDataModel | None:
        """Get company with ticker information by ticker symbol.

        Joins companies with ticker_history to find companies associated with
        the given ticker symbol (active or delisted) and enriches the result
        with ticker information.

        Args:
            ticker: Ticker symbol to search for

        Returns:
            Company data enriched with ticker info, or None if not found
        """
        try:
            with self._company_repo._SessionLocal() as session:
                # Join Company with TickerHistory and filter by symbol
                result = session.execute(
                    select(CompanyTable, TickerHistoryTable)
                    .join(
                        TickerHistoryTable,
                        CompanyTable.id == TickerHistoryTable.company_id,
                    )
                    .where(TickerHistoryTable.symbol == ticker.upper())
                    .limit(1)
                )

                row = result.first()

                if row:
                    company_db, ticker_history_db = row

                    # Convert DB models to data models
                    company = CompanyDataModel.from_db_model(company_db)
                    ticker_history = TickerHistory.from_db_model(ticker_history_db)

                    return CompanyWithTickerDataModel(
                        company=company,
                        ticker_history=ticker_history,
                    )
                return None

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving company by ticker {ticker}: {e}")
            raise

    def update_company(self, ticker: str, company_data: CompanyDataModel) -> bool:
        """Update company by ticker symbol.

        Uses join to find company by ticker, then updates via repository.

        Args:
            ticker: Ticker symbol to find the company
            company_data: Company data to update

        Returns:
            True if company was updated, False otherwise
        """
        # Use service method to get company (performs join)
        existing_company_data = self.get_company_by_ticker(ticker)
        if not existing_company_data:
            return False

        company_id = existing_company_data.company.id
        if not company_id:
            return False

        # Update by ID using repository
        return self._company_repo.update_by_id(company_id, company_data)

    def deactivate_company(self, ticker: str) -> bool:
        """Deactivate company by ticker symbol.

        Uses join to find company by ticker, then deactivates via repository.

        Args:
            ticker: Ticker symbol to find the company

        Returns:
            True if company was deactivated, False otherwise
        """
        # Use service method to get company (performs join)
        existing_company_data = self.get_company_by_ticker(ticker)
        if not existing_company_data:
            return False

        company_id = existing_company_data.company.id
        if not company_id:
            return False

        # Create deactivation data and update by ID
        deactivate_data = CompanyDataModel(active=False, company_name="", exchange="")
        return self._company_repo.update_by_id(company_id, deactivate_data)
