"""NASDAQ screener data loader for CSV files."""

from src.data_sources.base.company_data_source import CompanyDataSource
from src.data_sources.models.company import Company
from src.data_sources.models.ticker import Ticker

from __future__ import annotations

import csv
import logging
from pathlib import Path


class ScreenerHeaders:
    """Headers expected in NASDAQ screener CSV files."""

    SYMBOL = "Symbol"
    NAME = "Name"
    MARKET_CAP = "Market Cap"
    COUNTRY = "Country"
    SECTOR = "Sector"
    INDUSTRY = "Industry"


class NasdaqScreenerLoader:
    """NASDAQ screener CSV file loader and parser."""

    def __init__(self):
        """Initialize the screener loader."""
        self.logger = logging.getLogger(__name__)

    def load_file(self, file_path: str | Path) -> list[Company]:
        """Load NASDAQ screener data from CSV file.

        Args:
            file_path: Path to the CSV file (format: nasdaq_screener_MONTH_DAY_YEAR.csv)

        Returns:
            List of Company objects with screener data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Screener file not found: {file_path}")

        self.logger.info(f"Loading NASDAQ screener data from {file_path}")

        companies = []

        try:
            with open(file_path, encoding="utf-8") as f:
                csv_reader = csv.DictReader(f)
                if csv_reader.fieldnames == None:
                    raise ValueError(f"data in the csv is not found: {file_path}")

                # Validate required headers exist
                self._validate_headers(csv_reader.fieldnames, file_path)

                for row_num, row in enumerate(
                    csv_reader, start=2
                ):  # Start at 2 for header row
                    try:
                        company = self._convert_row_to_company(row)
                        if company:
                            companies.append(company)
                    except Exception as e:
                        self.logger.warning(f"Error processing row {row_num}: {e}")
                        continue

            self.logger.info(
                f"Successfully loaded {len(companies)} companies from screener file"
            )
            return companies

        except csv.Error as e:
            raise ValueError(f"Invalid CSV format in file {file_path}: {e}")
        except Exception as e:
            self.logger.error(f"Error loading screener file {file_path}: {e}")
            raise

    def load_directory(self, directory_path: str | Path) -> list[Company]:
        """Load all NASDAQ screener files from a directory.

        Args:
            directory_path: Path to directory containing screener CSV files

        Returns:
            List of Company objects from all screener files
        """
        directory_path = Path(directory_path)

        if not directory_path.exists():
            raise FileNotFoundError(f"Screener directory not found: {directory_path}")

        all_companies = []

        # Find all screener files matching the pattern
        screener_files = list(directory_path.glob("nasdaq_screener_*.csv"))

        if not screener_files:
            self.logger.warning(f"No screener files found in {directory_path}")
            return all_companies

        self.logger.info(f"Found {len(screener_files)} screener files")

        for file_path in screener_files:
            try:
                companies = self.load_file(file_path)
                all_companies.extend(companies)
                self.logger.info(
                    f"Loaded {len(companies)} companies from {file_path.name}"
                )
            except Exception as e:
                self.logger.error(f"Error loading file {file_path.name}: {e}")
                continue

        self.logger.info(
            f"Total companies loaded from all screener files: {len(all_companies)}"
        )
        return all_companies

    def _validate_headers(self, fieldnames: list[str], file_path: Path) -> None:
        """Validate that required headers exist in the CSV file.

        Args:
            fieldnames: List of field names from CSV header
            file_path: Path to file for error reporting

        Raises:
            ValueError: If required headers are missing
        """
        required_headers = [
            ScreenerHeaders.SYMBOL,
            ScreenerHeaders.NAME,
            ScreenerHeaders.MARKET_CAP,
            ScreenerHeaders.COUNTRY,
            ScreenerHeaders.SECTOR,
            ScreenerHeaders.INDUSTRY,
        ]

        missing_headers = [h for h in required_headers if h not in fieldnames]
        if missing_headers:
            raise ValueError(f"Missing required headers: {missing_headers}")

    def _convert_row_to_company(self, row: dict) -> Company | None:
        """Convert a screener CSV row to Company object.

        Args:
            row: Dictionary representing a CSV row

        Returns:
            Company object or None if conversion fails
        """
        symbol = row.get(ScreenerHeaders.SYMBOL, "").strip()
        name = row.get(ScreenerHeaders.NAME, "").strip()

        # Skip rows with missing essential data
        if not symbol or not name:
            return None

        # Parse market cap (remove commas and convert to int)
        market_cap_str = (
            row.get(ScreenerHeaders.MARKET_CAP, "").replace(",", "").strip()
        )
        market_cap = None
        if market_cap_str and market_cap_str != "0.00":
            try:
                market_cap = int(float(market_cap_str))
            except (ValueError, TypeError):
                market_cap = None

        # Get other fields with defaults
        country = row.get(ScreenerHeaders.COUNTRY, "").strip() or None
        sector = row.get(ScreenerHeaders.SECTOR, "").strip() or None
        industry = row.get(ScreenerHeaders.INDUSTRY, "").strip() or None

        # Determine exchange from symbol characteristics (basic heuristic)
        exchange = "NASDAQ"  # Default to NASDAQ since this is screener data

        # Create ticker model (company_id will be set when company is saved to database)
        ticker_model = Ticker(
            symbol=symbol,
            company_id=None,  # Will be updated when company is inserted
        )

        return Company(
            id=None,
            ticker=ticker_model,
            company_name=name,
            exchange=exchange,
            sector=sector,
            industry=industry,
            country=country,
            market_cap=market_cap,
            description=None,
            source="NASDAQ_SCREENER",
        )


class NasdaqScreenerSource(CompanyDataSource):
    """Convert NASDAQ screener files into a data source."""

    def __init__(self, screener_dir: str = None):
        """Initialize NASDAQ screener source.

        Args:
            screener_dir: Path to directory containing screener CSV files.
                         If None, uses default path.
        """
        self.screener_dir = screener_dir
        self.loader = NasdaqScreenerLoader()

    @property
    def name(self) -> str:
        """Name of the data source."""
        return "NASDAQ Screener Files"

    def get_companies(self) -> list[Company]:
        """Load companies from NASDAQ screener files.

        Returns:
            List of Company objects from screener files
        """
        return self.loader.load_directory(self.screener_dir)


# Backward compatibility functions - delegate to class methods
def load_screener_file(file_path: str | Path) -> list[Company]:
    """Load NASDAQ screener data from CSV file.

    DEPRECATED: Use NasdaqScreenerLoader.load_file() instead.
    """
    loader = NasdaqScreenerLoader()
    return loader.load_file(file_path)


def load_screener_files_from_directory(directory_path: str | Path) -> list[Company]:
    """Load all NASDAQ screener files from a directory.

    DEPRECATED: Use NasdaqScreenerLoader.load_directory() instead.
    """
    loader = NasdaqScreenerLoader()
    return loader.load_directory(directory_path)


if __name__ == "__main__":
    # Example usage
    screener_dir = Path(__file__).parent / "data" / "data_screener"

    if screener_dir.exists():
        loader = NasdaqScreenerLoader()
        companies = loader.load_directory(screener_dir)
        print(f"Loaded {len(companies)} companies from screener files")

        # Show first few companies
        for company in companies[:5]:
            company.print()
            print("-" * 40)
    else:
        print(f"Screener directory not found: {screener_dir}")
