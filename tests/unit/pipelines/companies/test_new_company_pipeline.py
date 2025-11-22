"""Comprehensive tests for CompanyPipeline using mocks."""

import logging
import unittest

from src.data_sources.nasdaq.company_mock import create_nasdaq_company_source_mock

# Import our mocks
from src.data_sources.nasdaq.screener_mock import create_nasdaq_screener_source_mock
from src.models.company import Company
from src.models.ticker import Ticker
from src.pipelines.companies.new_company_pipeline import CompanyPipeline
from src.repos.equities.companies.company_repository_mock import (
    create_company_repository_mock,
)
from src.repos.equities.tickers.ticker_history_repository_mock import (
    create_ticker_history_repository_mock,
)
from src.repos.equities.tickers.ticker_repository_mock import (
    create_ticker_repository_mock,
)


class TestCompanyPipeline(unittest.TestCase):
    """Test CompanyPipeline with comprehensive mock scenarios."""

    def setUp(self):
        """Set up test fixtures with mocked repositories."""
        # Create mock repositories
        self.mock_company_repo = create_company_repository_mock(seed=12345)
        self.mock_ticker_repo = create_ticker_repository_mock(seed=12345)
        self.mock_ticker_history_repo = create_ticker_history_repository_mock(
            seed=12345
        )

        # Create pipeline and inject mocks
        self.pipeline = CompanyPipeline()
        self.pipeline.company_repo = self.mock_company_repo
        self.pipeline.ticker_repo = self.mock_ticker_repo
        self.pipeline.ticker_history_repo = self.mock_ticker_history_repo

        # Set up logging to capture messages
        self.logger = logging.getLogger("src.pipelines.companies.new_company_pipeline")
        self.logger.setLevel(logging.DEBUG)

    def tearDown(self):
        """Clean up after each test."""
        # Reset mock repositories to clean state by recreating them
        self.mock_company_repo = create_company_repository_mock(seed=12345)
        self.mock_ticker_repo = create_ticker_repository_mock(seed=12345)
        self.mock_ticker_history_repo = create_ticker_history_repository_mock(
            seed=12345
        )

        # Re-inject mocks into pipeline
        self.pipeline.company_repo = self.mock_company_repo
        self.pipeline.ticker_repo = self.mock_ticker_repo
        self.pipeline.ticker_history_repo = self.mock_ticker_history_repo

    def test_run_ingestion_with_single_source(self):
        """Test basic ingestion with a single data source."""
        # Create mock data source
        mock_source = create_nasdaq_screener_source_mock(seed=12345)
        mock_source.set_companies_per_file(10)  # Generate 10 companies per file

        # Run ingestion
        results = self.pipeline.run_ingestion([mock_source])

        # Verify results structure
        self.assertIn("inserted", results)
        self.assertIn("updated", results)
        self.assertIn("skipped", results)
        self.assertIn("errors", results)
        self.assertIn("tickers_inserted", results)
        self.assertIn("ticker_histories_inserted", results)

        # Should have inserted new companies (screener generates ~30 companies by default)
        self.assertGreater(results["inserted"], 0)
        self.assertEqual(results["errors"], 0)

        # Verify companies were actually added to repository
        all_companies = self.mock_company_repo.get_all_companies()
        self.assertGreater(
            len(all_companies), 3
        )  # More than initial 3 predefined companies

    def test_run_ingestion_with_multiple_sources(self):
        """Test ingestion with multiple data sources."""
        # Create multiple mock data sources
        screener_source = create_nasdaq_screener_source_mock(seed=12345)
        screener_source.set_companies_per_file(5)

        # Create NASDAQ company source mock (already implements CompanyDataSource)
        api_source = create_nasdaq_company_source_mock(seed=54321)
        api_source.set_company_count(8)

        # Run ingestion with multiple sources
        results = self.pipeline.run_ingestion([screener_source, api_source])

        # Verify results
        self.assertGreater(
            results["inserted"], 5
        )  # Should have companies from both sources
        self.assertEqual(results["errors"], 0)

        # Verify companies from both sources were processed
        all_companies = self.mock_company_repo.get_all_companies()
        company_sources = [
            c.source for c in all_companies if hasattr(c, "source") and c.source
        ]
        self.assertTrue(any("screener" in source.lower() for source in company_sources))

    def test_run_ingestion_with_unavailable_source(self):
        """Test ingestion when a data source is unavailable."""
        # Create mock source and make it unavailable
        mock_source = create_nasdaq_screener_source_mock(seed=12345)
        mock_source.set_available(False)

        # Run ingestion
        results = self.pipeline.run_ingestion([mock_source])

        # Should handle unavailable source gracefully
        self.assertEqual(results["inserted"], 0)
        self.assertEqual(results["updated"], 0)
        self.assertEqual(results["errors"], 0)

    def test_run_ingestion_with_source_error(self):
        """Test ingestion when data source throws an error."""
        # Create mock source that will throw an error
        mock_source = create_nasdaq_screener_source_mock(seed=12345)
        mock_source.simulate_loader_error("Mock data source error")

        # Run ingestion
        results = self.pipeline.run_ingestion([mock_source])

        # Should handle error gracefully
        self.assertEqual(results["inserted"], 0)
        self.assertEqual(results["errors"], 1)

    def test_clean_companies_removes_duplicates(self):
        """Test that the cleaning process removes duplicate tickers."""
        # Create companies with duplicate tickers
        companies = [
            Company(
                company_name="Apple Inc.",
                exchange="NASDAQ",
                ticker=Ticker(symbol="AAPL", company_id=None),
            ),
            Company(
                company_name="Apple Inc. (Duplicate)",
                exchange="NASDAQ",
                ticker=Ticker(symbol="AAPL", company_id=None),  # Same ticker
            ),
            Company(
                company_name="Microsoft Corporation",
                exchange="NASDAQ",
                ticker=Ticker(symbol="MSFT", company_id=None),
            ),
        ]

        # Clean the companies
        clean_companies = self.pipeline._clean_companies(companies)

        # Should have removed duplicate ticker
        self.assertEqual(len(clean_companies), 2)
        tickers = [c.ticker.symbol for c in clean_companies]
        self.assertEqual(len(set(tickers)), 2)  # All unique tickers

    def test_clean_companies_removes_invalid_companies(self):
        """Test that cleaning removes companies without valid tickers."""
        companies = [
            Company(
                company_name="Valid Company",
                exchange="NASDAQ",
                ticker=Ticker(symbol="VALID", company_id=None),
            ),
            Company(
                company_name="No Ticker Company",
                exchange="NASDAQ",
                ticker=None,  # No ticker
            ),
            Company(
                company_name="Empty Ticker Company",
                exchange="NASDAQ",
                ticker=Ticker(symbol="", company_id=None),  # Empty ticker
            ),
        ]

        # Clean the companies
        clean_companies = self.pipeline._clean_companies(companies)

        # Should only keep valid company
        self.assertEqual(len(clean_companies), 1)
        self.assertEqual(clean_companies[0].company_name, "Valid Company")

    def test_identify_new_companies(self):
        """Test identification of new companies."""
        companies = [
            Company(
                company_name="New Company",
                exchange="NASDAQ",
                ticker=Ticker(symbol="NEWCO", company_id=None),
            ),
            Company(
                company_name="Existing Company",
                exchange="NASDAQ",
                ticker=Ticker(
                    symbol="AAPL", company_id=None
                ),  # AAPL exists in mock repo
            ),
        ]

        existing_symbols = self.mock_company_repo.get_active_company_symbols()
        new_companies = self.pipeline._identify_new_companies(
            companies, existing_symbols
        )

        # Should identify only the new company
        self.assertEqual(len(new_companies), 1)
        self.assertEqual(new_companies[0].ticker.symbol, "NEWCO")

    def test_identify_companies_to_update(self):
        """Test identification of companies that need updates."""
        companies = [
            Company(
                company_name="New Company",
                exchange="NASDAQ",
                ticker=Ticker(symbol="NEWCO", company_id=None),
            ),
            Company(
                company_name="Apple Inc. Updated",
                exchange="NASDAQ",
                ticker=Ticker(
                    symbol="AAPL", company_id=None
                ),  # AAPL exists in mock repo
            ),
        ]

        existing_symbols = self.mock_company_repo.get_active_company_symbols()
        companies_to_update = self.pipeline._identify_companies_to_update(
            companies, existing_symbols
        )

        # Should identify only the existing company for update
        self.assertEqual(len(companies_to_update), 1)
        self.assertEqual(companies_to_update[0].ticker.symbol, "AAPL")

    def test_create_tickers_for_companies(self):
        """Test ticker creation for companies."""
        companies = [
            Company(
                id=1,
                company_name="Test Company 1",
                exchange="NASDAQ",
                ticker=Ticker(symbol="TEST1", company_id=None),
            ),
            Company(
                id=2,
                company_name="Test Company 2",
                exchange="NYSE",
                ticker=Ticker(symbol="TEST2", company_id=None),
            ),
        ]

        tickers = self.pipeline._create_tickers_for_companies(companies)

        # Should create ticker for each company
        self.assertEqual(len(tickers), 2)
        self.assertEqual(tickers[0].symbol, "TEST1")
        self.assertEqual(tickers[0].company_id, 1)
        self.assertEqual(tickers[1].symbol, "TEST2")
        self.assertEqual(tickers[1].company_id, 2)

    def test_create_ticker_histories_for_companies(self):
        """Test ticker history creation for companies."""
        companies = [
            Company(
                id=1,
                company_name="Test Company 1",
                exchange="NASDAQ",
                ticker=Ticker(symbol="TEST1", company_id=None),
            ),
            Company(
                id=2,
                company_name="Test Company 2",
                exchange="NYSE",
                ticker=Ticker(symbol="TEST2", company_id=None),
            ),
        ]

        ticker_histories = self.pipeline._create_ticker_histories_for_companies(
            companies
        )

        # Should create ticker history for each company
        self.assertEqual(len(ticker_histories), 2)
        self.assertEqual(ticker_histories[0].symbol, "TEST1")
        self.assertEqual(ticker_histories[0].company_id, 1)
        self.assertTrue(ticker_histories[0].active)
        self.assertIsNotNone(ticker_histories[0].valid_from)
        self.assertIsNone(ticker_histories[0].valid_to)  # Open-ended

    def test_run_comprehensive_sync(self):
        """Test comprehensive synchronization with unused ticker detection."""
        # Create mock source
        mock_source = create_nasdaq_screener_source_mock(seed=12345)
        mock_source.set_companies_per_file(5)

        # Add some extra tickers to the ticker repository that won't be in screener data
        fake_tickers = self.mock_ticker_repo.add_fake_tickers(2, company_id=999)
        # Manually set symbols for predictable testing
        fake_tickers[0].symbol = "UNUSED1"
        fake_tickers[1].symbol = "UNUSED2"

        # Run comprehensive sync
        results = self.pipeline.run_comprehensive_sync([mock_source])

        # Should have standard results plus unused ticker information
        self.assertIn("unused_tickers", results)
        self.assertIn("unused_ticker_count", results)

        # Should detect unused tickers (the ones we added manually)
        self.assertGreater(results["unused_ticker_count"], 0)

    def test_get_unused_tickers(self):
        """Test unused ticker detection."""
        # Add tickers to repository with specific symbols
        from src.models.ticker import Ticker

        self.mock_ticker_repo.insert(Ticker(symbol="ACTIVE1", company_id=1))
        self.mock_ticker_repo.insert(Ticker(symbol="UNUSED1", company_id=2))
        self.mock_ticker_repo.insert(Ticker(symbol="UNUSED2", company_id=3))

        # Simulate screener symbols (only include ACTIVE1)
        screener_symbols = {
            "ACTIVE1",
            "AAPL",
            "MSFT",
        }  # Include existing symbols from mock repo

        # Get unused tickers
        unused_tickers = self.pipeline._get_unused_tickers(screener_symbols)

        # Should find the unused tickers
        self.assertIn("UNUSED1", unused_tickers)
        self.assertIn("UNUSED2", unused_tickers)
        self.assertNotIn("ACTIVE1", unused_tickers)
        self.assertNotIn("AAPL", unused_tickers)  # This exists in both

    def test_pipeline_with_empty_sources_list(self):
        """Test pipeline behavior with empty sources list."""
        results = self.pipeline.run_ingestion([])

        # Should handle empty sources gracefully
        self.assertEqual(results["inserted"], 0)
        self.assertEqual(results["updated"], 0)
        self.assertEqual(results["skipped"], 0)
        self.assertEqual(results["errors"], 0)

    def test_pipeline_database_operations_integration(self):
        """Test end-to-end pipeline with database operations."""
        # Clear existing data to start fresh by recreating clean mocks
        self.mock_company_repo = create_company_repository_mock(seed=99999)
        self.mock_ticker_repo = create_ticker_repository_mock(seed=99999)
        self.mock_ticker_history_repo = create_ticker_history_repository_mock(
            seed=99999
        )

        # Re-inject clean mocks into pipeline
        self.pipeline.company_repo = self.mock_company_repo
        self.pipeline.ticker_repo = self.mock_ticker_repo
        self.pipeline.ticker_history_repo = self.mock_ticker_history_repo

        # Create mock source with specific companies
        mock_source = create_nasdaq_screener_source_mock(seed=99999)
        mock_source.set_companies_per_file(3)  # Small number for predictable testing

        # Run full ingestion
        results = self.pipeline.run_ingestion([mock_source])

        # Verify database state
        companies_in_db = self.mock_company_repo.get_all_companies()
        tickers_in_db = self.mock_ticker_repo.get_all_tickers()
        ticker_histories_in_db = (
            self.mock_ticker_history_repo.get_all_ticker_histories()
        )

        # Should have inserted companies, tickers, and histories
        self.assertGreater(len(companies_in_db), 0)
        # Allow for some variance in mock data generation (companies may already exist)
        self.assertGreaterEqual(len(companies_in_db), results["inserted"])

        # Verify relationship consistency
        company_ids = {c.id for c in companies_in_db}
        ticker_company_ids = {t.company_id for t in tickers_in_db}
        history_company_ids = {h.company_id for h in ticker_histories_in_db}

        # All ticker company_ids should reference existing companies
        self.assertTrue(ticker_company_ids.issubset(company_ids))
        self.assertTrue(history_company_ids.issubset(company_ids))


if __name__ == "__main__":
    # Set up logging for test runs
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    unittest.main(verbosity=2)
