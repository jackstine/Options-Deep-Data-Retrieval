"""Seed test database with fixture data for backfill pipeline testing.

This script populates the test database with pre-configured test data:
- TESTSPLIT: Active company with 30 days pricing + split on day 15
- TESTDELIST: Delisted company with 25 days pricing
- TESTACTIVE: Active company with 30 days pricing, no splits

This script is executed during Docker image build to create options-deep-test-data:latest
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from decimal import Decimal

# Add project root to path
sys.path.insert(0, "/opt/options-deep")

# Set environment variables for Docker init context
os.environ["OPTIONS_DEEP_ENV"] = "local-test"
os.environ["OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD"] = "test"
os.environ["ENVIRONMENT"] = "local-test"
os.environ["NASDAQ_API_KEY"] = "test_key"
os.environ["EODHD_API_KEY"] = "test_key"
os.environ["DOCKER_INIT"] = "true"

# Debug: Verify DOCKER_INIT is set
print(f"DEBUG: DOCKER_INIT environment variable = {os.getenv('DOCKER_INIT')}")

from src.database.equities.enums import DataSourceEnum
from src.models.company import Company
from src.models.historical_eod_pricing import HistoricalEndOfDayPricing
from src.models.split import Split
from src.models.ticker import Ticker
from src.models.ticker_history import TickerHistory
from src.repos.equities.companies.company_repository import CompanyRepository
from src.repos.equities.pricing.historical_eod_pricing_repository import (
    HistoricalEodPricingRepository,
)
from src.repos.equities.splits.splits_repository import SplitsRepository
from src.repos.equities.tickers.ticker_history_repository import (
    TickerHistoryRepository,
)
from src.repos.equities.tickers.ticker_repository import TickerRepository


def generate_pricing_data(
    base_price: Decimal,
    days: int,
    volatility: Decimal = Decimal("0.05"),
) -> list[Decimal]:
    """Generate realistic pricing data with volatility.

    Creates price movements that will generate patterns for backfill testing.
    Includes rises, falls, and recoveries to trigger threshold crossings.

    Args:
        base_price: Starting price
        days: Number of days to generate
        volatility: Price volatility factor (default 5%)

    Returns:
        List of close prices for each day
    """
    prices = []
    current_price = base_price

    for day in range(days):
        # Create pattern-friendly price movements
        if day < 5:
            # Initial rise
            change = Decimal("1.02")  # 2% daily increase
        elif day < 10:
            # Sharp drop (creates low/high threshold crossing)
            change = Decimal("0.95")  # 5% daily decrease
        elif day < 15:
            # Recovery (creates rebound/reversal)
            change = Decimal("1.03")  # 3% daily increase
        elif day < 20:
            # Second drop
            change = Decimal("0.96")  # 4% daily decrease
        else:
            # Final recovery
            change = Decimal("1.02")  # 2% daily increase

        current_price = current_price * change
        prices.append(current_price.quantize(Decimal("0.01")))

    return prices


def create_company_with_ticker_and_pricing(
    company_repo: CompanyRepository,
    ticker_repo: TickerRepository,
    ticker_history_repo: TickerHistoryRepository,
    pricing_repo: HistoricalEodPricingRepository,
    company_name: str,
    symbol: str,
    base_price: Decimal,
    pricing_days: int,
    start_date: date,
    valid_to: date | None = None,
) -> tuple[Company, Ticker, TickerHistory]:
    """Create a company with ticker history and pricing data.

    Args:
        company_repo: Company repository
        ticker_repo: Ticker repository
        ticker_history_repo: Ticker history repository
        pricing_repo: Historical pricing repository
        company_name: Company name
        symbol: Ticker symbol
        base_price: Starting price for pricing data generation
        pricing_days: Number of days of pricing data to generate
        start_date: Start date for pricing data
        valid_to: Optional end date for ticker history (for delisted companies)

    Returns:
        Tuple of (Company, Ticker, TickerHistory)
    """
    # Create company
    company = Company(
        company_name=company_name,
        exchange="NASDAQ",
        active=(valid_to is None),
        source=DataSourceEnum.EODHD,
    )
    inserted_company = company_repo.insert(company)

    # Create ticker history
    ticker_history = TickerHistory(
        symbol=symbol,
        company_id=inserted_company.id,
        valid_from=start_date,
        valid_to=valid_to,
    )
    inserted_ticker_history = ticker_history_repo.insert(ticker_history)

    # Create ticker
    ticker = Ticker(
        symbol=symbol,
        company_id=inserted_company.id,
        ticker_history_id=inserted_ticker_history.id,
    )
    inserted_ticker = ticker_repo.insert(ticker)

    # Generate and insert pricing data
    prices = generate_pricing_data(base_price, pricing_days)

    pricing_records = []
    for day_offset, close_price in enumerate(prices):
        pricing_date = start_date + timedelta(days=day_offset)

        # Generate realistic OHLC from close price
        daily_volatility = Decimal("0.02")  # 2% intraday volatility
        high = close_price * (Decimal("1.0") + daily_volatility)
        low = close_price * (Decimal("1.0") - daily_volatility)
        open_price = close_price * Decimal("0.995")  # Slight gap

        pricing = HistoricalEndOfDayPricing(
            ticker_history_id=inserted_ticker_history.id,
            date=pricing_date,
            open=open_price.quantize(Decimal("0.01")),
            high=high.quantize(Decimal("0.01")),
            low=low.quantize(Decimal("0.01")),
            close=close_price,
            adjusted_close=close_price,
            volume=1000000,  # Default volume
        )
        pricing_records.append(pricing)

    # Bulk insert pricing data
    pricing_repo.insert_many(pricing_records)

    return inserted_company, inserted_ticker, inserted_ticker_history


def seed_test_fixtures() -> None:
    """Seed the test database with fixture data."""
    print("🌱 Starting test fixture seeding...")

    # Initialize repositories
    company_repo = CompanyRepository()
    ticker_repo = TickerRepository()
    ticker_history_repo = TickerHistoryRepository()
    pricing_repo = HistoricalEodPricingRepository()
    splits_repo = SplitsRepository()

    # Debug: Show connection string being used
    from src.database.config import get_database_config
    db_config = get_database_config("equities")
    print(f"DEBUG: Connection string = {db_config.get_connection_string()}")
    print(f"DEBUG: DOCKER_INIT in get_connection_string = {os.getenv('DOCKER_INIT')}")

    # Base date for all test data
    base_date = date(2025, 11, 1)

    # 1. TESTSPLIT - Active company with split
    print("  Creating TESTSPLIT company with 30 days pricing and split...")
    testsplit_company, testsplit_ticker, testsplit_th = create_company_with_ticker_and_pricing(
        company_repo,
        ticker_repo,
        ticker_history_repo,
        pricing_repo,
        company_name="Test Split Company",
        symbol="TESTSPLIT",
        base_price=Decimal("100.00"),
        pricing_days=30,
        start_date=base_date,
        valid_to=None,  # Active company
    )

    # Add split on day 15
    split_date = base_date + timedelta(days=14)  # Day 15 (0-indexed)
    split = Split(
        ticker_history_id=testsplit_th.id,
        date=split_date,
        split_ratio="2.000000/1.000000",  # 2:1 forward split
    )
    splits_repo.insert(split)
    print(f"    ✓ Created TESTSPLIT (ticker_history_id={testsplit_th.id}) with split on {split_date}")

    # 2. TESTDELIST - Delisted company
    print("  Creating TESTDELIST company with 25 days pricing (delisted)...")
    delisting_date = base_date + timedelta(days=24)  # Day 25
    testdelist_company, testdelist_ticker, testdelist_th = create_company_with_ticker_and_pricing(
        company_repo,
        ticker_repo,
        ticker_history_repo,
        pricing_repo,
        company_name="Test Delisted Company",
        symbol="TESTDELIST",
        base_price=Decimal("80.00"),
        pricing_days=25,
        start_date=base_date,
        valid_to=delisting_date,  # Delisted on day 25
    )
    print(f"    ✓ Created TESTDELIST (ticker_history_id={testdelist_th.id}) delisted on {delisting_date}")

    # 3. TESTACTIVE - Active company without splits
    print("  Creating TESTACTIVE company with 30 days pricing (no splits)...")
    testactive_company, testactive_ticker, testactive_th = create_company_with_ticker_and_pricing(
        company_repo,
        ticker_repo,
        ticker_history_repo,
        pricing_repo,
        company_name="Test Active Company",
        symbol="TESTACTIVE",
        base_price=Decimal("90.00"),
        pricing_days=30,
        start_date=base_date,
        valid_to=None,  # Active company
    )
    print(f"    ✓ Created TESTACTIVE (ticker_history_id={testactive_th.id})")

    print("✅ Test fixture seeding completed successfully!")
    print(f"   - TESTSPLIT:   ticker_history_id={testsplit_th.id}")
    print(f"   - TESTDELIST:  ticker_history_id={testdelist_th.id}")
    print(f"   - TESTACTIVE:  ticker_history_id={testactive_th.id}")


if __name__ == "__main__":
    try:
        seed_test_fixtures()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error seeding test fixtures: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
