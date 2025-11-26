"""Company with ticker data model for enriched company information."""

from __future__ import annotations

from dataclasses import dataclass

from src.models.company import Company
from src.models.ticker_history import TickerHistory


@dataclass(frozen=True)
class CompanyWithTickerDataModel:
    """Company data enriched with ticker history information.

    Combines company data with associated ticker history information.
    """

    company: Company
    ticker_history: TickerHistory
