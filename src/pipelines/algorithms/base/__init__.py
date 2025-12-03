"""Base infrastructure for algorithm pipelines.

This module provides generic, reusable pipeline components that work with
any algorithm through dependency injection and abstract interfaces.
"""

from src.pipelines.algorithms.base.backfill_pipeline import (
    BackfillPipeline,
    BackfillResult,
)
from src.pipelines.algorithms.base.daily_pipeline import DailyPipeline, DailyResult
from src.pipelines.algorithms.base.interfaces import (
    ActivePatternRepository,
    CompletedPatternRepository,
    PatternProcessor,
    ProcessedPatternsProtocol,
)

__all__ = [
    # Pipeline classes
    "BackfillPipeline",
    "DailyPipeline",
    # Result types
    "BackfillResult",
    "DailyResult",
    # Abstract Base Classes
    "ActivePatternRepository",
    "CompletedPatternRepository",
    "PatternProcessor",
    # Protocols
    "ProcessedPatternsProtocol",
]
