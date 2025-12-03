"""Reusable test fixtures for integration tests.

This module provides DRY helper functions for common test setup patterns.
These fixtures reduce code duplication across integration tests and make tests
more maintainable.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from src.database.equities.enums import DataSourceEnum
from src.models.company import Company
from src.models.historical_eod_pricing import HistoricalEndOfDayPricing
from src.models.split import Split
from src.models.ticker import Ticker
from src.models.ticker_history import TickerHistory

if TYPE_CHECKING:
    from src.repos.equities.companies.company_repository import CompanyRepository
    from src.repos.equities.pricing.historical_eod_pricing_repository import (
        HistoricalEodPricingRepository,
    )
    from src.repos.equities.splits.splits_repository import SplitsRepository
    from src.repos.equities.tickers.ticker_history_repository import (
        TickerHistoryRepository,
    )
    from src.repos.equities.tickers.ticker_repository import TickerRepository


def create_company_with_ticker(
    company_repo: CompanyRepository,
    ticker_repo: TickerRepository,
    ticker_history_repo: TickerHistoryRepository,
    company_name: str,
    symbol: str,
    exchange: str,
    active: bool = True,
    source: DataSourceEnum = DataSourceEnum.EODHD,
    sector: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    market_cap: int | None = None,
    description: str | None = None,
    is_valid_data: bool = True,
    valid_from: date = date(2020, 1, 1),
    valid_to: date | None = None,
) -> tuple[Company, Ticker, TickerHistory]:
    """Create a complete company with ticker and ticker_history.

    This is a common pattern used across many integration tests. It creates all three
    related entities and properly links them together.

    Args:
        company_repo: Repository for companies
        ticker_repo: Repository for tickers
        ticker_history_repo: Repository for ticker histories
        company_name: Name of the company
        symbol: Ticker symbol
        exchange: Exchange code (e.g., "NYSE", "NASDAQ")
        active: Whether company is active (default: True)
        source: Data source enum (default: EODHD)
        sector: Optional sector
        industry: Optional industry
        country: Optional country code
        market_cap: Optional market capitalization
        description: Optional company description
        is_valid_data: Whether data is valid (default: True)
        valid_from: Ticker history valid_from date (default: 2020-01-01)
        valid_to: Ticker history valid_to date (default: None for active)

    Returns:
        Tuple of (inserted_company, ticker, ticker_history)
    """
    # Create and insert company
    company = Company(
        company_name=company_name,
        exchange=exchange,
        active=active,
        source=source,
        sector=sector,
        industry=industry,
        country=country,
        market_cap=market_cap,
        description=description,
        is_valid_data=is_valid_data,
    )
    inserted_company = company_repo.insert(company)

    # Create and insert ticker_history
    ticker_history = TickerHistory(
        symbol=symbol,
        company_id=inserted_company.id,
        valid_from=valid_from,
        valid_to=valid_to,
    )
    inserted_ticker_history = ticker_history_repo.insert(ticker_history)

    # Create and insert ticker
    ticker = Ticker(
        symbol=symbol,
        company_id=inserted_company.id,
        ticker_history_id=inserted_ticker_history.id,
    )
    inserted_ticker = ticker_repo.insert(ticker)

    return inserted_company, inserted_ticker, inserted_ticker_history


def bulk_create_companies_with_tickers(
    company_repo: CompanyRepository,
    ticker_repo: TickerRepository,
    ticker_history_repo: TickerHistoryRepository,
    scenarios: list[dict[str, any]],
) -> list[tuple[Company, Ticker, TickerHistory]]:
    """Create multiple companies with tickers from a list of scenarios.

    Each scenario dict should contain the same fields as create_company_with_ticker().
    At minimum, each scenario must have: company_name, symbol, exchange.

    Args:
        company_repo: Repository for companies
        ticker_repo: Repository for tickers
        ticker_history_repo: Repository for ticker histories
        scenarios: List of dicts with company/ticker data

    Returns:
        List of tuples of (inserted_company, ticker, ticker_history)
    """
    results = []
    for scenario in scenarios:
        company, ticker, ticker_history = create_company_with_ticker(
            company_repo=company_repo,
            ticker_repo=ticker_repo,
            ticker_history_repo=ticker_history_repo,
            company_name=scenario["company_name"],
            symbol=scenario["symbol"],
            exchange=scenario["exchange"],
            active=scenario.get("active", True),
            source=scenario.get("source", DataSourceEnum.EODHD),
            sector=scenario.get("sector"),
            industry=scenario.get("industry"),
            country=scenario.get("country"),
            market_cap=scenario.get("market_cap"),
            description=scenario.get("description"),
            is_valid_data=scenario.get("is_valid_data", True),
            valid_from=scenario.get("valid_from", date(2020, 1, 1)),
            valid_to=scenario.get("valid_to"),
        )
        results.append((company, ticker, ticker_history))
    return results


def insert_pricing_data(
    pricing_repo: HistoricalEodPricingRepository,
    ticker_history_id: int,
    pricing_data: list[dict[str, any]],
) -> list[HistoricalEndOfDayPricing]:
    """Insert historical pricing data for a ticker_history.

    Each pricing_data dict should contain: date, open, high, low, close,
    adjusted_close, volume.

    Args:
        pricing_repo: Repository for historical pricing
        ticker_history_id: ID of the ticker_history to associate pricing with
        pricing_data: List of dicts with pricing data

    Returns:
        List of inserted pricing models
    """
    pricing_models = [
        HistoricalEndOfDayPricing(
            ticker_history_id=ticker_history_id,
            date=p["date"],
            open=p["open"],
            high=p["high"],
            low=p["low"],
            close=p["close"],
            adjusted_close=p["adjusted_close"],
            volume=p["volume"],
        )
        for p in pricing_data
    ]

    pricing_repo.bulk_upsert_pricing(ticker_history_id, pricing_models)
    return pricing_models


def insert_splits(
    splits_repo: SplitsRepository,
    ticker_history_id: int,
    symbol: str | None,
    splits_data: list[dict[str, any]],
) -> list[Split]:
    """Insert split data for a ticker_history.

    Each splits_data dict should contain: date, split_ratio.

    Args:
        splits_repo: Repository for splits
        ticker_history_id: ID of the ticker_history to associate splits with
        symbol: Optional symbol for display purposes
        splits_data: List of dicts with split data

    Returns:
        List of inserted split models
    """
    split_models = [
        Split(
            ticker_history_id=ticker_history_id,
            symbol=symbol,
            date=s["date"],
            split_ratio=s["split_ratio"],
        )
        for s in splits_data
    ]

    splits_repo.bulk_upsert_splits(ticker_history_id, split_models)
    return split_models
