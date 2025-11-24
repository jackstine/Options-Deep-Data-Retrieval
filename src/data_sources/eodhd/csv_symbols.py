#!/usr/bin/env python3
"""EODHD CSV symbols data loader for delisted companies.

This module provides functionality to load delisted company symbols from
EODHD CSV files stored locally, implementing the CompanyDataSource interface.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from src.config.configuration import CONFIG
from src.data_sources.base.company_data_source import CompanyDataSource
from src.database.equities.enums import DataSourceEnum
from src.models.company import Company


class EodhdCsvHeaders:
    """Headers expected in EODHD delisted symbols CSV files."""

    CODE = "Code"
    NAME = "Name"
    COUNTRY = "Country"
    EXCHANGE = "Exchange"
    CURRENCY = "Currency"
    TYPE = "Type"
    ISIN = "Isin"


class EodhdCsvSymbolsLoader:
    """EODHD CSV symbols file loader and parser."""

    def __init__(self) -> None:
        """Initialize the CSV symbols loader."""
        self.logger = logging.getLogger(__name__)

    def load_delisted_file(self, file_path: str | Path) -> list[Company]:
        """Load EODHD delisted symbols from CSV file.

        Args:
            file_path: Path to the delisted.csv file

        Returns:
            List of Company objects with delisted symbol data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Delisted symbols file not found: {file_path}")

        self.logger.info(f"Loading EODHD delisted symbols from {file_path}")

        companies = []
        skipped_count = 0

        # Get test limits from configuration
        test_limit = CONFIG.get_test_limits()
        if test_limit:
            self.logger.info(f"Test limits active: processing max {test_limit} symbols")

        try:
            with open(file_path, encoding="utf-8") as f:
                csv_reader = csv.DictReader(f)
                if csv_reader.fieldnames is None:
                    raise ValueError(f"No data found in CSV: {file_path}")

                # Validate required headers exist
                self._validate_headers(list(csv_reader.fieldnames), file_path)

                for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header row
                    try:
                        # Apply test limit if configured
                        if test_limit and len(companies) >= test_limit:
                            self.logger.info(
                                f"Reached test limit of {test_limit} symbols, stopping load"
                            )
                            break

                        # Filter for Common Stock only
                        symbol_type = row.get(EodhdCsvHeaders.TYPE, "").strip()
                        if symbol_type != "Common Stock":
                            skipped_count += 1
                            continue

                        company = self._convert_row_to_company(row)
                        if company:
                            companies.append(company)
                    except Exception as e:
                        self.logger.warning(f"Error processing row {row_num}: {e}")
                        continue

            self.logger.info(
                f"Successfully loaded {len(companies)} Common Stock symbols "
                f"(skipped {skipped_count} non-Common Stock symbols)"
            )
            return companies

        except csv.Error as e:
            raise ValueError(f"Invalid CSV format in file {file_path}: {e}")
        except Exception as e:
            self.logger.error(f"Error loading delisted symbols file {file_path}: {e}")
            raise

    def _validate_headers(self, fieldnames: list[str], file_path: Path) -> None:
        """Validate that required headers exist in the CSV file.

        Args:
            fieldnames: List of field names from CSV header
            file_path: Path to file for error reporting

        Raises:
            ValueError: If required headers are missing
        """
        required_headers = [
            EodhdCsvHeaders.CODE,
            EodhdCsvHeaders.NAME,
            EodhdCsvHeaders.EXCHANGE,
            EodhdCsvHeaders.TYPE,
        ]

        missing_headers = [h for h in required_headers if h not in fieldnames]
        if missing_headers:
            raise ValueError(
                f"Missing required headers in {file_path}: {missing_headers}"
            )

    def _convert_row_to_company(self, row: dict) -> Company | None:
        """Convert a CSV row to Company object.

        Uses Company.from_dict() which handles PascalCase field names from EODHD.

        Args:
            row: Dictionary representing a CSV row

        Returns:
            Company object or None if conversion fails
        """
        # Company.from_dict() expects PascalCase field names, which the CSV already has
        # We just need to add the source field and ensure required fields exist
        code = row.get(EodhdCsvHeaders.CODE, "").strip()
        name = row.get(EodhdCsvHeaders.NAME, "").strip()

        # Skip rows with missing essential data
        if not code or not name:
            return None

        # Add source to the row data
        row_with_source = row.copy()
        row_with_source["Source"] = DataSourceEnum.EODHD.value

        try:
            # Company.from_dict() handles PascalCase -> snake_case conversion
            # and creates the ticker from the "Code" field
            company = Company.from_dict(row_with_source)
            return company
        except Exception as e:
            self.logger.warning(f"Error converting row to Company: {e}")
            return None


class EodhdCsvSymbolsSource(CompanyDataSource):
    """EODHD CSV symbols data source for delisted companies."""

    def __init__(self, csv_file_path: str | Path | None = None):
        """Initialize EODHD CSV symbols source.

        Args:
            csv_file_path: Path to the delisted.csv file.
                          If None, uses default path relative to this module.
        """
        if csv_file_path is None:
            # Default to data/symbols/delisted.csv relative to this module
            csv_file_path = Path(__file__).parent / "data" / "symbols" / "delisted.csv"

        self.csv_file_path = Path(csv_file_path)
        self.loader = EodhdCsvSymbolsLoader()

    @property
    def name(self) -> str:
        """Name of the data source."""
        return "EODHD CSV Symbols"

    def get_delisted_symbols(self) -> list[Company]:
        """Load delisted companies from EODHD CSV file.

        Returns:
            List of Company objects from CSV file (filtered for Common Stock only)
        """
        return self.loader.load_delisted_file(self.csv_file_path)

    def get_companies(self) -> list[Company]:
        """Get active companies from this data source.

        EODHD delisted CSV only contains delisted symbols, so this returns empty list.

        Returns:
            Empty list (this CSV only has delisted symbols)
        """
        return []

    def is_available(self) -> bool:
        """Check if the CSV file exists and is available.

        Returns:
            True if CSV file exists, False otherwise
        """
        return self.csv_file_path.exists()
