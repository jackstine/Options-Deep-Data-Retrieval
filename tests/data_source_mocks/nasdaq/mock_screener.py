"""Mock NASDAQ screener data source for testing."""

from __future__ import annotations

from pathlib import Path

from src.data_sources.base.company_data_source import CompanyDataSource
from src.data_sources.nasdaq.screener import NasdaqScreenerLoader
from src.models.company import Company


class MockNasdaqScreenerSource(CompanyDataSource):
    """Mock NASDAQ screener source that reads from fixture files."""

    def __init__(self) -> None:
        """Initialize mock NASDAQ screener source.

        The mock automatically uses the fixtures directory.
        """
        self.fixtures_dir = Path(__file__).parent / "fixtures"
        self.loader = NasdaqScreenerLoader()

    @property
    def name(self) -> str:
        """Name of the data source."""
        return "Mock NASDAQ Screener Files"

    def get_companies(self) -> list[Company]:
        """Load companies from NASDAQ screener fixture file.

        Returns:
            List of Company objects from fixture file
        """
        # Load the single screener.csv file from fixtures
        fixture_file = self.fixtures_dir / "screener.csv"

        if not fixture_file.exists():
            raise FileNotFoundError(f"Fixture file not found: {fixture_file}")

        return self.loader.load_file(fixture_file)

    def get_delisted_symbols(self) -> list[Company]:
        """Get delisted symbols from NASDAQ screener.

        NASDAQ screener files only contain active symbols, so this returns empty list.

        Returns:
            Empty list (NASDAQ screener doesn't provide delisted symbols)
        """
        return []
