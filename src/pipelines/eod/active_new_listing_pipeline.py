"""Pipeline for ingesting active company listings with EOD data validation."""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TypedDict

from src.data_sources.base.company_data_source import CompanyDataSource
from src.data_sources.base.historical_data_source import HistoricalDataSource
from src.models.company import Company
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


class CompanyStats(TypedDict):
    """Statistics calculated from EOD data for a company."""

    code: str
    name: str
    exchange: str
    min_price: Decimal | None
    max_price: Decimal | None
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
    valid_companies: int
    invalid_companies: int
    companies_inserted: int
    tickers_inserted: int
    ticker_histories_inserted: int
    pricing_records_inserted: int
    failed_symbols: list[str]
    errors: list[str]


VALID_EXCHANGES = {"NASDAQ", "NYSE", "NYSE_MKT", "NYSE ARCA", "AMEX"}
MAX_PRICE_THRESHOLD = Decimal("1000.00")
MIN_COVERAGE_PCT = 9000  # 90% in basis points


class ActiveNewListingPipeline:
    """Pipeline for ingesting and validating active company listings with EOD data."""

    def __init__(
        self,
        company_source: CompanyDataSource | None = None,
        historical_source: HistoricalDataSource | None = None,
        company_repo: CompanyRepository | None = None,
        ticker_repo: TickerRepository | None = None,
        ticker_history_repo: TickerHistoryRepository | None = None,
        pricing_repo: HistoricalEodPricingRepository | None = None,
        stats_repo: TickerHistoryStatsRepository | None = None,
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
            logger: Logger instance for pipeline operations
        """
        self.company_source = company_source
        self.historical_source = historical_source
        self.company_repo = company_repo or CompanyRepository()
        self.ticker_repo = ticker_repo or TickerRepository()
        self.ticker_history_repo = ticker_history_repo or TickerHistoryRepository()
        self.pricing_repo = pricing_repo or HistoricalEodPricingRepository()
        self.stats_repo = stats_repo or TickerHistoryStatsRepository()
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
            missing_days_count=missing_days_count,
            total_trading_days=total_trading_days,
            data_coverage_pct=coverage,
            start_date=start_date,
            end_date=end_date,
            error=None,
        )

    def _is_valid_data(
        self, company: Company, stats: CompanyStats
    ) -> tuple[bool, str | None]:
        """Validate company data based on exchange, coverage, and price criteria.

        Args:
            company: Company object with exchange info
            stats: CompanyStats with calculated metrics

        Returns:
            Tuple of (is_valid, reason) where reason is None if valid
        """
        # Check exchange
        if company.exchange not in VALID_EXCHANGES:
            return False, f"Invalid exchange: {company.exchange}"

        # Check coverage
        if stats["data_coverage_pct"] <= MIN_COVERAGE_PCT:
            coverage_pct = stats["data_coverage_pct"] / 100.0
            return False, f"Insufficient coverage: {coverage_pct:.2f}%"

        # Check max price
        if stats["max_price"] and stats["max_price"] > MAX_PRICE_THRESHOLD:
            return False, f"Max price too high: ${stats['max_price']:.2f}"

        return True, None

    def _write_failed_company_data(
        self,
        company: Company,
        stats: CompanyStats,
        eod_data: list[HistoricalEndOfDayPricing],
        reason: str,
    ) -> None:
        """Write failed company data to filesystem.

        Args:
            company: Company that failed validation
            stats: Statistics for the company
            eod_data: EOD pricing data
            reason: Reason for failure
        """
        symbol = company.ticker.symbol if company.ticker else stats["code"]
        output_dir = Path("src/data_sources/eodhd/data/failed_eod_active") / symbol
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write company info
        company_file = output_dir / "company.json"
        company_data = company.to_dict()
        company_data["validation_failure_reason"] = reason
        with open(company_file, "w") as f:
            json.dump(company_data, f, indent=2, default=str)

        # Write stats
        stats_file = output_dir / "stats.json"
        with open(stats_file, "w") as f:
            json.dump(dict(stats), f, indent=2, default=str)

        # Write EOD data
        eod_file = output_dir / "eod_data.json"
        eod_records = [record.to_dict() for record in eod_data]
        with open(eod_file, "w") as f:
            json.dump(eod_records, f, indent=2, default=str)

        self.logger.info(
            f"Wrote failed company data for {symbol} to {output_dir}"
        )

    def _generate_failed_report(
        self, failed_companies: list[tuple[Company, CompanyStats, str]]
    ) -> None:
        """Generate markdown report of failed companies.

        Args:
            failed_companies: List of tuples (company, stats, reason)
        """
        if not failed_companies:
            self.logger.info("No failed companies to report")
            return

        report_path = Path("reports/failed_active_eod_report.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w") as f:
            f.write("# Failed Active EOD Company Report\n\n")
            f.write(f"Generated: {date.today()}\n\n")
            f.write(f"Total Failed: {len(failed_companies)}\n\n")
            f.write("---\n\n")

            # Summary by failure reason
            f.write("## Failure Reasons Summary\n\n")
            reason_counts: dict[str, int] = {}
            for _, _, reason in failed_companies:
                reason_key = reason.split(":")[0] if ":" in reason else reason
                reason_counts[reason_key] = reason_counts.get(reason_key, 0) + 1

            for reason, count in sorted(
                reason_counts.items(), key=lambda x: x[1], reverse=True
            ):
                f.write(f"- {reason}: {count}\n")

            f.write("\n---\n\n")

            # Detailed table
            f.write("## Detailed Failed Companies\n\n")
            f.write(
                "| Code | Name | Exchange | Min Price | Max Price | "
                "Missing Days | Total Days | Coverage % | Start Date | End Date | Error |\n"
            )
            f.write(
                "|------|------|----------|-----------|-----------|"
                "--------------|------------|------------|------------|----------|-------|\n"
            )

            for company, stats, reason in failed_companies:
                symbol = company.ticker.symbol if company.ticker else stats["code"]
                name = company.company_name or stats["name"]
                exchange = company.exchange or stats["exchange"]
                min_price = (
                    f"${stats['min_price']:.2f}" if stats["min_price"] else "N/A"
                )
                max_price = (
                    f"${stats['max_price']:.2f}" if stats["max_price"] else "N/A"
                )
                coverage = stats["data_coverage_pct"] / 100.0
                start = stats["start_date"] or "N/A"
                end = stats["end_date"] or "N/A"

                f.write(
                    f"| {symbol} | {name} | {exchange} | {min_price} | {max_price} | "
                    f"{stats['missing_days_count']} | {stats['total_trading_days']} | "
                    f"{coverage:.2f}% | {start} | {end} | {reason} |\n"
                )

        self.logger.info(f"Generated failed companies report at {report_path}")

    def run_ingestion(self, from_date: date | None = None) -> IngestionResult:
        """Run the active company ingestion pipeline.

        Args:
            from_date: Optional start date for EOD data (defaults to 1 year ago)

        Returns:
            IngestionResult with counts and status
        """
        if not self.company_source:
            raise ValueError("CompanyDataSource is required")
        if not self.historical_source:
            raise ValueError("HistoricalDataSource is required")

        # Default to 1 year of data
        if from_date is None:
            from_date = date.today() - timedelta(days=365)

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

        result: IngestionResult = {
            "total_companies": len(all_companies),
            "common_stock_count": len(common_stock_companies),
            "processed": 0,
            "valid_companies": 0,
            "invalid_companies": 0,
            "companies_inserted": 0,
            "tickers_inserted": 0,
            "ticker_histories_inserted": 0,
            "pricing_records_inserted": 0,
            "failed_symbols": [],
            "errors": [],
        }

        failed_companies: list[tuple[Company, CompanyStats, str]] = []

        for idx, company in enumerate(common_stock_companies, 1):
            symbol = company.ticker.symbol if company.ticker else "UNKNOWN"

            try:
                self.logger.info(
                    f"[{idx}/{len(common_stock_companies)}] Processing {symbol}"
                )

                # Get EOD data
                eod_data = self.historical_source.get_eod_data(
                    symbol, from_date=from_date
                )

                if not eod_data:
                    self.logger.warning(f"No EOD data for {symbol}")
                    stats = self._calculate_eod_stats(symbol, [])
                    stats["name"] = company.company_name
                    stats["exchange"] = company.exchange
                    failed_companies.append((company, stats, "No EOD data"))
                    result["invalid_companies"] += 1
                    result["failed_symbols"].append(symbol)
                    self._write_failed_company_data(
                        company, stats, [], "No EOD data"
                    )
                    continue

                # Calculate statistics
                stats = self._calculate_eod_stats(symbol, eod_data)
                stats["name"] = company.company_name
                stats["exchange"] = company.exchange

                # Validate data
                is_valid, reason = self._is_valid_data(company, stats)

                if not is_valid:
                    self.logger.info(f"Invalid data for {symbol}: {reason}")
                    failed_companies.append((company, stats, reason or "Unknown"))
                    result["invalid_companies"] += 1
                    result["failed_symbols"].append(symbol)
                    self._write_failed_company_data(
                        company, stats, eod_data, reason or "Validation failed"
                    )
                    continue

                # Insert valid company data
                self.logger.info(f"Inserting valid company {symbol}")

                # 1. Insert/update company
                existing_company = self.company_repo.get_company_by_ticker(symbol)
                company_id : int
                if existing_company:
                    self.company_repo.update_company(symbol, company)
                    if existing_company.id is None:
                        raise ValueError("id of existing company cannot be None")
                    company_id = existing_company.id
                else:
                    # Insert company - need to get ID
                    inserted = self.company_repo.bulk_insert_companies([company])
                    result["companies_inserted"] += inserted
                    # Retrieve to get ID
                    company_db = self.company_repo.get_company_by_ticker(symbol)
                    if not company_db:
                        raise ValueError(f"Failed to retrieve company after insert: {symbol}")
                    if company_db.id is None:
                        raise ValueError("id of company db cannot be None")
                    company_id = company_db.id

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
                result["ticker_histories_inserted"] += inserted_histories

                # Get the ticker_history_id (required for ticker FK constraint)
                ticker_histories = self.ticker_history_repo.get_ticker_history_by_symbol(
                    symbol
                )
                if not ticker_histories:
                    raise ValueError(f"Failed to retrieve ticker_history after insert: {symbol}")

                ticker_history_id = ticker_histories[0].id

                # 3. Insert ticker with ticker_history_id
                existing_ticker = self.ticker_repo.get_ticker_by_symbol(symbol)
                if not existing_ticker:
                    self.ticker_repo.create_ticker_for_company(
                        symbol, company_id, ticker_history_id
                    )
                    result["tickers_inserted"] += 1
                else:
                    self.logger.info(f"Ticker {symbol} already exists, skipping insert")

                # 4. Insert ticker_history_stats
                ticker_stats = TickerHistoryStats(
                    ticker_history_id=ticker_history_id,
                    data_coverage_pct=stats["data_coverage_pct"],
                    min_price=stats["min_price"],
                    max_price=stats["max_price"],
                )
                self.stats_repo.upsert_stats(ticker_stats)

                # 5. Bulk insert EOD pricing data (uses ticker_history_id, not ticker_id)
                for record in eod_data:
                    record.ticker_history_id = ticker_history_id

                pricing_result = self.pricing_repo.bulk_upsert_pricing(
                    ticker_history_id, eod_data
                )
                result["pricing_records_inserted"] += pricing_result.get("inserted", 0)

                result["valid_companies"] += 1
                result["processed"] += 1

            except Exception as e:
                self.logger.exception(f"Error processing {symbol}: {e}")
                result["errors"].append(f"{symbol}: {str(e)}")
                result["failed_symbols"].append(symbol)

        # Generate report for failed companies
        if failed_companies:
            self._generate_failed_report(failed_companies)

        self.logger.info("Active company ingestion pipeline completed")
        return result
