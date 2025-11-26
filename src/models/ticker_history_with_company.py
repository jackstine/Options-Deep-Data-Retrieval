"""Ticker history with company data model for enriched ticker information."""

from __future__ import annotations

from dataclasses import dataclass

from src.models.company import Company
from src.models.ticker_history import TickerHistory


@dataclass(frozen=True)
class TickerHistoryWithCompanyDataModel:
    """Ticker history data enriched with company information.

    Combines ticker history data with associated company information.
    """

    ticker_history: TickerHistory
    company: Company
