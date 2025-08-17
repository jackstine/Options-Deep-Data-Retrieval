"""Centralized test providers for financial data generation using Faker."""

from faker.providers import BaseProvider


class StockMarketProvider(BaseProvider):
    """Faker provider for generating realistic stock market and financial data."""

    exchanges = ["NASDAQ", "NYSE", "AMEX", "OTC"]
    sectors = [
        "Technology",
        "Healthcare",
        "Financial Services",
        "Consumer Discretionary",
        "Industrials",
        "Communication Services",
        "Consumer Staples",
        "Energy",
        "Materials",
        "Real Estate",
        "Utilities",
    ]
    industries = [
        "Software",
        "Biotechnology",
        "Banks",
        "Retail",
        "Aerospace & Defense",
        "Semiconductors",
        "Pharmaceuticals",
        "Insurance",
        "Oil & Gas",
        "Telecommunications",
        "Automotive",
        "Food & Beverage",
        "Mining",
    ]

    def stock_ticker(self) -> str:
        """Generate a realistic stock ticker symbol (3-4 characters)."""
        length = self.random_element([3, 4])
        return "".join(self.random_choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", length=length))

    def stock_sector(self) -> str:
        """Generate a realistic stock market sector."""
        return self.random_element(self.sectors)

    def stock_industry(self) -> str:
        """Generate a realistic industry within a sector."""
        return self.random_element(self.industries)

    def stock_exchange(self) -> str:
        """Generate a realistic stock exchange."""
        return self.random_element(self.exchanges)

    def stock_price(self) -> float:
        """Generate a realistic stock price based on market categories."""
        category = self.random_element(["penny", "low", "medium", "high", "premium"])
        if category == "penny":
            return float(round(self.generator.random.uniform(0.01, 5.00), 2))
        elif category == "low":
            return float(round(self.generator.random.uniform(5.00, 25.00), 2))
        elif category == "medium":
            return float(round(self.generator.random.uniform(25.00, 100.00), 2))
        elif category == "high":
            return float(round(self.generator.random.uniform(100.00, 500.00), 2))
        else:  # premium
            return float(round(self.generator.random.uniform(500.00, 5000.00), 2))

    def volume(self) -> int:
        """Generate realistic trading volume."""
        return self.random_int(10_000, 100_000_000)

    def market_cap(self) -> int:
        """Generate realistic market capitalization."""
        category = self.random_element(["small", "mid", "large", "mega"])
        if category == "small":
            return self.random_int(300_000_000, 2_000_000_000)
        elif category == "mid":
            return self.random_int(2_000_000_000, 10_000_000_000)
        elif category == "large":
            return self.random_int(10_000_000_000, 200_000_000_000)
        else:  # mega
            return self.random_int(200_000_000_000, 3_000_000_000_000)

    def company_description(self) -> str:
        """Generate a realistic company description."""
        sector = self.stock_sector().lower()
        return f"A leading {sector} company specializing in innovative solutions and market excellence."

    def pe_ratio(self) -> float:
        """Generate a realistic P/E ratio."""
        return float(round(self.generator.random.uniform(5.0, 50.0), 2))

    def dividend_yield(self) -> float:
        """Generate a realistic dividend yield percentage."""
        return float(round(self.generator.random.uniform(0.0, 8.0), 2))

    def beta(self) -> float:
        """Generate a realistic stock beta value."""
        return float(round(self.generator.random.uniform(0.1, 3.0), 2))

    def earnings_per_share(self) -> float:
        """Generate realistic earnings per share."""
        return float(round(self.generator.random.uniform(-5.0, 25.0), 2))

    def revenue(self) -> int:
        """Generate realistic company revenue."""
        category = self.random_element(["small", "medium", "large", "mega"])
        if category == "small":
            return self.random_int(1_000_000, 100_000_000)
        elif category == "medium":
            return self.random_int(100_000_000, 1_000_000_000)
        elif category == "large":
            return self.random_int(1_000_000_000, 50_000_000_000)
        else:  # mega
            return self.random_int(50_000_000_000, 500_000_000_000)
