"""Algorithm database tables."""

from src.database.algorithms.tables.highs import High
from src.database.algorithms.tables.lows import Low
from src.database.algorithms.tables.rebounds import Rebound
from src.database.algorithms.tables.reversals import Reversal

__all__ = ["High", "Low", "Rebound", "Reversal"]
