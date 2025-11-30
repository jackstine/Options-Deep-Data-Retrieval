"""Company repository for database operations."""

from __future__ import annotations

import logging

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

    @staticmethod
    def from_db_model(db_model: CompanyTable) -> CompanyDataModel:
        """Create data model from SQLAlchemy database model.

        Args:
            db_model: SQLAlchemy Company instance from database

        Returns:
            Company: Data model instance
        """
        return CompanyDataModel(
            id=db_model.id,
            company_name=db_model.company_name,
            exchange=db_model.exchange,
            sector=db_model.sector,
            industry=db_model.industry,
            country=db_model.country,
            market_cap=db_model.market_cap,
            description=db_model.description,
            active=db_model.active,
            is_valid_data=db_model.is_valid_data,
            source=db_model.source,  # Already a DataSourceEnum from DB
        )

    @staticmethod
    def to_db_model(data_model: CompanyDataModel) -> CompanyTable:
        """Convert data model to SQLAlchemy database model.

        Args:
            data_model: Company data model instance

        Returns:
            DBCompany: SQLAlchemy model instance ready for database operations
        """
        return CompanyTable(
            company_name=data_model.company_name,
            exchange=data_model.exchange,
            sector=data_model.sector,
            industry=data_model.industry,
            country=data_model.country,
            market_cap=data_model.market_cap,
            description=data_model.description,
            active=data_model.active,
            is_valid_data=data_model.is_valid_data,
            source=data_model.source,
        )

    def get_all_companies(self) -> list[CompanyDataModel]:
        """Retrieve all companies from the database using base repository."""
        return self.get_filter()  # Uses base repository get_filter() method

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
        for original, inserted in zip(companies, inserted_companies, strict=False):
            original.id = inserted.id

        return inserted_companies

