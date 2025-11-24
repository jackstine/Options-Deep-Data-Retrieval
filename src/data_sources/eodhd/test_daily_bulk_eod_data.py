"""Unit tests for EodhdDailyBulkEodData data source using unittest framework.

This test suite covers:
- Successful bulk EOD data retrieval
- Filtering for Common Stock
- Symbol parsing and normalization
- Error handling for API failures
- Data validation and edge cases
"""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.data_sources.eodhd.daily_bulk_eod_data import EodhdDailyBulkEodData
from src.database.equities.enums import DataSourceEnum
from src.models.misplaced_eod_pricing import MisplacedEndOfDayPricing


class TestEodhdDailyBulkEodData(unittest.TestCase):
    """Test the EodhdDailyBulkEodData data source."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.data_source = EodhdDailyBulkEodData()

    @patch("src.data_sources.eodhd.daily_bulk_eod_data.CONFIG.get_eodhd_api_key")
    def test_is_available_with_api_key(self, mock_get_key: MagicMock) -> None:
        """Test that is_available returns True when API key is configured."""
        mock_get_key.return_value = "test_api_key"
        self.assertTrue(self.data_source.is_available())

    @patch("src.data_sources.eodhd.daily_bulk_eod_data.CONFIG.get_eodhd_api_key")
    def test_is_available_without_api_key(self, mock_get_key: MagicMock) -> None:
        """Test that is_available returns False when API key is not configured."""
        mock_get_key.side_effect = Exception("API key not configured")
        self.assertFalse(self.data_source.is_available())

    @patch("src.data_sources.eodhd.daily_bulk_eod_data.requests.get")
    @patch("src.data_sources.eodhd.daily_bulk_eod_data.CONFIG.get_eodhd_api_key")
    def test_get_bulk_latest_eod_success(
        self, mock_get_key: MagicMock, mock_requests_get: MagicMock
    ) -> None:
        """Test successful bulk EOD data retrieval."""
        mock_get_key.return_value = "test_api_key"

        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "code": "AAPL.US",
                "date": "2025-01-15",
                "open": 180.5,
                "high": 182.3,
                "low": 179.8,
                "close": 181.2,
                "adjusted_close": 181.2,
                "volume": 50000000,
                "type": "Common Stock",
            },
            {
                "code": "MSFT.US",
                "date": "2025-01-15",
                "open": 420.1,
                "high": 425.5,
                "low": 419.0,
                "close": 423.8,
                "adjusted_close": 423.8,
                "volume": 30000000,
                "type": "Common Stock",
            },
        ]
        mock_requests_get.return_value = mock_response

        # Call method
        result = self.data_source.get_bulk_latest_eod(exchange="US")

        # Verify results
        self.assertEqual(len(result), 2)
        self.assertIn("AAPL", result)
        self.assertIn("MSFT", result)

        # Verify AAPL data
        aapl_pricing = result["AAPL"]
        self.assertIsInstance(aapl_pricing, MisplacedEndOfDayPricing)
        self.assertEqual(aapl_pricing.symbol, "AAPL")
        self.assertEqual(aapl_pricing.date, date(2025, 1, 15))
        self.assertEqual(aapl_pricing.close, Decimal("181.2"))
        self.assertEqual(aapl_pricing.volume, 50000000)
        self.assertEqual(aapl_pricing.source, DataSourceEnum.EODHD)

        # Verify MSFT data
        msft_pricing = result["MSFT"]
        self.assertEqual(msft_pricing.symbol, "MSFT")
        self.assertEqual(msft_pricing.close, Decimal("423.8"))

    @patch("src.data_sources.eodhd.daily_bulk_eod_data.requests.get")
    @patch("src.data_sources.eodhd.daily_bulk_eod_data.CONFIG.get_eodhd_api_key")
    def test_filter_common_stock(
        self, mock_get_key: MagicMock, mock_requests_get: MagicMock
    ) -> None:
        """Test filtering for Common Stock only."""
        mock_get_key.return_value = "test_api_key"

        # Mock API response with mixed types
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "code": "AAPL.US",
                "date": "2025-01-15",
                "open": 180.5,
                "high": 182.3,
                "low": 179.8,
                "close": 181.2,
                "adjusted_close": 181.2,
                "volume": 50000000,
                "type": "Common Stock",
            },
            {
                "code": "SPY.US",
                "date": "2025-01-15",
                "open": 450.0,
                "high": 455.0,
                "low": 449.0,
                "close": 452.5,
                "adjusted_close": 452.5,
                "volume": 80000000,
                "type": "ETF",
            },
        ]
        mock_requests_get.return_value = mock_response

        # Call method with filter_common_stock=True
        result = self.data_source.get_bulk_latest_eod(
            exchange="US", filter_common_stock=True
        )

        # Verify only Common Stock is returned
        self.assertEqual(len(result), 1)
        self.assertIn("AAPL", result)
        self.assertNotIn("SPY", result)

        # Call method with filter_common_stock=False
        result_no_filter = self.data_source.get_bulk_latest_eod(
            exchange="US", filter_common_stock=False
        )

        # Verify both types are returned
        self.assertEqual(len(result_no_filter), 2)
        self.assertIn("AAPL", result_no_filter)
        self.assertIn("SPY", result_no_filter)

    @patch("src.data_sources.eodhd.daily_bulk_eod_data.requests.get")
    @patch("src.data_sources.eodhd.daily_bulk_eod_data.CONFIG.get_eodhd_api_key")
    def test_symbol_parsing(
        self, mock_get_key: MagicMock, mock_requests_get: MagicMock
    ) -> None:
        """Test that symbols with .US suffix are parsed correctly."""
        mock_get_key.return_value = "test_api_key"

        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "code": "GOOGL.US",
                "date": "2025-01-15",
                "open": 150.0,
                "high": 152.0,
                "low": 149.0,
                "close": 151.5,
                "adjusted_close": 151.5,
                "volume": 20000000,
                "type": "Common Stock",
            }
        ]
        mock_requests_get.return_value = mock_response

        # Call method
        result = self.data_source.get_bulk_latest_eod(exchange="US")

        # Verify symbol is parsed without .US suffix
        self.assertIn("GOOGL", result)
        self.assertNotIn("GOOGL.US", result)
        self.assertEqual(result["GOOGL"].symbol, "GOOGL")

    @patch("src.data_sources.eodhd.daily_bulk_eod_data.requests.get")
    @patch("src.data_sources.eodhd.daily_bulk_eod_data.CONFIG.get_eodhd_api_key")
    def test_missing_data_fields(
        self, mock_get_key: MagicMock, mock_requests_get: MagicMock
    ) -> None:
        """Test handling of records with missing or invalid fields."""
        mock_get_key.return_value = "test_api_key"

        # Mock API response with problematic records
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "code": "AAPL.US",
                "date": "2025-01-15",
                "open": 180.5,
                "high": 182.3,
                "low": 179.8,
                "close": 181.2,
                "adjusted_close": 181.2,
                "volume": 50000000,
                "type": "Common Stock",
            },
            {
                # Missing code field
                "date": "2025-01-15",
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "adjusted_close": 100.5,
                "volume": 10000000,
                "type": "Common Stock",
            },
            {
                "code": "TSLA.US",
                # Missing date field
                "open": 250.0,
                "high": 255.0,
                "low": 248.0,
                "close": 252.5,
                "adjusted_close": 252.5,
                "volume": 40000000,
                "type": "Common Stock",
            },
        ]
        mock_requests_get.return_value = mock_response

        # Call method
        result = self.data_source.get_bulk_latest_eod(exchange="US")

        # Verify only valid record is returned
        self.assertEqual(len(result), 1)
        self.assertIn("AAPL", result)

    @patch("src.data_sources.eodhd.daily_bulk_eod_data.requests.get")
    @patch("src.data_sources.eodhd.daily_bulk_eod_data.CONFIG.get_eodhd_api_key")
    def test_api_request_error(
        self, mock_get_key: MagicMock, mock_requests_get: MagicMock
    ) -> None:
        """Test handling of API request errors."""
        import requests

        mock_get_key.return_value = "test_api_key"

        # Mock API request failure
        mock_requests_get.side_effect = requests.exceptions.RequestException(
            "API request failed"
        )

        # Verify exception is raised
        with self.assertRaises(requests.exceptions.RequestException):
            self.data_source.get_bulk_latest_eod(exchange="US")

    @patch("src.data_sources.eodhd.daily_bulk_eod_data.requests.get")
    @patch("src.data_sources.eodhd.daily_bulk_eod_data.CONFIG.get_eodhd_api_key")
    def test_unexpected_response_format(
        self, mock_get_key: MagicMock, mock_requests_get: MagicMock
    ) -> None:
        """Test handling of unexpected response format (not a list)."""
        mock_get_key.return_value = "test_api_key"

        # Mock API response with unexpected format
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "Invalid exchange"}
        mock_requests_get.return_value = mock_response

        # Call method
        result = self.data_source.get_bulk_latest_eod(exchange="INVALID")

        # Verify empty dict is returned
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
