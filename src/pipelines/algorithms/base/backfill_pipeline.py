"""Generic backfill pipeline for algorithm patterns.

This module provides a reusable pipeline for backfilling historical pattern data.
It works with any algorithm through dependency injection.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Generic, TypedDict, cast

from src.models.date_price import DatePrice
from src.models.split_adjusted_pricing import SplitAdjustedPricing
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
from src.repos.equities.tickers.ticker_history_repository import (
    TickerHistoryRepository,
)
from src.services.pricing.split_adjusted_pricing_service import (
    SplitAdjustedPricingService,
)


class BackfillResult(TypedDict):
    """Result of backfill operation."""

    ticker_history_id: int
    from_date: str
    to_date: str
    total_patterns_generated: int
    active_patterns_inserted: int
    completed_patterns_inserted: int
    errors: int


class BackfillPipeline(Generic[TActive, TCompleted, TConfig]):
    """Generic pipeline for backfilling patterns from historical pricing data.

    This pipeline:
    1. Fetches all historical pricing data for a ticker
    2. For each config (threshold + other params)
    3. Initializes first pattern from first price
    4. Processes all prices chronologically using core algorithm
    5. Bulk inserts resulting active and completed patterns into database

    This is a one-time operation for generating historical pattern data.
    After backfill, use DailyPipeline for incremental updates.

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
        ticker_history_repo: TickerHistoryRepository,
        split_adjusted_pricing_service: SplitAdjustedPricingService,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize backfill pipeline.

        Args:
            active_repo: Repository for active patterns
            completed_repo: Repository for completed patterns
            processor: Pattern processor implementing PatternProcessor interface
            configs: List of configs to process (e.g., different thresholds)
            pricing_repo: Repository for pricing data
            ticker_history_repo: Repository for ticker history data
            split_adjusted_pricing_service: Service for split-adjusted pricing
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
        self.ticker_history_repo = ticker_history_repo
        self.split_adjusted_pricing_service = split_adjusted_pricing_service
        self.logger = logger or logging.getLogger(__name__)

    def _process_single_ticker(
        self,
        ticker_history_id: int,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> BackfillResult:
        """Process patterns for a single ticker history.

        Args:
            ticker_history_id: Ticker history ID to backfill
            from_date: Start date (default: all available history)
            to_date: End date (default: most recent date)

        Returns:
            BackfillResult with processing statistics
        """
        self.logger.info(
            f"Starting backfill for ticker_history_id={ticker_history_id}"
        )

        result: BackfillResult = {
            "ticker_history_id": ticker_history_id,
            "from_date": "",
            "to_date": "",
            "total_patterns_generated": 0,
            "active_patterns_inserted": 0,
            "completed_patterns_inserted": 0,
            "errors": 0,
        }

        try:
            # Step 1: Get split-adjusted pricing data
            self.logger.info(
                f"Fetching split-adjusted pricing for ticker_history_id={ticker_history_id}"
            )
            split_adjusted_data = cast(
                SplitAdjustedPricing[DatePrice],
                self.split_adjusted_pricing_service.get_split_adjusted_pricing_with_ticker_history_id(
                    ticker_history_id=ticker_history_id,
                    from_date=from_date or date(1900, 1, 1),
                    to_date=to_date or date.today(),
                    include_ohlc=False,
                ),
            )

            # Extract prices from split-adjusted result
            date_prices = split_adjusted_data.prices

            if not date_prices:
                self.logger.warning(
                    f"No pricing data found for ticker_history_id={ticker_history_id}"
                )
                return result

            # Sort chronologically (should already be sorted, but ensure it)
            date_prices = sorted(date_prices, key=lambda p: p.date)
            result["from_date"] = str(date_prices[0].date)
            result["to_date"] = str(date_prices[-1].date)

            self.logger.info(
                f"Processing {len(date_prices)} days of split-adjusted pricing data "
                f"from {result['from_date']} to {result['to_date']}"
            )

            # Step 3: Process each config
            all_active_patterns = []
            all_completed_patterns = []

            for config in self.configs:
                threshold = config.threshold  # type: ignore[attr-defined]
                self.logger.info(
                    f"Processing threshold {float(threshold):.0%} for "
                    f"ticker_history_id={ticker_history_id}"
                )

                try:
                    # Process all prices with this config
                    # Processor will create initial pattern from first price if needed
                    processed = self.processor.process(
                        [],
                        date_prices,
                        config,
                        ticker_history_id=ticker_history_id,
                    )

                    # Collect results from protocol interface
                    all_active_patterns.extend(processed.active)
                    all_completed_patterns.extend(processed.completed)

                    self.logger.info(
                        f"Threshold {float(threshold):.0%}: "
                        f"{len(processed.active)} active patterns, "
                        f"{len(processed.completed)} completed patterns"
                    )

                except Exception as e:
                    self.logger.error(
                        f"Error processing threshold {float(threshold):.0%}: {e}"
                    )
                    result["errors"] += 1

            # Step 5: Bulk insert into database
            if all_active_patterns:
                self.logger.info(
                    f"Inserting {len(all_active_patterns)} active patterns"
                )
                upsert_result = self.active_repo.bulk_upsert(all_active_patterns)
                result["active_patterns_inserted"] = (
                    upsert_result["inserted"] + upsert_result["updated"]
                )

            if all_completed_patterns:
                self.logger.info(
                    f"Inserting {len(all_completed_patterns)} completed patterns"
                )
                completed_inserted = self.completed_repo.bulk_insert(all_completed_patterns)
                result["completed_patterns_inserted"] = completed_inserted

            result["total_patterns_generated"] = len(all_active_patterns) + len(
                all_completed_patterns
            )

            self.logger.info(
                f"Backfill complete for ticker_history_id={ticker_history_id}: {result}"
            )

        except Exception as e:
            self.logger.error(
                f"Error in backfill pipeline for ticker_history_id={ticker_history_id}: {e}"
            )
            result["errors"] += 1

        return result

    def run(
        self,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[BackfillResult]:
        """Backfill patterns for all ticker histories.

        Queries all ticker histories from the database and processes each one.

        Args:
            from_date: Start date (default: all available history)
            to_date: End date (default: most recent date)

        Returns:
            List of BackfillResult for each ticker history
        """
        # Get all ticker histories
        self.logger.info("Fetching all ticker histories")
        all_ticker_histories = self.ticker_history_repo.get_all_ticker_histories()
        ticker_history_ids = [
            th.id for th in all_ticker_histories if th.id is not None
        ]

        self.logger.info(
            f"Starting backfill for {len(ticker_history_ids)} ticker histories"
        )

        results = []
        for i, ticker_history_id in enumerate(ticker_history_ids, 1):
            self.logger.info(
                f"Processing ticker history {i}/{len(ticker_history_ids)}: "
                f"ticker_history_id={ticker_history_id}"
            )
            result = self._process_single_ticker(ticker_history_id, from_date, to_date)
            results.append(result)

        # Summary
        total_patterns = sum(r["total_patterns_generated"] for r in results)
        total_errors = sum(r["errors"] for r in results)
        self.logger.info(
            f"Backfill complete: {total_patterns} patterns generated, "
            f"{total_errors} errors across {len(results)} ticker histories"
        )

        return results
