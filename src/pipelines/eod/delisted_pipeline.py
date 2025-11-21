"""Pipeline for ingesting delisted company data with historical EOD pricing."""

from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, TypedDict

from src.data_sources.base.company_data_source import CompanyDataSource
from src.data_sources.base.historical_data_source import HistoricalDataSource
from src.models.company import Company
from src.models.historical_eod_pricing import HistoricalEndOfDayPricing
from src.models.ticker import Ticker
from src.models.ticker_history_stats import TickerHistoryStats
from src.repos.equities.companies.company_repository import CompanyRepository
from src.repos.equities.pricing.historical_eod_pricing_repository import (
    HistoricalEodPricingRepository,
)
from src.repos.equities.tickers.ticker_history_repository import (
    TickerHistoryRepository,
)
from src.repos.equities.tickers.ticker_history_stats_repository import (
    TickerHistoryStatsRepository,
)
from src.repos.equities.tickers.ticker_repository import TickerRepository
from src.utils.trading_calendar import get_missing_trading_days

logger = logging.getLogger(__name__)


class StockMetrics(TypedDict):
    """Type definition for stock analysis metrics."""

    code: str
    name: str
    exchange: str
    min_price: Decimal
    max_price: Decimal
    missing_days_count: int
    total_trading_days: int
    data_coverage_pct: float
    start_date: date
    end_date: date
    error: str | None


class DelistedIngestionResult(TypedDict):
    """Result of delisted company ingestion operation."""

    total_companies: int
    companies_inserted: int
    companies_updated: int
    ticker_histories_created: int
    stats_upserted: int
    pricing_records_inserted: int
    pricing_records_updated: int
    failed_companies: int
    failed_symbols: list[dict[str, Any]]


class DelistedCompanyPipeline:
    """Pipeline for ingesting delisted companies with historical EOD pricing data."""

    VALID_EXCHANGES = ["NASDAQ", "NYSE", "NYSE_MKT", "NYSE ARCA", "AMEX"]
    MAX_VALID_PRICE = Decimal("1000.0")
    MIN_VALID_COVERAGE = 90.0

    def __init__(
        self,
        company_repo: CompanyRepository | None = None,
        ticker_repo: TickerRepository | None = None,
        ticker_history_repo: TickerHistoryRepository | None = None,
        ticker_history_stats_repo: TickerHistoryStatsRepository | None = None,
        pricing_repo: HistoricalEodPricingRepository | None = None,
        logger_instance: logging.Logger | None = None,
    ) -> None:
        """Initialize delisted company pipeline with dependency injection.

        Args:
            company_repo: Repository for company operations
            ticker_repo: Repository for ticker operations
            ticker_history_repo: Repository for ticker history operations
            ticker_history_stats_repo: Repository for ticker history stats operations
            pricing_repo: Repository for historical pricing operations
            logger_instance: Logger instance for this pipeline
        """
        self.company_repo = company_repo or CompanyRepository()
        self.ticker_repo = ticker_repo or TickerRepository()
        self.ticker_history_repo = ticker_history_repo or TickerHistoryRepository()
        self.ticker_history_stats_repo = (
            ticker_history_stats_repo or TickerHistoryStatsRepository()
        )
        self.pricing_repo = pricing_repo or HistoricalEodPricingRepository()
        self.logger = logger_instance or logger

    def ingest_delisted_companies(
        self,
        company_source: CompanyDataSource,
        historical_source: HistoricalDataSource,
    ) -> DelistedIngestionResult:
        """Ingest delisted companies with historical EOD data.

        Args:
            company_source: Data source for fetching delisted companies
            historical_source: Data source for fetching historical EOD pricing

        Returns:
            DelistedIngestionResult with counts of operations performed
        """
        result: DelistedIngestionResult = {
            "total_companies": 0,
            "companies_inserted": 0,
            "companies_updated": 0,
            "ticker_histories_created": 0,
            "stats_upserted": 0,
            "pricing_records_inserted": 0,
            "pricing_records_updated": 0,
            "failed_companies": 0,
            "failed_symbols": [],
        }

        # Fetch delisted companies
        self.logger.info("Fetching delisted companies from data source...")
        delisted_companies = company_source.get_delisted_symbols()
        result["total_companies"] = len(delisted_companies)
        self.logger.info(f"Found {len(delisted_companies)} delisted companies to process")

        # Process each company
        for idx, company in enumerate(delisted_companies, start=1):
            # Log progress every 50 companies
            if idx % 50 == 0 or idx == 1:
                self.logger.info(
                    f"Processing company {idx}/{len(delisted_companies)}: {company.ticker.symbol if company.ticker else 'N/A'}"
                )

            process_result = self._process_single_company(company, historical_source)

            # Update result counters
            if process_result["success"]:
                if process_result["company_inserted"]:
                    result["companies_inserted"] += 1
                elif process_result["company_updated"]:
                    result["companies_updated"] += 1

                if process_result["ticker_history_created"]:
                    result["ticker_histories_created"] += 1
                if process_result["stats_upserted"]:
                    result["stats_upserted"] += 1

                result["pricing_records_inserted"] += process_result["pricing_inserted"]
                result["pricing_records_updated"] += process_result["pricing_updated"]
            else:
                result["failed_companies"] += 1
                result["failed_symbols"].append(process_result["failed_company_info"])

        self.logger.info("Delisted company ingestion complete!")
        return result

    def _process_single_company(
        self,
        company: Company,
        historical_source: HistoricalDataSource,
    ) -> dict[str, Any]:
        """Process a single delisted company.

        Args:
            company: Company to process
            historical_source: Data source for historical pricing

        Returns:
            Dictionary with processing results
        """
        result = {
            "success": False,
            "company_inserted": False,
            "company_updated": False,
            "ticker_history_created": False,
            "stats_upserted": False,
            "pricing_inserted": 0,
            "pricing_updated": 0,
            "failed_company_info": {},
        }

        symbol = company.ticker.symbol if company.ticker else None
        if not symbol:
            self.logger.warning(f"Company has no ticker symbol: {company.company_name}")
            result["failed_company_info"] = {
                "code": "N/A",
                "name": company.company_name,
                "exchange": company.exchange,
                "error": "No ticker symbol",
            }
            return result

        try:
            # Fetch EOD data
            eod_data = historical_source.get_eod_data(symbol)

            if not eod_data:
                # No EOD data - still insert company but mark as invalid
                self.logger.warning(f"No EOD data found for {symbol}")
                company.is_valid_data = False
                result["failed_company_info"] = {
                    "code": symbol,
                    "name": company.company_name,
                    "exchange": company.exchange,
                    "error": "No EOD data available",
                }

                # Insert company record anyway
                existing_company = self.company_repo.get_company_by_ticker(symbol)
                if existing_company:
                    self.company_repo.update_company(symbol, company)
                    result["company_updated"] = True
                else:
                    self.company_repo.insert(company)
                    result["company_inserted"] = True

                return result

            # Calculate metrics from EOD data
            metrics = self._calculate_metrics(symbol, company.company_name, company.exchange, eod_data)

            if metrics["error"]:
                # Error calculating metrics
                self.logger.warning(f"Error calculating metrics for {symbol}: {metrics['error']}")
                company.is_valid_data = False
                result["failed_company_info"] = {
                    "code": symbol,
                    "name": company.company_name,
                    "exchange": company.exchange,
                    "error": metrics["error"],
                }

                # Insert company record anyway
                existing_company = self.company_repo.get_company_by_ticker(symbol)
                if existing_company:
                    self.company_repo.update_company(symbol, company)
                    result["company_updated"] = True
                else:
                    self.company_repo.insert(company)
                    result["company_inserted"] = True

                return result

            # Calculate is_valid_data flag
            company.is_valid_data = self._calculate_is_valid_data(company.exchange, metrics)

            # Insert or update company
            existing_company = self.company_repo.get_company_by_ticker(symbol)
            if existing_company:
                company.id = existing_company.id
                self.company_repo.update_company(symbol, company)
                result["company_updated"] = True
                company_id = existing_company.id
            else:
                # Use insert() instead of bulk_insert to get the ID back
                inserted_company = self.company_repo.insert(company)
                result["company_inserted"] = True
                company_id = inserted_company.id

            if not company_id:
                raise Exception(f"Failed to get company_id for {symbol}")

            # NOTE: We do NOT create ticker records for delisted companies
            # The ticker table is only for currently active/trading symbols
            # Delisted companies only get ticker_history records

            # Check if ticker history already exists
            existing_histories = self.ticker_history_repo.get_ticker_history_for_company(company_id)
            matching_history = None
            for hist in existing_histories:
                if hist.symbol == symbol and hist.valid_from == metrics["start_date"]:
                    matching_history = hist
                    break

            if matching_history:
                ticker_history_id = matching_history.id
            else:
                # Create ticker_history with valid_to = max EOD date
                created_history = self.ticker_history_repo.create_ticker_history_for_company(
                    symbol=symbol,
                    company_id=company_id,
                    valid_from=metrics["start_date"],
                    valid_to=metrics["end_date"],
                )
                result["ticker_history_created"] = True
                ticker_history_id = created_history.id

            if not ticker_history_id:
                raise Exception(f"Failed to get ticker_history_id for {symbol}")

            # Create ticker history stats
            stats = TickerHistoryStats(
                ticker_history_id=ticker_history_id,
                data_coverage_pct=int(metrics["data_coverage_pct"] * 100),  # Convert to basis points
                min_price=metrics["min_price"],
                max_price=metrics["max_price"],
            )
            self.ticker_history_stats_repo.upsert_stats(stats)
            result["stats_upserted"] = True

            # Bulk insert pricing data using ticker_history_id
            # NOTE: historical_eod_pricing uses ticker_history_id to support both active and delisted symbols
            for eod in eod_data:
                eod.ticker_history_id = ticker_history_id

            pricing_result = self.pricing_repo.bulk_upsert_pricing(ticker_history_id, eod_data)
            result["pricing_inserted"] = pricing_result.get("inserted", 0)
            result["pricing_updated"] = pricing_result.get("updated", 0)

            result["success"] = True
            return result

        except Exception as e:
            self.logger.error(f"Error processing company {symbol}: {e}")
            result["failed_company_info"] = {
                "code": symbol,
                "name": company.company_name,
                "exchange": company.exchange,
                "error": str(e),
            }

            # Try to insert company with is_valid_data=False
            try:
                company.is_valid_data = False
                existing_company = self.company_repo.get_company_by_ticker(symbol)
                if existing_company:
                    self.company_repo.update_company(symbol, company)
                    result["company_updated"] = True
                else:
                    self.company_repo.insert(company)
                    result["company_inserted"] = True
            except Exception as insert_error:
                self.logger.error(f"Failed to insert company {symbol} after error: {insert_error}")

            return result

    def _calculate_metrics(
        self,
        code: str,
        name: str,
        exchange: str,
        eod_data: list[HistoricalEndOfDayPricing],
    ) -> StockMetrics:
        """Calculate metrics from EOD data.

        Args:
            code: Stock ticker code
            name: Stock name
            exchange: Exchange the stock trades on
            eod_data: List of historical EOD pricing records

        Returns:
            StockMetrics dictionary with calculated values
        """
        metrics: StockMetrics = {
            "code": code,
            "name": name,
            "exchange": exchange,
            "min_price": Decimal("0"),
            "max_price": Decimal("0"),
            "missing_days_count": 0,
            "total_trading_days": 0,
            "data_coverage_pct": 0.0,
            "start_date": date.today(),
            "end_date": date.today(),
            "error": None,
        }

        try:
            if not eod_data:
                metrics["error"] = "No EOD data"
                return metrics

            # Extract dates and prices
            dates: set[date] = set()
            low_prices: list[Decimal] = []
            high_prices: list[Decimal] = []

            for record in eod_data:
                dates.add(record.date)
                low_prices.append(record.low)
                high_prices.append(record.high)

            if not dates or not low_prices or not high_prices:
                metrics["error"] = "No valid price data"
                return metrics

            # Calculate min/max prices
            metrics["min_price"] = min(low_prices)
            metrics["max_price"] = max(high_prices)

            # Determine date range
            date_list = sorted(dates)
            start_date = date_list[0]
            end_date = date_list[-1]
            metrics["start_date"] = start_date
            metrics["end_date"] = end_date

            # Calculate missing trading days
            missing_days = get_missing_trading_days(dates, start_date, end_date)
            metrics["missing_days_count"] = len(missing_days)

            # Calculate total expected trading days
            metrics["total_trading_days"] = len(dates) + len(missing_days)

            # Calculate coverage percentage
            if metrics["total_trading_days"] > 0:
                metrics["data_coverage_pct"] = (
                    len(dates) / metrics["total_trading_days"]
                ) * 100.0
            else:
                metrics["data_coverage_pct"] = 0.0

        except Exception as e:
            metrics["error"] = f"Error calculating metrics: {str(e)}"

        return metrics

    def _calculate_is_valid_data(self, exchange: str, metrics: StockMetrics) -> bool:
        """Calculate the is_valid_data flag based on exchange and metrics.

        Logic:
        - If exchange is in valid exchanges list → return True
        - Else → must meet coverage > 90% AND max_price <= $1000

        Args:
            exchange: Exchange the stock trades on
            metrics: Calculated stock metrics

        Returns:
            True if data is valid, False otherwise
        """
        if exchange in self.VALID_EXCHANGES:
            return True
        else:
            return (
                metrics["data_coverage_pct"] > self.MIN_VALID_COVERAGE
                and metrics["max_price"] <= self.MAX_VALID_PRICE
            )
