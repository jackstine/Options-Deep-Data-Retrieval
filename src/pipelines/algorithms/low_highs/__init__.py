"""Pipelines for low/high pattern detection.

This module provides configured instances of the generic pipeline classes
for the low/high algorithm.

IMPORTANT: Commands must provide configs when calling get_backfill_pipeline()
and get_daily_pipeline(). The factory functions no longer create default configs.
"""

import logging

from src.algorithms.low_highs.models.high import High
from src.algorithms.low_highs.models.reversal import Reversal
from src.algorithms.low_highs.pattern_config import LowHighPatternConfig
from src.algorithms.low_highs.processor_wrapper import LowHighProcessor
from src.pipelines.algorithms.base import BackfillPipeline, DailyPipeline
from src.repos.algorithms.low_highs.highs_repository import HighsRepository
from src.repos.algorithms.low_highs.reversals_repository import ReversalsRepository
from src.repos.equities.pricing.historical_eod_pricing_repository import (
    HistoricalEodPricingRepository,
)
from src.repos.equities.tickers.ticker_history_repository import (
    TickerHistoryRepository,
)
from src.repos.equities.tickers.ticker_repository import TickerRepository
from src.services.pricing.split_adjusted_pricing_service import (
    SplitAdjustedPricingService,
)


def get_backfill_pipeline(
    configs: list[LowHighPatternConfig],
) -> BackfillPipeline[High, Reversal, LowHighPatternConfig]:
    """Get or create the BackfillLowHighPipeline instance.

    Args:
        configs: List of configs to process (e.g., different thresholds)

    Returns:
        Backfill pipeline instance

    Raises:
        ValueError: If configs is empty or None
    """
    if not configs:
        raise ValueError("configs must be provided and cannot be empty")

    return BackfillPipeline[High, Reversal, LowHighPatternConfig](
        active_repo=HighsRepository(),
        completed_repo=ReversalsRepository(),
        processor=LowHighProcessor(),
        configs=configs,
        pricing_repo=HistoricalEodPricingRepository(),
        ticker_history_repo=TickerHistoryRepository(),
        split_adjusted_pricing_service=SplitAdjustedPricingService(),
        logger=logging.getLogger(__name__),
    )


def get_daily_pipeline(
    configs: list[LowHighPatternConfig],
) -> DailyPipeline[High, Reversal, LowHighPatternConfig]:
    """Get or create the DailyLowHighPipeline instance.

    Args:
        configs: List of configs to process (e.g., different thresholds)

    Returns:
        Daily pipeline instance

    Raises:
        ValueError: If configs is empty or None
    """
    if not configs:
        raise ValueError("configs must be provided and cannot be empty")

    return DailyPipeline[High, Reversal, LowHighPatternConfig](
        active_repo=HighsRepository(),
        completed_repo=ReversalsRepository(),
        processor=LowHighProcessor(),
        configs=configs,
        pricing_repo=HistoricalEodPricingRepository(),
        ticker_repo=TickerRepository(),
        logger=logging.getLogger(__name__),
    )


# For backward compatibility, expose as module-level callables
BackfillLowHighPipeline = get_backfill_pipeline
DailyLowHighPipeline = get_daily_pipeline

__all__ = ["BackfillLowHighPipeline", "DailyLowHighPipeline", "get_backfill_pipeline", "get_daily_pipeline"]
