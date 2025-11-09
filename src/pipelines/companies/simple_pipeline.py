"""Company ingestion pipeline."""

from __future__ import annotations

import logging
from datetime import date

from src.data_sources.base.company_data_source import CompanyDataSource
from src.models.company import Company
from src.models.ticker import Ticker as TickerDataModel
from src.models.ticker_history import (
    TickerHistory as TickerHistoryDataModel,
)
from src.repos.equities.companies.company_repository import CompanyRepository
from src.repos.equities.tickers.ticker_history_repository import TickerHistoryRepository
from src.repos.equities.tickers.ticker_repository import TickerRepository


class CompanyPipeline:
    """Company ingestion pipeline with comprehensive database synchronization."""

    def __init__(
        self,
        company_repo: CompanyRepository | None = None,
        ticker_repo: TickerRepository | None = None,
        ticker_history_repo: TickerHistoryRepository | None = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize the pipeline with repositories and logger."""
        self.company_repo = company_repo or CompanyRepository()
        self.ticker_repo = ticker_repo or TickerRepository()
        self.ticker_history_repo = ticker_history_repo or TickerHistoryRepository()
        self.logger = logger or logging.getLogger(__name__)

    def run_ingestion(self, sources: list[CompanyDataSource]) -> dict[str, int]:
        """Run ingestion from the given data sources.

        Args:
            sources: List of data sources to get companies from

        Returns:
            Dictionary with results: {
                "inserted": 5,
                "updated": 3,
                "skipped": 2,
                "errors": 0,
                "tickers_inserted": 5,
                "ticker_histories_inserted": 5
            }
        """
        results = {
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "tickers_inserted": 0,
            "ticker_histories_inserted": 0,
        }
        all_companies = []

        # Step 1: Get companies from all sources
        for source in sources:
            try:
                if not source.is_available():
                    self.logger.warning(f"Source {source.name} is not available")
                    continue

                self.logger.info(f"Getting companies from {source.name}")
                companies = source.get_companies()

                # Add source info to each company (if the company model supports it)
                for company in companies:
                    if hasattr(company, "source"):
                        company.source = source.name

                all_companies.extend(companies)
                self.logger.info(f"Got {len(companies)} companies from {source.name}")

            except Exception as e:
                self.logger.error(f"Error getting companies from {source.name}: {e}")
                results["errors"] += 1

        if not all_companies:
            self.logger.warning("No companies found from any source")
            return results

        # Step 2: Clean and validate data
        clean_companies = self._clean_companies(all_companies)

        # Step 3: Comprehensive database synchronization
        sync_results = self._comprehensive_sync_to_database(clean_companies)
        results.update(sync_results)

        return results

    def run_comprehensive_sync(
        self, sources: list[CompanyDataSource]
    ) -> dict[str, int | set[str]]:
        """Run comprehensive synchronization including unused ticker detection.

        Args:
            sources: List of data sources to get companies from

        Returns:
            Dictionary with comprehensive results including unused tickers
        """
        # First run normal ingestion
        results: dict[str, int | set[str]] = dict(self.run_ingestion(sources))

        # Add unused ticker detection
        inserted_count = results.get("inserted", 0)
        updated_count = results.get("updated", 0)
        if (isinstance(inserted_count, int) and inserted_count > 0) or (
            isinstance(updated_count, int) and updated_count > 0
        ):
            try:
                # Get screener symbols from sources
                screener_symbols = set()
                for source in sources:
                    if source.is_available():
                        companies = source.get_companies()
                        for company in companies:
                            if company.ticker and company.ticker.symbol:
                                screener_symbols.add(company.ticker.symbol)

                # Find unused tickers
                unused_tickers = self._get_unused_tickers(screener_symbols)
                results["unused_tickers"] = unused_tickers
                results["unused_ticker_count"] = len(unused_tickers)

                if unused_tickers:
                    self.logger.info(f"Found {len(unused_tickers)} unused tickers:")
                    for ticker in sorted(list(unused_tickers)[:10]):  # Show first 10
                        self.logger.info(f"  - {ticker}")

            except Exception as e:
                self.logger.error(f"Error detecting unused tickers: {e}")

        return results

    def _clean_companies(self, companies: list[Company]) -> list[Company]:
        """Basic data cleaning - remove duplicates and invalid companies."""
        clean_companies = []
        seen_tickers = set()

        for company in companies:
            # Skip if no ticker
            if not company.ticker or not company.ticker.symbol:
                continue

            ticker = company.ticker.symbol.upper()

            # Skip duplicates (keep first occurrence)
            if ticker in seen_tickers:
                continue

            seen_tickers.add(ticker)

            # Basic cleaning
            if company.company_name:
                company.company_name = company.company_name.strip()
            if company.exchange:
                company.exchange = company.exchange.upper()

            clean_companies.append(company)

        self.logger.info(
            f"Cleaned data: {len(clean_companies)} companies after removing duplicates"
        )
        return clean_companies

    def _comprehensive_sync_to_database(
        self, companies: list[Company]
    ) -> dict[str, int]:
        """Comprehensive database synchronization with bulk operations and ticker management."""
        results = {
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "tickers_inserted": 0,
            "ticker_histories_inserted": 0,
        }

        if not companies:
            return results

        try:
            # Get existing data from database
            existing_company_symbols = self.company_repo.get_active_company_symbols()
            existing_ticker_symbols = self.ticker_repo.get_active_ticker_symbols()

            # Categorize companies
            new_companies = self._identify_new_companies(
                companies, existing_company_symbols
            )
            companies_to_update = self._identify_companies_to_update(
                companies, existing_company_symbols
            )

            # 1. Insert new companies using bulk operations
            if new_companies:
                self.logger.info(f"Inserting {len(new_companies)} new companies...")
                companies_inserted = self.company_repo.bulk_insert_companies(
                    new_companies
                )
                results["inserted"] = companies_inserted

                if companies_inserted > 0:
                    # Get the newly inserted companies with their database IDs
                    inserted_companies_with_ids = []
                    for company in new_companies:
                        if company.ticker:
                            ticker_symbol = company.ticker.symbol
                            db_company = self.company_repo.get_company_by_ticker(
                                ticker_symbol
                            )
                            if db_company:
                                inserted_companies_with_ids.append(db_company)

                    # Create tickers for new companies
                    if inserted_companies_with_ids:
                        tickers_to_insert = self._create_tickers_for_companies(
                            inserted_companies_with_ids
                        )
                        if tickers_to_insert:
                            self.logger.info(
                                f"Inserting {len(tickers_to_insert)} new tickers..."
                            )
                            results["tickers_inserted"] = (
                                self.ticker_repo.bulk_insert_tickers(tickers_to_insert)
                            )

                        # Create ticker histories for new companies
                        ticker_histories_to_insert = (
                            self._create_ticker_histories_for_companies(
                                inserted_companies_with_ids
                            )
                        )
                        if ticker_histories_to_insert:
                            self.logger.info(
                                f"Inserting {len(ticker_histories_to_insert)} new ticker histories..."
                            )
                            results["ticker_histories_inserted"] = (
                                self.ticker_history_repo.bulk_insert_ticker_histories(
                                    ticker_histories_to_insert
                                )
                            )

            # 2. Update existing companies
            if companies_to_update:
                self.logger.info(
                    f"Updating {len(companies_to_update)} existing companies..."
                )
                for company in companies_to_update:
                    if company.ticker is None:
                        continue
                    ticker_symbol = company.ticker.symbol
                    try:
                        # Create update object with only market_cap
                        market_cap_update = Company(
                            company_name="",  # Empty = ignored by base repository
                            exchange="",      # Empty = ignored by base repository
                            market_cap=company.market_cap  # Only this will be updated
                        )
                        
                        if self.company_repo.update_company(ticker_symbol, market_cap_update):
                            results["updated"] += 1
                        else:
                            results["skipped"] += 1
                    except Exception as e:
                        self.logger.error(
                            f"Error updating company {ticker_symbol}: {e}"
                        )
                        results["errors"] += 1

            # 3. Handle companies with new ticker symbols (existing companies, new tickers)
            new_ticker_companies = self._identify_new_tickers(
                companies, existing_ticker_symbols
            )
            existing_companies_with_new_tickers = []

            for ticker_company in new_ticker_companies:
                ticker_symbol_for_new: str | None = (
                    ticker_company.ticker.symbol if ticker_company.ticker else None
                )
                new_company_tickers = {
                    c.ticker.symbol for c in new_companies if c.ticker
                }

                if (
                    ticker_symbol_for_new
                    and ticker_symbol_for_new not in new_company_tickers
                ):
                    # This might be an existing company with a new ticker symbol
                    assert ticker_symbol_for_new is not None  # Type guard for mypy
                    existing_company = self.company_repo.get_company_by_ticker(
                        ticker_symbol_for_new
                    )
                    if existing_company:
                        existing_companies_with_new_tickers.append(existing_company)

            # Create additional tickers for existing companies
            if existing_companies_with_new_tickers:
                additional_tickers = self._create_tickers_for_companies(
                    existing_companies_with_new_tickers
                )
                if additional_tickers:
                    self.logger.info("Inserting additional ticker symbols...")
                    additional_tickers_inserted = self.ticker_repo.bulk_insert_tickers(
                        additional_tickers
                    )
                    results["tickers_inserted"] += additional_tickers_inserted

        except Exception as e:
            self.logger.error(f"Error during comprehensive database sync: {e}")
            results["errors"] += 1
            raise

        return results

    def _identify_new_companies(
        self, companies: list[Company], existing_symbols: set[str]
    ) -> list[Company]:
        """Identify new companies that don't exist in the database."""
        new_companies = []

        for company in companies:
            ticker_symbol = company.ticker.symbol if company.ticker else None
            if ticker_symbol and ticker_symbol not in existing_symbols:
                new_companies.append(company)

        self.logger.info(f"Identified {len(new_companies)} new companies")
        return new_companies

    def _identify_companies_to_update(
        self, companies: list[Company], existing_symbols: set[str]
    ) -> list[Company]:
        """Identify existing companies that may need updates."""
        companies_to_update = []

        for company in companies:
            ticker_symbol = company.ticker.symbol if company.ticker else None
            if ticker_symbol and ticker_symbol in existing_symbols:
                companies_to_update.append(company)

        self.logger.info(
            f"Identified {len(companies_to_update)} companies for potential updates"
        )
        return companies_to_update

    def _identify_new_tickers(
        self, companies: list[Company], existing_ticker_symbols: set[str]
    ) -> list[Company]:
        """Identify companies with ticker symbols not in the ticker repository."""
        new_ticker_companies = []

        for company in companies:
            ticker_symbol = company.ticker.symbol if company.ticker else None
            if ticker_symbol and ticker_symbol not in existing_ticker_symbols:
                new_ticker_companies.append(company)

        self.logger.info(
            f"Identified {len(new_ticker_companies)} companies with new ticker symbols"
        )
        return new_ticker_companies

    def _create_tickers_for_companies(
        self, companies: list[Company]
    ) -> list[TickerDataModel]:
        """Create ticker data models for companies."""
        tickers = []

        for company in companies:
            if company.ticker and company.id:
                ticker = TickerDataModel(
                    symbol=company.ticker.symbol, company_id=company.id
                )
                tickers.append(ticker)

        self.logger.info(f"Created {len(tickers)} ticker data models")
        return tickers

    def _create_ticker_histories_for_companies(
        self, companies: list[Company]
    ) -> list[TickerHistoryDataModel]:
        """Create ticker history data models for companies."""
        ticker_histories = []
        today = date.today()

        for company in companies:
            if company.ticker and company.id:
                ticker_history = TickerHistoryDataModel(
                    symbol=company.ticker.symbol,
                    company_id=company.id,
                    valid_from=today,
                    valid_to=None,  # Open-ended validity
                    active=True,
                )
                ticker_histories.append(ticker_history)

        self.logger.info(f"Created {len(ticker_histories)} ticker history data models")
        return ticker_histories

    def _get_unused_tickers(self, active_screener_symbols: set[str]) -> set[str]:
        """Identify ticker symbols that are in the database but not in current screener data."""
        try:
            # Get all active ticker symbols from database
            db_ticker_symbols = self.ticker_repo.get_active_ticker_symbols()

            # Find tickers in database that are not in current screener data
            unused_tickers = db_ticker_symbols - active_screener_symbols

            self.logger.info(f"Found {len(unused_tickers)} unused ticker symbols")
            return unused_tickers

        except Exception as e:
            self.logger.error(f"Error identifying unused tickers: {e}")
            raise
