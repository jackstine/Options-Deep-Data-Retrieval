"""Database assertion utilities for integration tests."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from src.database.equities.tables.company import Company as CompanyTable
from src.database.equities.tables.historical_eod_pricing import HistoricalEodPricing as HistoricalEodPricingTable
from src.database.equities.tables.misplaced_eod_pricing import MisplacedEodPricing as MisplacedEodPricingTable
from src.database.equities.tables.splits import Split as SplitTable
from src.database.equities.tables.ticker import Ticker as TickerTable
from src.database.equities.tables.ticker_history import TickerHistory as TickerHistoryTable


def assert_company_exists(
    db: Session,
    company_name: str,
    expected_fields: dict[str, Any] | None = None,
) -> CompanyTable:
    """Assert that a company exists in the database with expected fields.

    Args:
        db: Database session
        company_name: Name of the company to find
        expected_fields: Optional dictionary of field_name -> expected_value

    Returns:
        The company database model if found

    Raises:
        AssertionError: If company doesn't exist or fields don't match
    """
    stmt = select(CompanyTable).where(CompanyTable.company_name == company_name)
    company = db.execute(stmt).scalar_one_or_none()

    assert company is not None, f"Company '{company_name}' not found in database"

    if expected_fields:
        for field_name, expected_value in expected_fields.items():
            actual_value = getattr(company, field_name, None)
            assert actual_value == expected_value, (
                f"Company '{company_name}' field '{field_name}' "
                f"expected {expected_value}, got {actual_value}"
            )

    return company


def assert_ticker_exists(
    db: Session,
    symbol: str,
    company_id: int | None = None,
) -> TickerTable:
    """Assert that a ticker exists in the tickers table.

    Args:
        db: Database session
        symbol: Ticker symbol to find
        company_id: Optional company ID to verify

    Returns:
        The ticker database model if found

    Raises:
        AssertionError: If ticker doesn't exist or company_id doesn't match
    """
    stmt = select(TickerTable).where(TickerTable.symbol == symbol)
    ticker = db.execute(stmt).scalar_one_or_none()

    assert ticker is not None, f"Ticker '{symbol}' not found in tickers table"

    if company_id is not None:
        assert ticker.company_id == company_id, (
            f"Ticker '{symbol}' company_id expected {company_id}, "
            f"got {ticker.company_id}"
        )

    return ticker


def assert_ticker_history_valid(
    db: Session,
    symbol: str,
    company_id: int,
    valid_from: str | None = None,
    valid_to: str | None = None,
) -> TickerHistoryTable:
    """Assert that a ticker_history record exists with correct validity dates.

    Args:
        db: Database session
        symbol: Ticker symbol to find
        company_id: Company ID to verify
        valid_from: Optional expected valid_from date (YYYY-MM-DD or None)
        valid_to: Optional expected valid_to date (YYYY-MM-DD or None)

    Returns:
        The ticker_history database model if found

    Raises:
        AssertionError: If ticker_history doesn't exist or dates don't match
    """
    stmt = select(TickerHistoryTable).where(
        TickerHistoryTable.symbol == symbol,
        TickerHistoryTable.company_id == company_id,
    )
    ticker_history = db.execute(stmt).scalar_one_or_none()

    assert ticker_history is not None, (
        f"Ticker history for '{symbol}' and company_id {company_id} "
        f"not found in ticker_history table"
    )

    if valid_from is not None:
        actual_from = ticker_history.valid_from.strftime("%Y-%m-%d") if ticker_history.valid_from else None
        assert actual_from == valid_from, (
            f"Ticker history '{symbol}' valid_from expected {valid_from}, "
            f"got {actual_from}"
        )

    if valid_to is not None:
        actual_to = ticker_history.valid_to.strftime("%Y-%m-%d") if ticker_history.valid_to else None
        assert actual_to == valid_to, (
            f"Ticker history '{symbol}' valid_to expected {valid_to}, "
            f"got {actual_to}"
        )

    return ticker_history


def count_records(db: Session, table_name: str) -> int:
    """Count total records in a table.

    Args:
        db: Database session
        table_name: Name of the table

    Returns:
        Number of records in the table
    """
    result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    return result.scalar() or 0


def count_companies(db: Session, active_only: bool = False) -> int:
    """Count companies in the database.

    Args:
        db: Database session
        active_only: If True, count only active companies

    Returns:
        Number of companies
    """
    stmt = select(func.count()).select_from(CompanyTable)

    if active_only:
        stmt = stmt.where(CompanyTable.active == True)  # noqa: E712

    result = db.execute(stmt)
    return result.scalar() or 0


def count_tickers(db: Session) -> int:
    """Count tickers in the tickers table.

    Args:
        db: Database session

    Returns:
        Number of tickers
    """
    stmt = select(func.count()).select_from(TickerTable)
    result = db.execute(stmt)
    return result.scalar() or 0


def count_ticker_histories(db: Session) -> int:
    """Count ticker_history records.

    Args:
        db: Database session

    Returns:
        Number of ticker_history records
    """
    stmt = select(func.count()).select_from(TickerHistoryTable)
    result = db.execute(stmt)
    return result.scalar() or 0


def get_company_by_name(db: Session, company_name: str) -> CompanyTable | None:
    """Get a company by name.

    Args:
        db: Database session
        company_name: Name of the company

    Returns:
        Company model or None if not found
    """
    stmt = select(CompanyTable).where(CompanyTable.company_name == company_name)
    return db.execute(stmt).scalar_one_or_none()


def get_ticker_by_symbol(db: Session, symbol: str) -> TickerTable | None:
    """Get a ticker by symbol.

    Args:
        db: Database session
        symbol: Ticker symbol

    Returns:
        Ticker model or None if not found
    """
    stmt = select(TickerTable).where(TickerTable.symbol == symbol)
    return db.execute(stmt).scalar_one_or_none()


def get_ticker_histories_for_symbol(db: Session, symbol: str) -> list[TickerHistoryTable]:
    """Get all ticker_history records for a symbol.

    Args:
        db: Database session
        symbol: Ticker symbol

    Returns:
        List of ticker_history records
    """
    stmt = select(TickerHistoryTable).where(TickerHistoryTable.symbol == symbol)
    return list(db.execute(stmt).scalars().all())


def count_historical_eod_pricing(db: Session, ticker_history_id: int | None = None) -> int:
    """Count historical EOD pricing records.

    Args:
        db: Database session
        ticker_history_id: Optional ticker_history_id to filter by

    Returns:
        Number of historical EOD pricing records
    """
    stmt = select(func.count()).select_from(HistoricalEodPricingTable)

    if ticker_history_id is not None:
        stmt = stmt.where(HistoricalEodPricingTable.ticker_history_id == ticker_history_id)

    result = db.execute(stmt)
    return result.scalar() or 0


def count_misplaced_eod_pricing(db: Session, symbol: str | None = None) -> int:
    """Count misplaced EOD pricing records.

    Args:
        db: Database session
        symbol: Optional symbol to filter by

    Returns:
        Number of misplaced EOD pricing records
    """
    stmt = select(func.count()).select_from(MisplacedEodPricingTable)

    if symbol is not None:
        stmt = stmt.where(MisplacedEodPricingTable.symbol == symbol)

    result = db.execute(stmt)
    return result.scalar() or 0


def count_splits(db: Session, ticker_history_id: int | None = None) -> int:
    """Count split records.

    Args:
        db: Database session
        ticker_history_id: Optional ticker_history_id to filter by

    Returns:
        Number of split records
    """
    stmt = select(func.count()).select_from(SplitTable)

    if ticker_history_id is not None:
        stmt = stmt.where(SplitTable.ticker_history_id == ticker_history_id)

    result = db.execute(stmt)
    return result.scalar() or 0


def get_historical_eod_pricing_by_date(
    db: Session, ticker_history_id: int, pricing_date: str
) -> HistoricalEodPricingTable | None:
    """Get historical EOD pricing record for a specific date.

    Args:
        db: Database session
        ticker_history_id: Ticker history ID
        pricing_date: Date in YYYY-MM-DD format

    Returns:
        Historical EOD pricing record or None if not found
    """
    from datetime import date

    target_date = date.fromisoformat(pricing_date)
    stmt = select(HistoricalEodPricingTable).where(
        HistoricalEodPricingTable.ticker_history_id == ticker_history_id,
        HistoricalEodPricingTable.date == target_date,
    )
    return db.execute(stmt).scalar_one_or_none()


def get_splits_by_symbol(db: Session, symbol: str) -> list[SplitTable]:
    """Get all split records for a symbol.

    Args:
        db: Database session
        symbol: Ticker symbol

    Returns:
        List of split records
    """
    # First get ticker_history_id(s) for the symbol
    ticker_histories = get_ticker_histories_for_symbol(db, symbol)

    if not ticker_histories:
        return []

    # Get splits for all ticker_history_ids associated with this symbol
    ticker_history_ids = [th.id for th in ticker_histories]
    stmt = select(SplitTable).where(SplitTable.ticker_history_id.in_(ticker_history_ids))
    return list(db.execute(stmt).scalars().all())
