#!/usr/bin/env python3
"""Example usage of the simple company ingestion pipeline."""

from src.data_sources.nasdaq.screener import NasdaqScreenerSource
from src.pipelines.companies.simple_pipeline import CompanyPipeline


def example_single_source():
    """Example using a single NASDAQ screener source."""
    print("=== Single Source Example ===")

    # Create data source
    nasdaq_source = NasdaqScreenerSource("/path/to/screener/files")

    # Create pipeline
    pipeline = CompanyPipeline()

    # Run ingestion (this would fail without real files, but shows the API)
    try:
        results = pipeline.run_ingestion([nasdaq_source])

        print(f"Inserted: {results['inserted']}")
        print(f"Updated: {results['updated']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Errors: {results['errors']}")

    except Exception as e:
        print(f"Example error (expected without real data): {e}")


def example_multiple_sources():
    """Example using multiple data sources."""
    print("\n=== Multiple Sources Example ===")

    # Create multiple NASDAQ sources from different directories
    nasdaq_source1 = NasdaqScreenerSource("/path/to/screener/files1")
    nasdaq_source2 = NasdaqScreenerSource("/path/to/screener/files2")

    # Create pipeline
    pipeline = CompanyPipeline()

    # Run ingestion from multiple sources
    try:
        results = pipeline.run_ingestion([nasdaq_source1, nasdaq_source2])

        print("Results from multiple sources:")
        print(f"  Inserted: {results['inserted']}")
        print(f"  Updated: {results['updated']}")
        print(f"  Skipped: {results['skipped']}")
        print(f"  Errors: {results['errors']}")

    except Exception as e:
        print(f"Example error (expected without real data): {e}")


def example_custom_source():
    """Example showing how to create a custom data source."""
    print("\n=== Custom Source Example ===")

    import logging

    from src.data_sources.base.company_data_source import CompanyDataSource
    from src.data_sources.models.company import Company
    from src.data_sources.models.ticker import Ticker

    class MockDataSource(CompanyDataSource):
        """Mock data source for demonstration."""

        @property
        def name(self) -> str:
            return "Mock Data Source"

        def get_companies(self) -> list[Company]:
            """Return some mock companies."""
            return [
                Company(
                    company_name="Mock Company 1",
                    exchange="NYSE",
                    ticker=Ticker(symbol="MOCK1", company_id=None),
                    sector="Technology",
                    active=True,
                ),
                Company(
                    company_name="Mock Company 2",
                    exchange="NASDAQ",
                    ticker=Ticker(symbol="MOCK2", company_id=None),
                    sector="Healthcare",
                    active=True,
                ),
            ]

    class MockCompanyRepository:
        """Mock company repository for testing."""

        def get_active_company_symbols(self) -> set[str]:
            return set()  # Empty set for mock

        def bulk_insert_companies(self, companies: list[Company]) -> int:
            print(f"[MOCK] Would insert {len(companies)} companies")
            return len(companies)

        def update_company(self, ticker_symbol: str, company: Company) -> bool:
            print(f"[MOCK] Would update company {ticker_symbol}")
            return True

        def get_company_by_ticker(self, ticker_symbol: str) -> Company | None:
            return None  # Not found for mock

    class MockTickerRepository:
        """Mock ticker repository for testing."""

        def get_active_ticker_symbols(self) -> set[str]:
            return set()  # Empty set for mock

        def bulk_insert_tickers(self, tickers) -> int:
            print(f"[MOCK] Would insert {len(tickers)} tickers")
            return len(tickers)

    class MockTickerHistoryRepository:
        """Mock ticker history repository for testing."""

        def bulk_insert_ticker_histories(self, ticker_histories) -> int:
            print(f"[MOCK] Would insert {len(ticker_histories)} ticker histories")
            return len(ticker_histories)

    # Use the custom source with mock repositories
    mock_source = MockDataSource()
    mock_company_repo = MockCompanyRepository()
    mock_ticker_repo = MockTickerRepository()
    mock_ticker_history_repo = MockTickerHistoryRepository()
    mock_logger = logging.getLogger("mock_pipeline")

    pipeline = CompanyPipeline(
        company_repo=mock_company_repo,
        ticker_repo=mock_ticker_repo,
        ticker_history_repo=mock_ticker_history_repo,
        logger=mock_logger,
    )

    try:
        results = pipeline.run_ingestion([mock_source])
        print("Mock source results:")
        print(f"  Inserted: {results['inserted']}")
        print(f"  Updated: {results['updated']}")
        print(f"  Skipped: {results['skipped']}")
        print(f"  Errors: {results['errors']}")
        print(f"  Tickers inserted: {results['tickers_inserted']}")
        print(f"  Ticker histories inserted: {results['ticker_histories_inserted']}")

    except Exception as e:
        print(f"Error with mock source: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("Company Ingestion Pipeline Usage Examples")
    print("=" * 50)

    # Run examples (these will show the API but won't actually work without real data)
    example_single_source()
    example_multiple_sources()
    example_custom_source()

    print("\n" + "=" * 50)
    print("Examples completed!")
    print("Note: These examples show the API usage but won't run successfully")
    print("without real data files and database configuration.")
