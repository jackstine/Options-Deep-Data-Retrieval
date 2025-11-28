"""Ticker history service for cross-repository operations."""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.database.equities.tables.company import Company as CompanyDBModel
from src.database.equities.tables.ticker_history import (
    TickerHistory as TickerHistoryDBModel,
)
from src.models.company import Company
from src.models.ticker_history import TickerHistory
from src.models.ticker_history_with_company import TickerHistoryWithCompanyDataModel
from src.repos.equities.companies.company_repository import CompanyRepository
from src.repos.equities.tickers.ticker_history_repository import (
    TickerHistoryRepository,
)

logger = logging.getLogger(__name__)


class TickerHistoryService:
    """Service layer for ticker history operations involving multiple repositories."""

    def __init__(
        self,
        ticker_history_repository: TickerHistoryRepository,
        company_repository: CompanyRepository,
    ) -> None:
        """Initialize ticker history service with required repositories.

        Args:
            ticker_history_repository: Repository for ticker history operations
            company_repository: Repository for company operations
        """
        self._ticker_history_repo = ticker_history_repository
        self._company_repo = company_repository

    def get_active_ticker_history_symbols(self) -> set[str]:
        """Get all currently active ticker symbols from ticker history.

        Filters by:
        - Date validity (valid_from <= today <= valid_to or valid_to is None)
        - Company active status (via join with companies table)

        Returns:
            Set of currently active ticker symbols
        """
        try:
            with self._ticker_history_repo._SessionLocal() as session:
                today = date.today()
                result = session.execute(
                    select(TickerHistoryDBModel.symbol)
                    .join(CompanyDBModel, TickerHistoryDBModel.company_id == CompanyDBModel.id)
                    .where(
                        (TickerHistoryDBModel.valid_from <= today)
                        & (
                            (TickerHistoryDBModel.valid_to.is_(None))
                            | (TickerHistoryDBModel.valid_to >= today)
                        )
                        & CompanyDBModel.active
                    )
                )
                symbols = {row[0] for row in result.fetchall()}
                logger.info(
                    f"Retrieved {len(symbols)} active ticker history symbols from database"
                )
                return symbols

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving active ticker history symbols: {e}"
            )
            raise

    def get_active_ticker_histories(self) -> list[TickerHistoryWithCompanyDataModel]:
        """Get all active ticker history records enriched with company data.

        Returns ticker histories where the associated company is active,
        enriched with company information.

        Returns:
            List of ticker history records with company data
        """
        try:
            with self._ticker_history_repo._SessionLocal() as session:
                result = session.execute(
                    select(TickerHistoryDBModel, CompanyDBModel)
                    .join(CompanyDBModel, TickerHistoryDBModel.company_id == CompanyDBModel.id)
                    .where(CompanyDBModel.active)
                )
                rows = result.all()

                enriched_histories: list[TickerHistoryWithCompanyDataModel] = []
                for ticker_history_db, company_db in rows:
                    # Convert DB models to data models
                    ticker_history = TickerHistoryRepository.from_db_model(ticker_history_db)
                    company = CompanyRepository.from_db_model(company_db)

                    enriched_histories.append(
                        TickerHistoryWithCompanyDataModel(
                            ticker_history=ticker_history,
                            company=company,
                        )
                    )

                logger.info(
                    f"Retrieved {len(enriched_histories)} active ticker histories with company data"
                )
                return enriched_histories

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving active ticker histories: {e}")
            raise
