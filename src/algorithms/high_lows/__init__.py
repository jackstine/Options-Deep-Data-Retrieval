"""High/Low pattern detection algorithm.

Detects patterns where price drops from a peak, then rebounds.
"""

from src.algorithms.high_lows.processor import process_high_low_patterns
from src.algorithms.high_lows.pattern_calculator import PatternCalculator

__all__ = ["process_high_low_patterns", "PatternCalculator"]
