"""Generic daily pipeline for algorithm patterns.

This module provides a reusable pipeline for daily pattern processing.
It works with any algorithm through dependency injection.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Generic, TypedDict

from src.models.date_price import DatePrice
from src.pipelines.algorithms.base.interfaces import (
    ActivePatternRepository,
    CompletedPatternRepository,
    PatternProcessor,
    TActive,
    TCompleted,
    TConfig,
)
from src.repos.equities.pricing.historical_eod_pricing_repository import (
    HistoricalEodPricingRepository,
)
from src.repos.equities.tickers.ticker_repository import TickerRepository


class DailyResult(TypedDict):
    """Result of daily pattern processing."""

    total_tickers_processed: int
    total_patterns_processed: int
    patterns_completed: int
    patterns_updated: int
    patterns_spawned: int
    patterns_expired: int
    errors: int


class DailyPipeline(Generic[TActive, TCompleted, TConfig]):
    """Generic pipeline for daily pattern processing.

    This pipeline:
    1. Gets all active (non-expired) patterns from database
    2. Gets today's EOD pricing data for each ticker
    3. Processes patterns with new prices using core algorithm
    4. Separates completed patterns from active patterns
    5. Deletes completed patterns from active table
    6. Inserts completed patterns into completed table
    7. Upserts updated/new active patterns
    8. Marks expired patterns (>1200 days old)

    Type parameters:
        TActive: The active pattern type (e.g., High, Low)
        TCompleted: The completed pattern type (e.g., Reversal, Rebound)
        TConfig: The configuration type (e.g., LowHighPatternConfig)
    """

    def __init__(
        self,
        active_repo: ActivePatternRepository[TActive],
        completed_repo: CompletedPatternRepository[TCompleted],
        processor: PatternProcessor[TActive, TCompleted, TConfig],
        configs: list[TConfig],
        pricing_repo: HistoricalEodPricingRepository,
        ticker_repo: TickerRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize daily pipeline.

        Args:
            active_repo: Repository for active patterns
            completed_repo: Repository for completed patterns
            processor: Pattern processor implementing PatternProcessor interface
            configs: List of configs to process (e.g., different thresholds)
            pricing_repo: Repository for pricing data
            ticker_repo: Repository for ticker data
            logger: Logger instance (optional)

        Raises:
            ValueError: If configs is empty
        """
        if not configs:
            raise ValueError("configs must not be empty")

        self.active_repo = active_repo
        self.completed_repo = completed_repo
        self.processor = processor
        self.configs = configs
        self.pricing_repo = pricing_repo
        self.ticker_repo = ticker_repo
        self.logger = logger or logging.getLogger(__name__)

    def run(self, calculation_date: date | None = None) -> DailyResult:
        """Run daily pattern processing.

        Args:
            calculation_date: Date to process (default: today)

        Returns:
            DailyResult with processing statistics
        """
        calc_date = calculation_date or date.today()
        self.logger.info(f"Starting daily processing for {calc_date}")

        result: DailyResult = {
            "total_tickers_processed": 0,
            "total_patterns_processed": 0,
            "patterns_completed": 0,
            "patterns_updated": 0,
            "patterns_spawned": 0,
            "patterns_expired": 0,
            "errors": 0,
        }

        try:
            # Step 1: Get all active patterns
            self.logger.info("Fetching all active patterns...")
            all_active_patterns = self.active_repo.get_all_active()
            result["total_patterns_processed"] = len(all_active_patterns)

            if not all_active_patterns:
                self.logger.info("No active patterns found. Nothing to process.")
                return result

            # Step 2: Group patterns by ticker_history_id for batch processing
            patterns_by_ticker = self._group_patterns_by_ticker(all_active_patterns)
            result["total_tickers_processed"] = len(patterns_by_ticker)

            # Step 3: Process each ticker's patterns
            all_updated_patterns = []
            all_completed_patterns = []
            completed_pattern_ids = []

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
                        all_updated_patterns.extend(ticker_patterns)
                        continue

                    # Check if close price is available
                    if pricing.close is None:
                        self.logger.debug(
                            f"No close price for ticker_history_id {ticker_history_id} on {calc_date}"
                        )
                        # Keep existing patterns as-is
                        all_updated_patterns.extend(ticker_patterns)
                        continue

                    # Convert to DatePrice
                    date_price = DatePrice(date=pricing.date, price=pricing.close)

                    # Group by threshold and process
                    patterns_by_threshold = self._group_patterns_by_threshold(
                        ticker_patterns
                    )

                    for config, threshold_patterns in patterns_by_threshold.items():
                        # Process patterns with the core algorithm
                        processed = self.processor.process(
                            threshold_patterns,
                            [date_price],
                            config,
                            ticker_history_id=ticker_history_id,
                        )

                        # Collect results from protocol interface
                        all_updated_patterns.extend(processed.active)
                        all_completed_patterns.extend(processed.completed)

                        # Track IDs of completed patterns to delete
                        for pattern in threshold_patterns:
                            # Check if this pattern was completed
                            if pattern not in processed.active and pattern.id:  # type: ignore[attr-defined]
                                completed_pattern_ids.append(pattern.id)  # type: ignore[attr-defined]

                        # Count spawned patterns
                        newly_spawned = len(processed.active) - len(threshold_patterns)
                        if newly_spawned > 0:
                            result["patterns_spawned"] += newly_spawned

                except Exception as e:
                    self.logger.error(
                        f"Error processing ticker_history_id {ticker_history_id}: {e}"
                    )
                    result["errors"] += 1
                    # Keep existing patterns for this ticker
                    all_updated_patterns.extend(ticker_patterns)

            # Step 4: Identify expired patterns
            expired_pattern_ids = [
                pattern.id  # type: ignore[attr-defined]
                for pattern in all_updated_patterns
                if pattern.id and pattern.is_expired()  # type: ignore[attr-defined]
            ]

            # Step 5: Database operations
            # Delete completed patterns
            if completed_pattern_ids:
                self.logger.info(
                    f"Deleting {len(completed_pattern_ids)} completed patterns"
                )
                self.active_repo.delete_by_ids(completed_pattern_ids)
                result["patterns_completed"] = len(completed_pattern_ids)

            # Insert completed patterns
            if all_completed_patterns:
                self.logger.info(
                    f"Inserting {len(all_completed_patterns)} completed patterns"
                )
                self.completed_repo.bulk_insert(all_completed_patterns)

            # Mark expired patterns
            if expired_pattern_ids:
                self.logger.info(
                    f"Marking {len(expired_pattern_ids)} patterns as expired"
                )
                self.active_repo.mark_as_expired(expired_pattern_ids)
                result["patterns_expired"] = len(expired_pattern_ids)

            # Upsert active patterns
            if all_updated_patterns:
                self.logger.info(
                    f"Upserting {len(all_updated_patterns)} active patterns"
                )
                upsert_result = self.active_repo.bulk_upsert(all_updated_patterns)
                result["patterns_updated"] = (
                    upsert_result["inserted"] + upsert_result["updated"]
                )

            self.logger.info(f"Daily processing complete: {result}")

        except Exception as e:
            self.logger.error(f"Error in daily pipeline: {e}")
            result["errors"] += 1

        return result

    def _group_patterns_by_ticker(
        self, patterns: list[TActive]
    ) -> dict[int, list[TActive]]:
        """Group patterns by ticker_history_id.

        Args:
            patterns: List of active patterns

        Returns:
            Dictionary mapping ticker_history_id to list of patterns
        """
        grouped: dict[int, list[TActive]] = {}
        for pattern in patterns:
            ticker_id = pattern.ticker_history_id  # type: ignore[attr-defined]
            if ticker_id not in grouped:
                grouped[ticker_id] = []
            grouped[ticker_id].append(pattern)
        return grouped

    def _group_patterns_by_threshold(
        self, patterns: list[TActive]
    ) -> dict[TConfig, list[TActive]]:
        """Group patterns by threshold (as config).

        Args:
            patterns: List of active patterns

        Returns:
            Dictionary mapping config to list of patterns

        Raises:
            ValueError: If a pattern's threshold doesn't match any config
        """
        # First group by threshold value
        by_threshold: dict[Decimal, list[TActive]] = {}
        for pattern in patterns:
            threshold = pattern.threshold  # type: ignore[attr-defined]
            if threshold not in by_threshold:
                by_threshold[threshold] = []
            by_threshold[threshold].append(pattern)

        # Then match thresholds to configs
        grouped: dict[TConfig, list[TActive]] = {}
        for threshold, threshold_patterns in by_threshold.items():
            # Find matching config
            matching_config = None
            for config in self.configs:
                if config.threshold == threshold:  # type: ignore[attr-defined]
                    matching_config = config
                    break

            if matching_config is None:
                raise ValueError(
                    f"No config found for threshold {threshold}. "
                    f"Available thresholds: {[c.threshold for c in self.configs]}"  # type: ignore[attr-defined]
                )

            grouped[matching_config] = threshold_patterns

        return grouped
