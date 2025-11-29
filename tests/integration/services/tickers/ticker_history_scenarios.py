"""Test scenarios for ticker history integration tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class TickerHistoryTestScenario:
    """Test scenario for ticker history data."""

    symbol: str
    valid_from: date
    valid_to: date | None = None


@dataclass
class CompanyTestScenario:
    """Test scenario for company data."""

    company_name: str
    exchange: str
    sector: str | None = None
    industry: str | None = None
    country: str | None = None
    active: bool = True
