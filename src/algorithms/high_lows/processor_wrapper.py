"""Processor wrapper for high/low pattern processing.

This module provides an adapter that wraps the existing process_high_low_patterns
function to conform to the PatternProcessor interface.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.algorithms.high_lows.models.low import Low
from src.algorithms.high_lows.models.rebound import Rebound
from src.algorithms.high_lows.pattern_config import HighLowPatternConfig
from src.algorithms.high_lows.processor import process_high_low_patterns
from src.models.date_price import DatePrice
from src.pipelines.algorithms.base.interfaces import (
    PatternProcessor,
    ProcessedPatternsProtocol,
)


@dataclass
class ProcessedPatternsAdapter(ProcessedPatternsProtocol[Low, Rebound]):
    """Adapter to make processed patterns conform to the protocol.

    This adapts the result from process_high_low_patterns to match
    the ProcessedPatternsProtocol interface.

    Attributes:
        active: List of active Low patterns
        completed: List of completed Rebound patterns
    """

    active: list[Low]
    completed: list[Rebound]


class HighLowProcessor(PatternProcessor[Low, Rebound, HighLowPatternConfig]):
    """Processor for high/low patterns.

    Wraps the process_high_low_patterns function to provide a typed interface
    for the pipeline infrastructure.
    """

    def process(
        self,
        current_patterns: list[Low],
        new_prices: list[DatePrice],
        config: HighLowPatternConfig,
        ticker_history_id: int,
    ) -> ProcessedPatternsProtocol[Low, Rebound]:
        """Process high/low patterns with new price data.

        Args:
            current_patterns: Existing active Low patterns to update
            new_prices: New price data to process (chronological order)
            config: Configuration containing threshold
            ticker_history_id: Ticker history ID for creating new patterns

        Returns:
            Processed patterns with active and completed lists
        """
        # Call the existing processor function
        result = process_high_low_patterns(
            current_patterns=current_patterns,
            new_prices=new_prices,
            threshold=config.threshold,
            ticker_history_id=ticker_history_id,
        )

        # Adapt the result to the protocol
        return ProcessedPatternsAdapter(
            active=result.active_lows,
            completed=result.completed_rebounds,
        )
