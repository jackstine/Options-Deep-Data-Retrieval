"""Database tables for low/high pattern data."""

from src.database.algorithms.tables.low_highs.highs import High
from src.database.algorithms.tables.low_highs.reversals import Reversal

__all__ = ["High", "Reversal"]
