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

    def _create_id_filter(self, id: int) -> CompanyDataModel:
        """Create a Company filter model for ID lookups."""
        return CompanyDataModel(
            company_name="",  # Will be ignored
            exchange="",  # Will be ignored
            id=id,  # Will be used as filter
        )

    # Domain-specific methods using base repository functionality
    def get_all_companies(self) -> list[CompanyDataModel]:
        """Retrieve all companies from the database using base repository."""
        return self.get()  # Uses base repository get() method

    def get_active_companies(self) -> list[CompanyDataModel]:
        """Retrieve all active companies using base repository filtering."""
        active_filter = CompanyDataModel(active=True, company_name="", exchange="")
        return self.get(active_filter)

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

