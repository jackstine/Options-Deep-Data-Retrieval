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


# ============================================================================
# EXHAUSTIVE FIELD VALIDATION HELPERS
# ============================================================================
# These helpers encapsulate exhaustive field validation logic.
# They allow conditionals in helper functions while keeping test bodies clean.


def assert_company_fields_complete(
    company: CompanyTable,
    expected_values: dict[str, Any] | None = None,
) -> None:
    """Assert all Company fields are properly set and optionally match expected values.

    This helper performs exhaustive field validation for a Company record,
    checking that all fields exist, have correct types, and optionally match
    expected values.

    Args:
        company: Company table object to validate
        expected_values: Optional dict of field_name -> expected_value to verify

    Raises:
        AssertionError: If any field validation fails
    """
    # Validate id field
    assert company.id is not None, "Company id should be set"
    assert isinstance(company.id, int), "Company id should be an integer"

    # Validate required string fields
    assert company.company_name is not None, "Company name should be set"
    assert isinstance(company.company_name, str), "Company name should be a string"
    assert company.exchange is not None, "Exchange should be set"
    assert isinstance(company.exchange, str), "Exchange should be a string"

    # Validate optional string fields (can be None, but if set must be string)
    if company.sector is not None:
        assert isinstance(company.sector, str), "Sector should be a string if set"
    if company.industry is not None:
        assert isinstance(company.industry, str), "Industry should be a string if set"
    if company.country is not None:
        assert isinstance(company.country, str), "Country should be a string if set"
    if company.description is not None:
        assert isinstance(company.description, str), "Description should be a string if set"

    # Validate optional numeric fields
    if company.market_cap is not None:
        assert isinstance(company.market_cap, int), "Market cap should be an integer if set"

    # Validate boolean fields
    assert company.active is not None, "Active flag should be set"
    assert isinstance(company.active, bool), "Active should be a boolean"
    assert company.is_valid_data is not None, "is_valid_data should be set"
    assert isinstance(company.is_valid_data, bool), "is_valid_data should be a boolean"

    # Validate source field
    assert company.source is not None, "Source should be set"
    assert isinstance(company.source, str), "Source should be a string"

    # Validate against expected values if provided
    if expected_values:
        for field_name, expected_value in expected_values.items():
            actual_value = getattr(company, field_name)
            assert actual_value == expected_value, (
                f"Company.{field_name} expected {expected_value}, got {actual_value}"
            )


def assert_ticker_fields_complete(
    ticker: TickerTable,
    expected_values: dict[str, Any] | None = None,
) -> None:
    """Assert all Ticker fields are properly set and optionally match expected values.

    Args:
        ticker: Ticker table object to validate
        expected_values: Optional dict of field_name -> expected_value to verify

    Raises:
        AssertionError: If any field validation fails
    """
    # Validate id field
    assert ticker.id is not None, "Ticker id should be set"
    assert isinstance(ticker.id, int), "Ticker id should be an integer"

    # Validate symbol
    assert ticker.symbol is not None, "Ticker symbol should be set"
    assert isinstance(ticker.symbol, str), "Ticker symbol should be a string"

    # Validate foreign keys
    assert ticker.company_id is not None, "Ticker company_id should be set"
    assert isinstance(ticker.company_id, int), "Ticker company_id should be an integer"
    assert ticker.ticker_history_id is not None, "Ticker ticker_history_id should be set"
    assert isinstance(ticker.ticker_history_id, int), "ticker_history_id should be an integer"

    # Validate against expected values if provided
    if expected_values:
        for field_name, expected_value in expected_values.items():
            actual_value = getattr(ticker, field_name)
            assert actual_value == expected_value, (
                f"Ticker.{field_name} expected {expected_value}, got {actual_value}"
            )


def assert_ticker_history_fields_complete(
    ticker_history: TickerHistoryTable,
    expected_values: dict[str, Any] | None = None,
) -> None:
    """Assert all TickerHistory fields are properly set and optionally match expected values.

    Args:
        ticker_history: TickerHistory table object to validate
        expected_values: Optional dict of field_name -> expected_value to verify

    Raises:
        AssertionError: If any field validation fails
    """
    from datetime import date as date_type

    # Validate id field
    assert ticker_history.id is not None, "TickerHistory id should be set"
    assert isinstance(ticker_history.id, int), "TickerHistory id should be an integer"

    # Validate symbol
    assert ticker_history.symbol is not None, "TickerHistory symbol should be set"
    assert isinstance(ticker_history.symbol, str), "TickerHistory symbol should be a string"

    # Validate foreign key
    assert ticker_history.company_id is not None, "TickerHistory company_id should be set"
    assert isinstance(ticker_history.company_id, int), "TickerHistory company_id should be an integer"

    # Validate valid_from
    assert ticker_history.valid_from is not None, "TickerHistory valid_from should be set"
    assert isinstance(ticker_history.valid_from, date_type), "valid_from should be a date"

    # Validate valid_to (can be None for active tickers)
    if ticker_history.valid_to is not None:
        assert isinstance(ticker_history.valid_to, date_type), "valid_to should be a date if set"

    # Validate against expected values if provided
    if expected_values:
        for field_name, expected_value in expected_values.items():
            actual_value = getattr(ticker_history, field_name)
            assert actual_value == expected_value, (
                f"TickerHistory.{field_name} expected {expected_value}, got {actual_value}"
            )


def assert_pricing_fields_complete(
    pricing: HistoricalEodPricingTable,
    expected_values: dict[str, Any] | None = None,
) -> None:
    """Assert all HistoricalEndOfDayPricing fields are properly set.

    Args:
        pricing: HistoricalEndOfDayPricing table object to validate
        expected_values: Optional dict of field_name -> expected_value to verify

    Raises:
        AssertionError: If any field validation fails
    """
    from datetime import date as date_type
    from decimal import Decimal

    # Validate id field
    assert pricing.id is not None, "Pricing id should be set"
    assert isinstance(pricing.id, int), "Pricing id should be an integer"

    # Validate foreign key
    assert pricing.ticker_history_id is not None, "ticker_history_id should be set"
    assert isinstance(pricing.ticker_history_id, int), "ticker_history_id should be an integer"

    # Validate date
    assert pricing.date is not None, "Pricing date should be set"
    assert isinstance(pricing.date, date_type), "Pricing date should be a date object"

    # Validate OHLC prices
    assert pricing.open is not None, "Open price should be set"
    assert isinstance(pricing.open, Decimal), "Open should be a Decimal"
    assert pricing.high is not None, "High price should be set"
    assert isinstance(pricing.high, Decimal), "High should be a Decimal"
    assert pricing.low is not None, "Low price should be set"
    assert isinstance(pricing.low, Decimal), "Low should be a Decimal"
    assert pricing.close is not None, "Close price should be set"
    assert isinstance(pricing.close, Decimal), "Close should be a Decimal"

    # Validate adjusted_close
    assert pricing.adjusted_close is not None, "Adjusted close should be set"
    assert isinstance(pricing.adjusted_close, Decimal), "Adjusted close should be a Decimal"

    # Validate volume
    assert pricing.volume is not None, "Volume should be set"
    assert isinstance(pricing.volume, int), "Volume should be an integer"

    # Validate against expected values if provided
    if expected_values:
        for field_name, expected_value in expected_values.items():
            actual_value = getattr(pricing, field_name)
            assert actual_value == expected_value, (
                f"HistoricalEndOfDayPricing.{field_name} expected {expected_value}, got {actual_value}"
            )


def assert_misplaced_pricing_fields_complete(
    pricing: MisplacedEodPricingTable,
    expected_values: dict[str, Any] | None = None,
) -> None:
    """Assert all MisplacedEndOfDayPricing fields are properly set.

    Args:
        pricing: MisplacedEndOfDayPricing table object to validate
        expected_values: Optional dict of field_name -> expected_value to verify

    Raises:
        AssertionError: If any field validation fails
    """
    from datetime import date as date_type
    from decimal import Decimal

    # Validate symbol
    assert pricing.symbol is not None, "Symbol should be set"
    assert isinstance(pricing.symbol, str), "Symbol should be a string"

    # Validate date
    assert pricing.date is not None, "Date should be set"
    assert isinstance(pricing.date, date_type), "Date should be a date object"

    # Validate OHLC prices
    assert pricing.open is not None, "Open price should be set"
    assert isinstance(pricing.open, Decimal), "Open should be a Decimal"
    assert pricing.high is not None, "High price should be set"
    assert isinstance(pricing.high, Decimal), "High should be a Decimal"
    assert pricing.low is not None, "Low price should be set"
    assert isinstance(pricing.low, Decimal), "Low should be a Decimal"
    assert pricing.close is not None, "Close price should be set"
    assert isinstance(pricing.close, Decimal), "Close should be a Decimal"

    # Validate adjusted_close
    assert pricing.adjusted_close is not None, "Adjusted close should be set"
    assert isinstance(pricing.adjusted_close, Decimal), "Adjusted close should be a Decimal"

    # Validate volume
    assert pricing.volume is not None, "Volume should be set"
    assert isinstance(pricing.volume, int), "Volume should be an integer"

    # Validate source
    assert pricing.source is not None, "Source should be set"

    # Validate against expected values if provided
    if expected_values:
        for field_name, expected_value in expected_values.items():
            actual_value = getattr(pricing, field_name)
            assert actual_value == expected_value, (
                f"MisplacedEodPricing.{field_name} expected {expected_value}, got {actual_value}"
            )


def assert_split_fields_complete(
    split: SplitTable,
    expected_values: dict[str, Any] | None = None,
) -> None:
    """Assert all Split fields are properly set.

    Args:
        split: Split table object to validate
        expected_values: Optional dict of field_name -> expected_value to verify

    Raises:
        AssertionError: If any field validation fails
    """
    from datetime import date as date_type

    # Validate id field
    assert split.id is not None, "Split id should be set"
    assert isinstance(split.id, int), "Split id should be an integer"

    # Validate date
    assert split.date is not None, "Split date should be set"
    assert isinstance(split.date, date_type), "Split date should be a date object"

    # Validate split_ratio
    assert split.split_ratio is not None, "Split ratio should be set"
    assert isinstance(split.split_ratio, str), "Split ratio should be a string"
    assert "/" in split.split_ratio, "Split ratio should contain a '/' separator"

    # Validate foreign key
    assert split.ticker_history_id is not None, "ticker_history_id should be set"
    assert isinstance(split.ticker_history_id, int), "ticker_history_id should be an integer"

    # Validate symbol (optional for display purposes)
    if split.symbol is not None:
        assert isinstance(split.symbol, str), "Symbol should be a string if set"

    # Validate split ratio can be parsed
    split_ratio_decimal = split.get_split_ratio()
    assert split_ratio_decimal is not None, "Split ratio should be parseable"
    assert split_ratio_decimal > 0, "Split ratio should be positive"

    # Validate against expected values if provided
    if expected_values:
        for field_name, expected_value in expected_values.items():
            actual_value = getattr(split, field_name)
            assert actual_value == expected_value, (
                f"Split.{field_name} expected {expected_value}, got {actual_value}"
            )


def assert_ohlc_relationships(pricing: HistoricalEodPricingTable | MisplacedEodPricingTable) -> None:
    """Assert OHLC price relationships are valid.

    Validates that:
    - High >= Low
    - High >= Open
    - High >= Close
    - Low <= Open
    - Low <= Close

    Args:
        pricing: Pricing table object to validate (HistoricalEodPricing or MisplacedEodPricing)

    Raises:
        AssertionError: If any price relationship is invalid
    """
    assert pricing.high >= pricing.low, "High must be >= Low"
    assert pricing.high >= pricing.open, "High must be >= Open"
    assert pricing.high >= pricing.close, "High must be >= Close"
    assert pricing.low <= pricing.open, "Low must be <= Open"
    assert pricing.low <= pricing.close, "Low must be <= Close"
