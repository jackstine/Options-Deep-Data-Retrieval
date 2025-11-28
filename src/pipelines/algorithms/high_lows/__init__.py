"""Pipelines for high/low pattern detection.

This module provides configured instances of the generic pipeline classes
for the high/low algorithm.

IMPORTANT: Commands must provide configs when calling get_backfill_pipeline()
and get_daily_pipeline(). The factory functions no longer create default configs.
"""

import logging

from src.algorithms.high_lows.models.low import Low
from src.algorithms.high_lows.models.rebound import Rebound
from src.algorithms.high_lows.pattern_config import HighLowPatternConfig
from src.algorithms.high_lows.processor_wrapper import HighLowProcessor
from src.pipelines.algorithms.base import BackfillPipeline, DailyPipeline
from src.repos.algorithms.high_lows.lows_repository import LowsRepository
from src.repos.algorithms.high_lows.rebounds_repository import ReboundsRepository
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
    configs: list[HighLowPatternConfig],
) -> BackfillPipeline[Low, Rebound, HighLowPatternConfig]:
    """Get or create the BackfillHighLowPipeline instance.

    Args:
        configs: List of configs to process (e.g., different thresholds)

    Returns:
        Backfill pipeline instance

    Raises:
        ValueError: If configs is empty or None
    """
    if not configs:
        raise ValueError("configs must be provided and cannot be empty")

    return BackfillPipeline[Low, Rebound, HighLowPatternConfig](
        active_repo=LowsRepository(),
        completed_repo=ReboundsRepository(),
        processor=HighLowProcessor(),
        configs=configs,
        pricing_repo=HistoricalEodPricingRepository(),
        ticker_history_repo=TickerHistoryRepository(),
        split_adjusted_pricing_service=SplitAdjustedPricingService(),
        logger=logging.getLogger(__name__),
    )


def get_daily_pipeline(
    configs: list[HighLowPatternConfig],
) -> DailyPipeline[Low, Rebound, HighLowPatternConfig]:
    """Get or create the DailyHighLowPipeline instance.

    Args:
        configs: List of configs to process (e.g., different thresholds)

    Returns:
        Daily pipeline instance

    Raises:
        ValueError: If configs is empty or None
    """
    if not configs:
        raise ValueError("configs must be provided and cannot be empty")

    return DailyPipeline[Low, Rebound, HighLowPatternConfig](
        active_repo=LowsRepository(),
        completed_repo=ReboundsRepository(),
        processor=HighLowProcessor(),
        configs=configs,
        pricing_repo=HistoricalEodPricingRepository(),
        ticker_repo=TickerRepository(),
        logger=logging.getLogger(__name__),
    )


# For backward compatibility, expose as module-level callables
BackfillHighLowPipeline = get_backfill_pipeline
DailyHighLowPipeline = get_daily_pipeline

__all__ = ["BackfillHighLowPipeline", "DailyHighLowPipeline", "get_backfill_pipeline", "get_daily_pipeline"]
