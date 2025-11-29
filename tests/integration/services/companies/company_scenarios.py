"""Test scenarios for company integration tests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CompanyTestScenario:
    """Test scenario data for company tests."""

    company_name: str
    exchange: str
    sector: str | None = None
    industry: str | None = None
    country: str | None = None
    active: bool = True
    symbol: str = ""
