"""Abstract base classes and protocols for algorithm pipelines.

This module defines the interfaces that repositories and processors must implement
to work with the generic pipeline infrastructure.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from src.models.date_price import DatePrice

# Type variables
TActive = TypeVar("TActive")
TCompleted = TypeVar("TCompleted")
TConfig = TypeVar("TConfig")


# ============================================================================
# Repository Abstract Base Classes
# ============================================================================


class ActivePatternRepository(Generic[TActive], ABC):
    """Abstract base class for active pattern repositories.

    Provides a unified interface for repositories managing active patterns
    (HighsRepository, LowsRepository, etc.)

    Type parameters:
        TActive: The active pattern data model type
    """

    @abstractmethod
    def get_all_active(self) -> list[TActive]:
        """Get all non-expired active patterns.

        Returns:
            List of all active patterns
        """
        ...

    @abstractmethod
    def bulk_upsert(self, patterns: list[TActive]) -> dict[str, int]:
        """Insert or update multiple patterns.

        Args:
            patterns: List of patterns to upsert

        Returns:
            Dict with 'inserted' and 'updated' counts
        """
        ...

    @abstractmethod
    def delete_by_ids(self, pattern_ids: list[int]) -> int:
        """Delete patterns by their IDs.

        Args:
            pattern_ids: List of pattern IDs to delete

        Returns:
            Count of patterns deleted
        """
        ...

    @abstractmethod
    def mark_as_expired(self, pattern_ids: list[int]) -> int:
        """Mark patterns as expired.

        Args:
            pattern_ids: List of pattern IDs to mark as expired

        Returns:
            Count of patterns updated
        """
        ...


class CompletedPatternRepository(Generic[TCompleted], ABC):
    """Abstract base class for completed pattern repositories.

    Provides a unified interface for repositories managing completed patterns
    (ReversalsRepository, ReboundsRepository, etc.)

    Type parameters:
        TCompleted: The completed pattern data model type
    """

    @abstractmethod
    def bulk_insert(self, patterns: list[TCompleted]) -> int:
        """Bulk insert completed patterns.

        Args:
            patterns: List of completed patterns to insert

        Returns:
            Count of patterns inserted
        """
        ...


# ============================================================================
# Processor Protocol and Abstract Base Class
# ============================================================================


class ProcessedPatternsProtocol(Generic[TActive, TCompleted]):
    """Protocol for processed pattern results.

    This is the interface that processed pattern results must conform to.

    Type parameters:
        TActive: The active pattern type
        TCompleted: The completed pattern type

    Attributes:
        active: List of active patterns after processing
        completed: List of completed patterns after processing
    """

    active: list[TActive]
    completed: list[TCompleted]


class PatternProcessor(Generic[TActive, TCompleted, TConfig], ABC):
    """Abstract base class for pattern processors.

    Wraps processor functions to provide a unified interface for the pipeline.

    Type parameters:
        TActive: Active pattern type (e.g., High, Low)
        TCompleted: Completed pattern type (e.g., Reversal, Rebound)
        TConfig: Configuration type for processing
    """

    @abstractmethod
    def process(
        self,
        current_patterns: list[TActive],
        new_prices: list[DatePrice],
        config: TConfig,
        ticker_history_id: int,
    ) -> ProcessedPatternsProtocol[TActive, TCompleted]:
        """Process patterns with new price data.

        Args:
            current_patterns: Existing active patterns to update
            new_prices: New price data to process (chronological order)
            config: Configuration containing threshold and other parameters
            ticker_history_id: Ticker history ID for creating new patterns

        Returns:
            Processed patterns containing updated active and completed lists
        """
        ...
