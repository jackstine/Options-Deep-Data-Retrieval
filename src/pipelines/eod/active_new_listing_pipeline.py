"""Pipeline for ingesting active company listings with EOD data and quality flags."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import TypedDict

from src.data_sources.base.company_data_source import CompanyDataSource
from src.data_sources.base.historical_data_source import HistoricalDataSource
from src.models.historical_eod_pricing import HistoricalEndOfDayPricing
from src.models.ticker_history import TickerHistory
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
from src.services.companies.company_service import CompanyService


class CompanyStats(TypedDict):
    """Statistics calculated from EOD data for a company."""

    code: str
    name: str
    exchange: str
    min_price: Decimal | None
    max_price: Decimal | None
    average_price: Decimal | None
    median_price: Decimal | None
    missing_days_count: int
    total_trading_days: int
    data_coverage_pct: int  # Basis points (100% = 10000)
    start_date: date | None
    end_date: date | None
    error: str | None


class IngestionResult(TypedDict):
    """Result of active company ingestion process."""

    total_companies: int
    common_stock_count: int
    processed: int
    companies_inserted: int
    tickers_inserted: int
    ticker_histories_inserted: int
    pricing_records_inserted: int
    errors: list[str]


class ActiveNewListingPipeline:
    """Pipeline for ingesting active company listings with EOD data and quality tracking flags."""

    def __init__(
        self,
        company_source: CompanyDataSource | None = None,
        historical_source: HistoricalDataSource | None = None,
        company_repo: CompanyRepository | None = None,
        ticker_repo: TickerRepository | None = None,
        ticker_history_repo: TickerHistoryRepository | None = None,
        pricing_repo: HistoricalEodPricingRepository | None = None,
        stats_repo: TickerHistoryStatsRepository | None = None,
        company_service: CompanyService | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize pipeline with data sources and repositories.

        Args:
            company_source: Source for company/symbol data
            historical_source: Source for historical EOD pricing data
            company_repo: Repository for company operations
            ticker_repo: Repository for ticker operations
            ticker_history_repo: Repository for ticker history operations
            pricing_repo: Repository for EOD pricing operations
            stats_repo: Repository for ticker history stats operations
            company_service: Service for company operations involving joins
            logger: Logger instance for pipeline operations
        """
        self.company_source = company_source
        self.historical_source = historical_source
        self.company_repo = company_repo or CompanyRepository()
        self.ticker_repo = ticker_repo or TickerRepository()
        self.ticker_history_repo = ticker_history_repo or TickerHistoryRepository()
        self.pricing_repo = pricing_repo or HistoricalEodPricingRepository()
        self.stats_repo = stats_repo or TickerHistoryStatsRepository()
        self.company_service = company_service or CompanyService(
            self.company_repo, self.ticker_history_repo
        )
        self.logger = logger or logging.getLogger(__name__)

    def _calculate_eod_stats(
        self, symbol: str, eod_data: list[HistoricalEndOfDayPricing]
    ) -> CompanyStats:
        """Calculate statistics from EOD pricing data.

        Args:
            symbol: Stock ticker symbol
            eod_data: List of historical EOD pricing records

        Returns:
            CompanyStats with calculated metrics
        """
        if not eod_data:
            return CompanyStats(
                code=symbol,
                name="",
                exchange="",
                min_price=None,
                max_price=None,
                average_price=None,
                median_price=None,
                missing_days_count=0,
                total_trading_days=0,
                data_coverage_pct=0,
                start_date=None,
                end_date=None,
                error="No EOD data available",
            )

        # Sort by date to ensure proper ordering
        sorted_data = sorted(eod_data, key=lambda x: x.date)
        start_date = sorted_data[0].date
        end_date = sorted_data[-1].date

        # Calculate price statistics
        prices = [record.close for record in sorted_data]
        min_price = min(prices)
        max_price = max(prices)

        # Calculate average price
        average_price = sum(prices) / len(prices)

        decimal_average_price: Decimal
        if isinstance(average_price, float):
            decimal_average_price = Decimal.from_float(average_price) 
        elif isinstance(average_price, int):
            decimal_average_price = Decimal(average_price)
        else:
            decimal_average_price = average_price

        # Calculate median price
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        if n % 2 == 0:
            # Even number of prices - average the two middle values
            median_price = (sorted_prices[n // 2 - 1] + sorted_prices[n // 2]) / Decimal("2")
        else:
            # Odd number of prices - take the middle value
            median_price = sorted_prices[n // 2]

        # Calculate trading days and coverage
        total_trading_days = len(sorted_data)
        calendar_days = (end_date - start_date).days + 1

        # Estimate expected trading days (weekdays minus ~9 holidays/year)
        # Approximate: 5/7 of calendar days minus holidays
        weeks = calendar_days / 7
        expected_trading_days = int((weeks * 5) - (weeks * 9 / 52))
        expected_trading_days = max(expected_trading_days, total_trading_days)

        missing_days_count = expected_trading_days - total_trading_days

        # Coverage in basis points (100% = 10000)
        if expected_trading_days > 0:
            coverage = int((total_trading_days / expected_trading_days) * 10000)
        else:
            coverage = 0

        
        return CompanyStats(
            code=symbol,
            name="",
            exchange="",
            min_price=min_price,
            max_price=max_price,
            average_price=decimal_average_price,
            median_price=median_price,
            missing_days_count=missing_days_count,
            total_trading_days=total_trading_days,
            data_coverage_pct=coverage,
            start_date=start_date,
            end_date=end_date,
            error=None,
        )

    def run_ingestion(
        self, test_limit: int | None = None
    ) -> IngestionResult:
        """Run the active company ingestion pipeline.

        Args:
            from_date: Optional start date for EOD data (defaults to 1 year ago)
            test_limit: Optional limit on number of companies to process (for testing)

        Returns:
            IngestionResult with counts and status
        """
        if not self.company_source:
            raise ValueError("CompanyDataSource is required")
        if not self.historical_source:
            raise ValueError("HistoricalDataSource is required")

        self.logger.info("Starting active company ingestion pipeline")

        # Get all companies
        all_companies = self.company_source.get_companies()
        self.logger.info(f"Retrieved {len(all_companies)} companies from source")

        # Filter for common stock
        common_stock_companies = [
            c for c in all_companies if c.type and "Common Stock" in c.type
        ]
        self.logger.info(
            f"Filtered to {len(common_stock_companies)} common stock companies"
        )

        # Apply test limit if provided
        if test_limit is not None and test_limit > 0:
            original_count = len(common_stock_companies)
            common_stock_companies = common_stock_companies[:test_limit]
            self.logger.info(
                f"TEST LIMIT APPLIED: Processing only {len(common_stock_companies)} "
                f"companies (limited from {original_count})"
            )

        result: IngestionResult = {
            "total_companies": len(all_companies),
            "common_stock_count": len(common_stock_companies),
            "processed": 0,
            "companies_inserted": 0,
            "tickers_inserted": 0,
            "ticker_histories_inserted": 0,
            "pricing_records_inserted": 0,
            "errors": [],
        }

        for idx, company in enumerate(common_stock_companies, 1):
            symbol = company.ticker.symbol if company.ticker else "UNKNOWN"
            try:
                self.logger.info(
                    f"[{idx}/{len(common_stock_companies)}] Processing {symbol}"
                )

                # Get EOD data
                eod_data = self.historical_source.get_eod_data(
                    symbol
                )

                if not eod_data:
                    self.logger.warning(f"No EOD data for {symbol}, skipping")
                    continue

                # Calculate statistics
                stats = self._calculate_eod_stats(symbol, eod_data)
                stats["name"] = company.company_name
                stats["exchange"] = company.exchange

                # Calculate data quality flags
                has_insufficient_coverage = stats["data_coverage_pct"] < 9000  # < 90%
                low_suspicious_price = stats["max_price"] is not None and stats["max_price"] <= Decimal("1.00")
                high_suspicious_price = stats["max_price"] is not None and stats["max_price"] >= Decimal("1000.00")

                # Insert company data (no longer rejecting based on quality flags)
                self.logger.info(f"Inserting company {symbol}")

                # 1. Insert/update company
                existing_company_data = self.company_service.get_company_by_ticker(symbol)
                company_id : int
                if existing_company_data:
                    self.company_service.update_company(symbol, company)
                    
                    if existing_company_data.company.id is None:
                        raise ValueError("id of existing company cannot be None")
                    company_id = existing_company_data.company.id
                else:
                    # Insert company - need to get ID
                    inserted = self.company_repo.bulk_insert_companies([company])
                    result["companies_inserted"] += len(inserted)
                    # Use the inserted company's ID directly
                    if not inserted or not inserted[0].id:
                        raise ValueError(f"Failed to insert company: {symbol}")
                    company_id = inserted[0].id

                # 2. Insert ticker_history FIRST (required for ticker FK)
                ticker_history = TickerHistory(
                    symbol=symbol,
                    company_id=company_id,
                    valid_from=stats["start_date"] or date.today(),
                    valid_to=None,
                )
                inserted_histories = self.ticker_history_repo.bulk_insert_ticker_histories(
                    [ticker_history]
                )
                result["ticker_histories_inserted"] += len(inserted_histories)

                # Use the inserted ticker_history's ID directly
                if not inserted_histories or not inserted_histories[0].id:
                    raise ValueError(f"Failed to insert ticker_history: {symbol}")
                ticker_history_id = inserted_histories[0].id

                # 3. Insert ticker with ticker_history_id
                existing_ticker = self.ticker_repo.get_ticker_by_symbol(symbol)
                if not existing_ticker:
                    self.ticker_repo.create_ticker_for_company(
                        symbol, company_id, ticker_history_id
                    )
                    result["tickers_inserted"] += 1
                else:
                    self.logger.info(f"Ticker {symbol} already exists, skipping insert")

                # 4. Insert ticker_history_stats with quality flags
                ticker_stats = TickerHistoryStats(
                    ticker_history_id=ticker_history_id,
                    data_coverage_pct=stats["data_coverage_pct"],
                    min_price=stats["min_price"],
                    max_price=stats["max_price"],
                    average_price=stats["average_price"],
                    median_price=stats["median_price"],
                    has_insufficient_coverage=has_insufficient_coverage,
                    low_suspicious_price=low_suspicious_price,
                    high_suspicious_price=high_suspicious_price,
                )
                self.stats_repo.upsert_stats(ticker_stats)

                # 5. Bulk insert EOD pricing data (uses ticker_history_id, not ticker_id)
                for record in eod_data:
                    record.ticker_history_id = ticker_history_id

                pricing_result = self.pricing_repo.bulk_upsert_pricing(
                    ticker_history_id, eod_data
                )
                result["pricing_records_inserted"] += pricing_result.get("inserted", 0)

                result["processed"] += 1

            except Exception as e:
                self.logger.exception(f"Error processing {symbol}: {e}")
                result["errors"].append(f"{symbol}: {str(e)}")

        self.logger.info("Active company ingestion pipeline completed")
        return result
