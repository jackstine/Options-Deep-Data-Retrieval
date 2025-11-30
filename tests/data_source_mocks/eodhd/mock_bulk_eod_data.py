"""Mock EODHD bulk EOD data source for testing."""

from __future__ import annotations

import csv
import logging
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.data_sources.base.bulk_eod_data_source import BulkEodDataSource
from src.database.equities.enums import DataSourceEnum
from src.models.misplaced_eod_pricing import MisplacedEndOfDayPricing
from tests.data_source_mocks.eodhd.mock_symbols import MockEodhdSymbolsSource

logger = logging.getLogger(__name__)


class MockEodhdDailyBulkEodData(BulkEodDataSource):
    """Mock EODHD bulk EOD data source that reads from fixture files instead of API."""

    def __init__(self) -> None:
        """Initialize mock EODHD bulk EOD data source."""
        self.fixtures_dir = Path(__file__).parent / "fixtures"

    @property
    def name(self) -> str:
        """Name of the data source."""
        return "Mock EODHD Bulk EOD Data"

    def is_available(self) -> bool:
        """Check if mock data source is available.

        Returns:
            Always returns True for mock data source
        """
        return True

    def get_bulk_latest_eod(
        self,
        exchange: str = "US",
        filter_common_stock: bool = True,
    ) -> dict[str, MisplacedEndOfDayPricing]:
        """Get latest end-of-day data for all symbols in an exchange from fixture file.

        Args:
            exchange: Exchange code (ignored in mock, always returns US symbols)
            filter_common_stock: If True, only return Common Stock symbols

        Returns:
            Dictionary mapping symbol (str) to MisplacedEndOfDayPricing instance
        """
        fixture_file = self.fixtures_dir / "bulk_eod.csv"

        try:
            with open(fixture_file, newline='') as f:
                reader = csv.DictReader(f)

                pricing_dict: dict[str, MisplacedEndOfDayPricing] = {}
                for row in reader:
                    try:
                        # Extract symbol (remove .US suffix if present)
                        code = row.get("Code", "")
                        symbol = code.split(".")[0] if "." in code else code

                        if not symbol:
                            logger.warning(f"Skipping record with missing symbol: {row}")
                            continue

                        # Parse date
                        date_str = row.get("Date")
                        if not date_str:
                            logger.warning(f"Skipping {symbol}: missing date")
                            continue
                        pricing_date = date.fromisoformat(date_str)

                        # Create MisplacedEndOfDayPricing instance
                        pricing = MisplacedEndOfDayPricing(
                            symbol=symbol,
                            date=pricing_date,
                            open=Decimal(str(row.get("Open", 0))),
                            high=Decimal(str(row.get("High", 0))),
                            low=Decimal(str(row.get("Low", 0))),
                            close=Decimal(str(row.get("Close", 0))),
                            adjusted_close=Decimal(str(row.get("Adjusted_close", 0))),
                            volume=int(row.get("Volume", 0)),
                            source=DataSourceEnum.EODHD,
                        )

                        pricing_dict[symbol] = pricing

                    except (ValueError, TypeError, KeyError) as e:
                        logger.warning(
                            f"Failed to parse record for symbol {row.get('Code', 'unknown')}: {e}"
                        )
                        continue

            logger.info(
                f"Loaded {len(pricing_dict)} EOD records for exchange {exchange} from fixture"
            )

            # Filter for Common Stock if requested
            if filter_common_stock:
                logger.info("Filtering for Common Stock symbols...")
                symbols_source = MockEodhdSymbolsSource()
                companies = symbols_source.get_active_symbols()

                # Create mapping of symbol to company
                symbol_info = {
                    company.ticker.symbol: company
                    for company in companies
                    if company.ticker and company.ticker.symbol
                }

                # Filter to keep only Common Stock symbols
                original_count = len(pricing_dict)
                pricing_dict = {
                    symbol: pricing
                    for symbol, pricing in pricing_dict.items()
                    if symbol in symbol_info and symbol_info[symbol].type == "Common Stock"
                }

                logger.info(
                    f"Filtered from {original_count} to {len(pricing_dict)} Common Stock symbols"
                )

            return pricing_dict

        except FileNotFoundError:
            logger.error(f"Fixture file not found: {fixture_file}")
            return {}
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return {}
