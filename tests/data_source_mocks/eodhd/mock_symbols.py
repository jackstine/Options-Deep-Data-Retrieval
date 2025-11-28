"""Mock EODHD symbols data source for testing."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from src.data_sources.base.company_data_source import CompanyDataSource
from src.database.equities.enums import DataSourceEnum
from src.models.company import Company

logger = logging.getLogger(__name__)


class MockEodhdSymbolsSource(CompanyDataSource):
    """Mock EODHD data source that reads from fixture files instead of API."""

    def __init__(self) -> None:
        """Initialize mock EODHD symbols data source."""
        self.fixtures_dir = Path(__file__).parent / "fixtures"

    @property
    def name(self) -> str:
        """Name of the data source."""
        return "Mock EODHD Symbols"

    def is_available(self) -> bool:
        """Check if mock data source is available.

        Returns:
            Always returns True for mock data source
        """
        return True

    def get_companies(self) -> list[Company]:
        """Get active companies from fixture file.

        Implements the CompanyDataSource interface by returning only active symbols.

        Returns:
            List of Company instances with active symbol information
        """
        return self.get_active_symbols()

    def get_delisted_symbols(self) -> list[Company]:
        """Get delisted US Common Stock symbols from fixture file.

        Returns:
            List of Company instances with symbol information for Common Stocks
        """
        fixture_file = self.fixtures_dir / "symbols_delisted.csv"

        try:
            with open(fixture_file, newline='') as f:
                reader = csv.DictReader(f)

                # Convert to Company instances
                companies = []
                for row in reader:
                    # Ensure Type is Common Stock
                    if row.get("Type") == "Common Stock":
                        # Map CSV columns to Company.from_dict() format
                        symbol_data = {
                            "Code": row["Code"],
                            "Name": row["Name"],
                            "Country": row["Country"],
                            "Exchange": row["Exchange"],
                            "Currency": row["Currency"],
                            "Type": row["Type"],
                            "Isin": row.get("Isin", ""),
                            "source": DataSourceEnum.EODHD
                        }
                        companies.append(Company.from_dict(symbol_data))

            logger.info(f"Loaded {len(companies)} delisted symbols from fixture")
            return companies

        except FileNotFoundError:
            logger.error(f"Fixture file not found: {fixture_file}")
            return []
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return []

    def get_active_symbols(self, exchange: str = "US") -> list[Company]:
        """Get active US stock symbols from fixture file.

        Args:
            exchange: Exchange code (ignored in mock, always returns US symbols)

        Returns:
            List of Company instances with symbol information (Common Stocks only)
        """
        fixture_file = self.fixtures_dir / "symbols_active.csv"

        try:
            with open(fixture_file, newline='') as f:
                reader = csv.DictReader(f)

                # Convert to Company instances
                companies = []
                for row in reader:
                    # Only include Common Stocks (filter out ETFs and FUNDs)
                    if row.get("Type") == "Common Stock":
                        # Map CSV columns to Company.from_dict() format
                        symbol_data = {
                            "Code": row["Code"],
                            "Name": row["Name"],
                            "Country": row["Country"],
                            "Exchange": row["Exchange"],
                            "Currency": row["Currency"],
                            "Type": row["Type"],
                            "Isin": row.get("Isin", ""),
                            "source": DataSourceEnum.EODHD
                        }
                        companies.append(Company.from_dict(symbol_data))

            logger.info(f"Loaded {len(companies)} active symbols from fixture")
            return companies

        except FileNotFoundError:
            logger.error(f"Fixture file not found: {fixture_file}")
            return []
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return []
