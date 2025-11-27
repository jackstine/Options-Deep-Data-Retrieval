"""Pipeline for daily high/low pattern processing."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import TypedDict

from src.algorithms.high_lows.models.low import Low
from src.algorithms.high_lows.pattern_calculator import PatternCalculator
from src.algorithms.high_lows.processor import process_high_low_patterns
from src.models.date_price import DatePrice
from src.repos.algorithms.high_lows.lows_repository import LowsRepository
from src.repos.algorithms.high_lows.rebounds_repository import ReboundsRepository
from src.repos.equities.pricing.historical_eod_pricing_repository import (
    HistoricalEodPricingRepository,
)
from src.repos.equities.tickers.ticker_repository import TickerRepository


class DailyHighLowResult(TypedDict):
    """Result of daily high/low processing."""

    total_tickers_processed: int
    total_patterns_processed: int
    patterns_completed: int
    patterns_updated: int
    patterns_spawned: int
    patterns_expired: int
    errors: int


class DailyHighLowPipeline:
    """Pipeline for daily high/low pattern processing.

    This pipeline:
    1. Gets all active (non-expired) low patterns from database
    2. Gets today's EOD pricing data for each ticker
    3. Processes patterns with new prices using core algorithm
    4. Separates completed patterns (rebounds) from active patterns
    5. Deletes completed low patterns from lows table
    6. Inserts completed patterns into rebounds table
    7. Upserts updated/new active patterns into lows table
    8. Marks expired patterns (>800 days old)
    """

    def __init__(
        self,
        lows_repo: LowsRepository | None = None,
        rebounds_repo: ReboundsRepository | None = None,
        pricing_repo: HistoricalEodPricingRepository | None = None,
        ticker_repo: TickerRepository | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize daily high/low pipeline.

        Args:
            lows_repo: Repository for lows operations
            rebounds_repo: Repository for rebounds operations
            pricing_repo: Repository for pricing operations
            ticker_repo: Repository for ticker operations
            logger: Logger instance
        """
        self.lows_repo = lows_repo or LowsRepository()
        self.rebounds_repo = rebounds_repo or ReboundsRepository()
        self.pricing_repo = pricing_repo or HistoricalEodPricingRepository()
        self.ticker_repo = ticker_repo or TickerRepository()
        self.logger = logger or logging.getLogger(__name__)
        self.pattern_calc = PatternCalculator()

    def run(self, calculation_date: date | None = None) -> DailyHighLowResult:
        """Run daily high/low pattern processing.

        Args:
            calculation_date: Date to process (default: today)

        Returns:
            DailyHighLowResult with processing statistics
        """
        calc_date = calculation_date or date.today()
        self.logger.info(f"Starting daily high/low processing for {calc_date}")

        result: DailyHighLowResult = {
            "total_tickers_processed": 0,
            "total_patterns_processed": 0,
            "patterns_completed": 0,
            "patterns_updated": 0,
            "patterns_spawned": 0,
            "patterns_expired": 0,
            "errors": 0,
        }

        try:
            # Step 1: Get all active patterns grouped by ticker and threshold
            self.logger.info("Fetching all active low patterns...")
            all_active_patterns = self.lows_repo.get_all_active_lows()
            result["total_patterns_processed"] = len(all_active_patterns)

            if not all_active_patterns:
                self.logger.info("No active patterns found. Nothing to process.")
                return result

            # Step 2: Group patterns by ticker_history_id for batch processing
            patterns_by_ticker = self._group_patterns_by_ticker(all_active_patterns)
            result["total_tickers_processed"] = len(patterns_by_ticker)

            # Step 3: Process each ticker's patterns
            all_updated_lows = []
            all_completed_rebounds = []
            completed_low_ids = []

            # TODO need to get all_ticker_history_id_pricing_for_date() returns the list
            # of all ticker_history_ids for that one date
            for ticker_history_id, ticker_patterns in patterns_by_ticker.items():
                try:
                    # Get today's pricing data for this ticker
                    pricing = self.pricing_repo.get_pricing_for_date(
                        ticker_history_id, calc_date
                    )

                    if not pricing:
                        self.logger.debug(
                            f"No pricing data for ticker_history_id {ticker_history_id} on {calc_date}"
                        )
                        # Keep existing patterns as-is
                        all_updated_lows.extend(ticker_patterns)
                        continue

                    # Check if close price is available
                    if pricing.close is None:
                        self.logger.debug(
                            f"No close price for ticker_history_id {ticker_history_id} on {calc_date}"
                        )
                        # Keep existing patterns as-is
                        all_updated_lows.extend(ticker_patterns)
                        continue

                    # Convert HistoricalEndOfDayPricing to DatePrice
                    date_price = DatePrice(date=pricing.date, price=pricing.close)

                    # Group by threshold and process
                    patterns_by_threshold = self._group_patterns_by_threshold(
                        ticker_patterns
                    )

                    for threshold, threshold_patterns in patterns_by_threshold.items():
                        # Process patterns with the core algorithm
                        processed = process_high_low_patterns(
                            current_patterns=threshold_patterns,
                            new_prices=[date_price],
                            threshold=threshold,
                        )

                        # Collect results
                        all_updated_lows.extend(processed.active_lows)
                        all_completed_rebounds.extend(processed.completed_rebounds)

                        # Track IDs of completed patterns to delete
                        for pattern in threshold_patterns:
                            # Check if this pattern was completed
                            if pattern not in processed.active_lows and pattern.id:
                                completed_low_ids.append(pattern.id)

                        # Count spawned patterns
                        newly_spawned = len(processed.active_lows) - len(
                            threshold_patterns
                        )
                        if newly_spawned > 0:
                            result["patterns_spawned"] += newly_spawned

                except Exception as e:
                    self.logger.error(
                        f"Error processing ticker_history_id {ticker_history_id}: {e}"
                    )
                    result["errors"] += 1
                    # Keep existing patterns for this ticker
                    all_updated_lows.extend(ticker_patterns)

            # Step 4: Identify expired patterns
            expired_low_ids = [
                low.id for low in all_updated_lows if low.id and low.is_expired()
            ]

            # Step 5: Database operations
            # Delete completed patterns
            if completed_low_ids:
                self.logger.info(f"Deleting {len(completed_low_ids)} completed patterns")
                self.lows_repo.delete_lows_by_ids(completed_low_ids)
                result["patterns_completed"] = len(completed_low_ids)

            # Insert completed rebounds
            if all_completed_rebounds:
                self.logger.info(f"Inserting {len(all_completed_rebounds)} rebounds")
                self.rebounds_repo.bulk_insert_rebounds(all_completed_rebounds)

            # Mark expired patterns
            if expired_low_ids:
                self.logger.info(f"Marking {len(expired_low_ids)} patterns as expired")
                self.lows_repo.mark_as_expired(expired_low_ids)
                result["patterns_expired"] = len(expired_low_ids)

            # Upsert active patterns
            if all_updated_lows:
                self.logger.info(f"Upserting {len(all_updated_lows)} active patterns")
                upsert_result = self.lows_repo.bulk_upsert_lows(all_updated_lows)
                result["patterns_updated"] = (
                    upsert_result["inserted"] + upsert_result["updated"]
                )

            self.logger.info(f"Daily high/low processing complete: {result}")

        except Exception as e:
            self.logger.error(f"Error in daily high/low pipeline: {e}")
            result["errors"] += 1

        return result

    def _group_patterns_by_ticker(
        self, patterns: list[Low]
    ) -> dict[int, list[Low]]:
        """Group patterns by ticker_history_id.

        Args:
            patterns: List of Low patterns

        Returns:
            Dictionary mapping ticker_history_id to list of patterns
        """
        grouped: dict[int, list[Low]] = {}
        for pattern in patterns:
            if pattern.ticker_history_id not in grouped:
                grouped[pattern.ticker_history_id] = []
            grouped[pattern.ticker_history_id].append(pattern)
        return grouped

    def _group_patterns_by_threshold(
        self, patterns: list[Low]
    ) -> dict[Decimal, list[Low]]:
        """Group patterns by threshold.

        Args:
            patterns: List of Low patterns

        Returns:
            Dictionary mapping threshold to list of patterns
        """
        grouped: dict[Decimal, list[Low]] = {}
        for pattern in patterns:
            if pattern.threshold not in grouped:
                grouped[pattern.threshold] = []
            grouped[pattern.threshold].append(pattern)
        return grouped
