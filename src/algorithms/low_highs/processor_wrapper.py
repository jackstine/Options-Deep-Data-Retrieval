"""Processor wrapper for low/high pattern processing.

This module provides an adapter that wraps the existing process_low_high_patterns
function to conform to the PatternProcessor interface.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.algorithms.low_highs.models.high import High
from src.algorithms.low_highs.models.reversal import Reversal
from src.algorithms.low_highs.pattern_config import LowHighPatternConfig
from src.algorithms.low_highs.processor import process_low_high_patterns
from src.models.date_price import DatePrice
from src.pipelines.algorithms.base.interfaces import (
    PatternProcessor,
    ProcessedPatternsProtocol,
)


@dataclass
class ProcessedPatternsAdapter(ProcessedPatternsProtocol[High, Reversal]):
    """Adapter to make processed patterns conform to the protocol.

    This adapts the result from process_low_high_patterns to match
    the ProcessedPatternsProtocol interface.

    Attributes:
        active: List of active High patterns
        completed: List of completed Reversal patterns
    """

    active: list[High]
    completed: list[Reversal]


class LowHighProcessor(PatternProcessor[High, Reversal, LowHighPatternConfig]):
    """Processor for low/high patterns.

    Wraps the process_low_high_patterns function to provide a typed interface
    for the pipeline infrastructure.
    """

    def process(
        self,
        current_patterns: list[High],
        new_prices: list[DatePrice],
        config: LowHighPatternConfig,
        ticker_history_id: int,
    ) -> ProcessedPatternsProtocol[High, Reversal]:
        """Process low/high patterns with new price data.

        Args:
            current_patterns: Existing active High patterns to update
            new_prices: New price data to process (chronological order)
            config: Configuration containing threshold
            ticker_history_id: Ticker history ID for creating new patterns

        Returns:
            Processed patterns with active and completed lists
        """
        # Call the existing processor function
        result = process_low_high_patterns(
            current_patterns=current_patterns,
            new_prices=new_prices,
            threshold=config.threshold,
            ticker_history_id=ticker_history_id,
        )

        # Adapt the result to the protocol
        return ProcessedPatternsAdapter(
            active=result.active_highs,
            completed=result.completed_reversals,
        )
