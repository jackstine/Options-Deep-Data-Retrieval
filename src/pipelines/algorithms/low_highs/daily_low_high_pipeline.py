"""Pipeline for daily low/high pattern processing."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import TypedDict

from src.algorithms.low_highs.models.high import High
from src.algorithms.low_highs.pattern_calculator import PatternCalculator
from src.algorithms.low_highs.processor import process_low_high_patterns
from src.models.date_price import DatePrice
from src.repos.algorithms.low_highs.highs_repository import HighsRepository
from src.repos.algorithms.low_highs.reversals_repository import ReversalsRepository
from src.repos.equities.pricing.historical_eod_pricing_repository import (
    HistoricalEodPricingRepository,
)
from src.repos.equities.tickers.ticker_repository import TickerRepository


class DailyLowHighResult(TypedDict):
    """Result of daily low/high processing."""

    total_tickers_processed: int
    total_patterns_processed: int
    patterns_completed: int
    patterns_updated: int
    patterns_spawned: int
    patterns_expired: int
    errors: int


class DailyLowHighPipeline:
    """Pipeline for daily low/high pattern processing.

    This pipeline:
    1. Gets all active (non-expired) high patterns from database
    2. Gets today's EOD pricing data for each ticker
    3. Processes patterns with new prices using core algorithm
    4. Separates completed patterns (reversals) from active patterns
    5. Deletes completed high patterns from highs table
    6. Inserts completed patterns into reversals table
    7. Upserts updated/new active patterns into highs table
    8. Marks expired patterns (>800 days old)
    """

    def __init__(
        self,
        highs_repo: HighsRepository | None = None,
        reversals_repo: ReversalsRepository | None = None,
        pricing_repo: HistoricalEodPricingRepository | None = None,
        ticker_repo: TickerRepository | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize daily low/high pipeline.

        Args:
            highs_repo: Repository for highs operations
            reversals_repo: Repository for reversals operations
            pricing_repo: Repository for pricing operations
            ticker_repo: Repository for ticker operations
            logger: Logger instance
        """
        self.highs_repo = highs_repo or HighsRepository()
        self.reversals_repo = reversals_repo or ReversalsRepository()
        self.pricing_repo = pricing_repo or HistoricalEodPricingRepository()
        self.ticker_repo = ticker_repo or TickerRepository()
        self.logger = logger or logging.getLogger(__name__)
        self.pattern_calc = PatternCalculator()

    def run(self, calculation_date: date | None = None) -> DailyLowHighResult:
        """Run daily low/high pattern processing.

        Args:
            calculation_date: Date to process (default: today)

        Returns:
            DailyLowHighResult with processing statistics
        """
        calc_date = calculation_date or date.today()
        self.logger.info(f"Starting daily low/high processing for {calc_date}")

        result: DailyLowHighResult = {
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
            self.logger.info("Fetching all active high patterns...")
            all_active_patterns = self.highs_repo.get_all_active_highs()
            result["total_patterns_processed"] = len(all_active_patterns)

            if not all_active_patterns:
                self.logger.info("No active patterns found. Nothing to process.")
                return result

            # Step 2: Group patterns by ticker_history_id for batch processing
            patterns_by_ticker = self._group_patterns_by_ticker(all_active_patterns)
            result["total_tickers_processed"] = len(patterns_by_ticker)

            # Step 3: Process each ticker's patterns
            all_updated_highs = []
            all_completed_reversals = []
            completed_high_ids = []

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
                        all_updated_highs.extend(ticker_patterns)
                        continue

                    # Check if close price is available
                    if pricing.close is None:
                        self.logger.debug(
                            f"No close price for ticker_history_id {ticker_history_id} on {calc_date}"
                        )
                        # Keep existing patterns as-is
                        all_updated_highs.extend(ticker_patterns)
                        continue

                    # Convert HistoricalEndOfDayPricing to DatePrice
                    date_price = DatePrice(date=pricing.date, price=pricing.close)

                    # Group by threshold and process
                    patterns_by_threshold = self._group_patterns_by_threshold(
                        ticker_patterns
                    )

                    for threshold, threshold_patterns in patterns_by_threshold.items():
                        # Process patterns with the core algorithm
                        processed = process_low_high_patterns(
                            current_patterns=threshold_patterns,
                            new_prices=[date_price],
                            threshold=threshold,
                        )

                        # Collect results
                        all_updated_highs.extend(processed.active_highs)
                        all_completed_reversals.extend(processed.completed_reversals)

                        # Track IDs of completed patterns to delete
                        for pattern in threshold_patterns:
                            # Check if this pattern was completed
                            if pattern not in processed.active_highs and pattern.id:
                                completed_high_ids.append(pattern.id)

                        # Count spawned patterns
                        newly_spawned = len(processed.active_highs) - len(
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
                    all_updated_highs.extend(ticker_patterns)

            # Step 4: Identify expired patterns
            expired_high_ids = [
                high.id for high in all_updated_highs if high.id and high.is_expired()
            ]

            # Step 5: Database operations
            # Delete completed patterns
            if completed_high_ids:
                self.logger.info(f"Deleting {len(completed_high_ids)} completed patterns")
                self.highs_repo.delete_highs_by_ids(completed_high_ids)
                result["patterns_completed"] = len(completed_high_ids)

            # Insert completed reversals
            if all_completed_reversals:
                self.logger.info(f"Inserting {len(all_completed_reversals)} reversals")
                self.reversals_repo.bulk_insert_reversals(all_completed_reversals)

            # Mark expired patterns
            if expired_high_ids:
                self.logger.info(f"Marking {len(expired_high_ids)} patterns as expired")
                self.highs_repo.mark_as_expired(expired_high_ids)
                result["patterns_expired"] = len(expired_high_ids)

            # Upsert active patterns
            if all_updated_highs:
                self.logger.info(f"Upserting {len(all_updated_highs)} active patterns")
                upsert_result = self.highs_repo.bulk_upsert_highs(all_updated_highs)
                result["patterns_updated"] = (
                    upsert_result["inserted"] + upsert_result["updated"]
                )

            self.logger.info(f"Daily low/high processing complete: {result}")

        except Exception as e:
            self.logger.error(f"Error in daily low/high pipeline: {e}")
            result["errors"] += 1

        return result

    def _group_patterns_by_ticker(
        self, patterns: list[High]
    ) -> dict[int, list[High]]:
        """Group patterns by ticker_history_id.

        Args:
            patterns: List of High patterns

        Returns:
            Dictionary mapping ticker_history_id to list of patterns
        """
        grouped: dict[int, list[High]] = {}
        for pattern in patterns:
            if pattern.ticker_history_id not in grouped:
                grouped[pattern.ticker_history_id] = []
            grouped[pattern.ticker_history_id].append(pattern)
        return grouped

    def _group_patterns_by_threshold(
        self, patterns: list[High]
    ) -> dict[Decimal, list[High]]:
        """Group patterns by threshold.

        Args:
            patterns: List of High patterns

        Returns:
            Dictionary mapping threshold to list of patterns
        """
        grouped: dict[Decimal, list[High]] = {}
        for pattern in patterns:
            if pattern.threshold not in grouped:
                grouped[pattern.threshold] = []
            grouped[pattern.threshold].append(pattern)
        return grouped
