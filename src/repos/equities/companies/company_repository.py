"""Company repository for database operations."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.config.configuration import CONFIG
from src.models.company import Company as CompanyDataModel
from src.models.ticker import Ticker
from src.database.equities.tables.company import Company as CompanyTable
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
                    .where(CompanyTable.active == True)
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
        """Get company by ticker symbol using base repository."""
        ticker_filter = CompanyDataModel(
            ticker=Ticker(symbol=ticker.upper()), company_name="", exchange=""
        )
        return self.get_one(ticker_filter)

    def bulk_insert_companies(self, companies: list[CompanyDataModel]) -> int:
        """Bulk insert companies using base repository."""
        return self.insert_many(companies)

    def update_company(self, ticker: str, company_data: CompanyDataModel) -> bool:
        """Update company by ticker using base repository."""
        ticker_filter = CompanyDataModel(
            ticker=Ticker(symbol=ticker.upper()), company_name="", exchange=""
        )
        return self.update(ticker_filter, company_data) > 0

    def deactivate_company(self, ticker: str) -> bool:
        """Deactivate company using base repository update."""
        ticker_filter = CompanyDataModel(
            ticker=Ticker(symbol=ticker.upper()), company_name="", exchange=""
        )
        deactivate_data = CompanyDataModel(active=False, company_name="", exchange="")
        return self.update(ticker_filter, deactivate_data) > 0
