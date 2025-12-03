"""Helper functions for high/low backfill integration tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal


class FixtureDataExpectations:
    """Expected values for fixture data from options-deep-test-data:latest image.

    The fixture contains:
    - TESTSPLIT: Active company with 30 days pricing + split on day 15
    - TESTDELIST: Delisted company with 25 days pricing
    - TESTACTIVE: Active company with 30 days pricing, no splits

    Pattern counts are based on analysis of the fixture data and the pattern detection algorithm.
    These should be verified against actual test runs and updated if fixture data changes.
    """

    # Expected pricing data counts
    TESTSPLIT_PRICING_DAYS = 30
    TESTDELIST_PRICING_DAYS = 25
    TESTACTIVE_PRICING_DAYS = 30

    # Expected date ranges
    FROM_DATE = date(2025, 11, 1)
    TO_DATE = date(2025, 11, 30)
    TESTDELIST_DELIST_DATE = date(2025, 11, 25)

    # Expected test configuration thresholds
    MULTI_CONFIG_THRESHOLDS = {
        Decimal("0.10"),
        Decimal("0.15"),
        Decimal("0.20"),
        Decimal("0.25"),
    }

    # Expected pattern counts per ticker per threshold
    # NOTE: These are ACTUAL counts from capture_actual_counts.py script
    # verified against the options-deep-test-data:latest fixture

    # Active patterns in database (lows table)
    TESTSPLIT_PATTERNS = {
        Decimal("0.10"): 2,
        Decimal("0.15"): 2,
        Decimal("0.20"): 1,
        Decimal("0.25"): 1,
    }
    TESTSPLIT_DB_COUNT = 6  # Active patterns in DB
    TESTSPLIT_TOTAL = 9  # Total generated (active + completed)

    TESTDELIST_PATTERNS = {
        Decimal("0.10"): 3,
        Decimal("0.15"): 2,
        Decimal("0.20"): 1,
        Decimal("0.25"): 1,
    }
    TESTDELIST_DB_COUNT = 7  # Active patterns in DB
    TESTDELIST_TOTAL = 7  # Total generated (active + completed)

    TESTACTIVE_PATTERNS = {
        Decimal("0.10"): 3,
        Decimal("0.15"): 3,
        Decimal("0.20"): 2,
        Decimal("0.25"): 1,
    }
    TESTACTIVE_DB_COUNT = 9  # Active patterns in DB
    TESTACTIVE_TOTAL = 9  # Total generated (active + completed)


def validate_backfill_result(
    result: dict,
    ticker_symbol: str,
    ticker_history_id: int,
    expected_from_date: str,
    expected_to_date: str,
    expected_pattern_count: int,
) -> None:
    """Validate backfill pipeline result with exact assertions.

    Args:
        result: Pipeline result dictionary
        ticker_symbol: Symbol being tested (for error messages)
        ticker_history_id: Expected ticker_history_id in result
        expected_from_date: Expected from_date in result
        expected_to_date: Expected to_date in result
        expected_pattern_count: Expected exact total patterns generated
    """
    assert result["ticker_history_id"] == ticker_history_id, (
        f"{ticker_symbol} result should have ticker_history_id {ticker_history_id}, "
        f"got {result['ticker_history_id']}"
    )
    assert result["errors"] == 0, (
        f"{ticker_symbol} should have zero errors, got {result['errors']}"
    )
    assert result["from_date"] == expected_from_date, (
        f"{ticker_symbol} from_date should be {expected_from_date}, "
        f"got {result['from_date']}"
    )
    assert result["to_date"] == expected_to_date, (
        f"{ticker_symbol} to_date should be {expected_to_date}, "
        f"got {result['to_date']}"
    )
    assert result["total_patterns_generated"] == expected_pattern_count, (
        f"{ticker_symbol} should generate exactly {expected_pattern_count} patterns, "
        f"got {result['total_patterns_generated']}"
    )


def validate_patterns_in_database(
    patterns: list,
    ticker_symbol: str,
    ticker_history_id: int,
    expected_count: int,
    expected_thresholds: set[Decimal],
) -> None:
    """Validate patterns retrieved from database with exact assertions.

    Args:
        patterns: List of pattern models from database
        ticker_symbol: Symbol being tested (for error messages)
        ticker_history_id: Expected ticker_history_id
        expected_count: Expected exact count of patterns
        expected_thresholds: Expected set of threshold values present in patterns
    """
    # Exact count assertion
    assert len(patterns) == expected_count, (
        f"{ticker_symbol} should have exactly {expected_count} patterns in database, "
        f"got {len(patterns)}"
    )

    # Validate all patterns have correct fields and ticker_history_id
    for pattern in patterns:
        assert pattern.ticker_history_id == ticker_history_id, (
            f"Pattern should have ticker_history_id {ticker_history_id}, "
            f"got {pattern.ticker_history_id}"
        )
        assert pattern.threshold is not None, "Pattern should have threshold"
        assert pattern.high_start_date is not None, "Pattern should have high_start_date"
        assert pattern.high_start_price is not None, "Pattern should have high_start_price"
        # low_threshold_price is optional - only set when pattern crosses threshold

    # Exact threshold set assertion
    actual_thresholds = set(p.threshold for p in patterns)
    assert actual_thresholds == expected_thresholds, (
        f"{ticker_symbol} should have exactly thresholds {expected_thresholds}, "
        f"got {actual_thresholds}"
    )


def validate_pattern_dates_before_delisting(
    patterns: list,
    delisting_date: date,
    ticker_symbol: str,
) -> None:
    """Validate all pattern dates are before delisting date.

    Args:
        patterns: List of pattern models from database
        delisting_date: Expected delisting date
        ticker_symbol: Symbol being tested (for error messages)
    """
    for pattern in patterns:
        if pattern.high_start_date:
            assert pattern.high_start_date <= delisting_date, (
                f"{ticker_symbol} pattern date {pattern.high_start_date} "
                f"should be on or before delisting date {delisting_date}"
            )
