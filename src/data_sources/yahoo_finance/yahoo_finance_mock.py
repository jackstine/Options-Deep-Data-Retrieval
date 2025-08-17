"""Mock implementation of Yahoo Finance data source for testing."""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

from faker import Faker

from src.data_sources.base.base import DataSourceBase
from src.data_sources.models.stock_quote import StockQuote
from src.data_sources.models.test_providers import StockMarketProvider

logger = logging.getLogger(__name__)


class YahooFinanceProviderMock(DataSourceBase):
    """Mock implementation of YahooFinanceProvider for testing purposes."""

    def __init__(self, timeout: int = 30, seed: int = 12345):
        """Initialize mock Yahoo Finance provider.

        Args:
            timeout: Request timeout in seconds (ignored in mock)
            seed: Seed for consistent fake data generation
        """
        self.timeout = timeout
        self._name = "Yahoo Finance (Mock)"

        # Initialize Faker for realistic data
        self.fake = Faker()
        self.fake.add_provider(StockMarketProvider)
        Faker.seed(seed)

        # Mock configuration
        self._connection_valid = True
        self._should_fail = False
        self._error_message = "Mock API error"
        self._supported_symbols: set[str] = set()

        # Initialize with common symbols
        self._initialize_supported_symbols()

    def _initialize_supported_symbols(self) -> None:
        """Initialize supported symbols with realistic stock tickers."""
        major_symbols = [
            "AAPL",
            "GOOGL",
            "GOOG",
            "MSFT",
            "AMZN",
            "TSLA",
            "META",
            "NVDA",
            "AMD",
            "NFLX",
            "UBER",
            "LYFT",
            "ZOOM",
            "SHOP",
            "SQ",
            "PYPL",
            "CRM",
            "ORCL",
            "IBM",
            "INTC",
            "CSCO",
            "BA",
            "JPM",
            "BAC",
            "WFC",
            "V",
            "MA",
            "JNJ",
            "PFE",
            "KO",
            "PEP",
            "WMT",
            "TGT",
        ]

        # Add major symbols
        self._supported_symbols.update(major_symbols)

        # Add some generated symbols for variety
        for _ in range(50):
            self._supported_symbols.add(self.fake.stock_ticker())

    @property
    def name(self) -> str:
        """Get the name of the data source."""
        return self._name

    def fetch_quotes(self, symbols: list[str]) -> list[StockQuote]:
        """Mock fetch stock quotes for given symbols.

        Args:
            symbols: List of stock symbols to fetch quotes for

        Returns:
            List of mock StockQuote objects with realistic data
        """
        if self._should_fail:
            raise Exception(self._error_message)

        if not self._connection_valid:
            raise ConnectionError("Mock: Yahoo Finance connection is not available")

        quotes: list[StockQuote] = []

        for symbol in symbols:
            try:
                # Generate mock quote data
                quote = self._generate_mock_stock_quote(symbol.upper())
                if quote:
                    quotes.append(quote)
                else:
                    logger.warning(f"Mock: No data available for symbol: {symbol}")

            except Exception as e:
                logger.error(f"Mock: Error fetching data for {symbol}: {str(e)}")
                continue

        return quotes

    def _generate_mock_stock_quote(self, symbol: str) -> StockQuote | None:
        """Generate a mock StockQuote with realistic financial data.

        Args:
            symbol: Stock symbol

        Returns:
            Mock StockQuote object with realistic data
        """
        try:
            # Only generate quotes for "supported" symbols to simulate real API behavior
            if symbol not in self._supported_symbols:
                return None

            # Generate realistic stock price data
            base_price = self.fake.stock_price()

            # Calculate related prices based on base price
            price_variance = base_price * 0.05  # 5% variance for highs/lows

            day_high = base_price + self.fake.pyfloat(
                min_value=0, max_value=price_variance
            )
            day_low = base_price - self.fake.pyfloat(
                min_value=0, max_value=price_variance
            )

            # Previous close should be close to current price
            previous_close = base_price + self.fake.pyfloat(
                min_value=-price_variance * 0.5, max_value=price_variance * 0.5
            )

            # Open price typically near previous close
            open_price = previous_close + self.fake.pyfloat(
                min_value=-price_variance * 0.3, max_value=price_variance * 0.3
            )

            # 52-week range should be wider
            week_52_high = base_price + self.fake.pyfloat(
                min_value=price_variance, max_value=price_variance * 3
            )
            week_52_low = base_price - self.fake.pyfloat(
                min_value=price_variance, max_value=price_variance * 2
            )

            # Bid/Ask spread
            spread = base_price * 0.001  # 0.1% spread
            bid = base_price - spread
            ask = base_price + spread

            quote = StockQuote(
                symbol=symbol,
                price=Decimal(str(round(base_price, 2))),
                bid=Decimal(str(round(bid, 2))),
                ask=Decimal(str(round(ask, 2))),
                volume=self.fake.volume(),
                market_cap=Decimal(str(self.fake.market_cap())),
                day_high=Decimal(str(round(day_high, 2))),
                day_low=Decimal(str(round(day_low, 2))),
                previous_close=Decimal(str(round(previous_close, 2))),
                open_price=Decimal(str(round(open_price, 2))),
                fifty_two_week_high=Decimal(str(round(week_52_high, 2))),
                fifty_two_week_low=Decimal(str(round(week_52_low, 2))),
                pe_ratio=Decimal(
                    str(round(self.fake.pyfloat(min_value=5, max_value=50), 2))
                ),
                dividend_yield=Decimal(
                    str(round(self.fake.pyfloat(min_value=0, max_value=8), 2))
                )
                if self.fake.boolean(chance_of_getting_true=60)
                else None,
                timestamp=datetime.now(),
                source=self.name,
            )

            return quote

        except Exception as e:
            logger.error(f"Mock: Error generating mock data for {symbol}: {str(e)}")
            return None

    def validate_connection(self) -> bool:
        """Mock validate connection to Yahoo Finance.

        Returns:
            True if mock connection is valid, False otherwise
        """
        if self._should_fail:
            logger.error("Mock: Connection validation failed due to simulated error")
            return False

        return self._connection_valid

    def get_supported_symbols(self) -> list[str]:
        """Get list of mock supported stock symbols.

        Returns:
            List of mock supported stock symbols
        """
        return sorted(list(self._supported_symbols))

    # Mock-specific utility methods
    def set_connection_valid(self, valid: bool) -> None:
        """Set connection validity for testing."""
        self._connection_valid = valid

    def simulate_error(self, error_message: str) -> None:
        """Configure mock to simulate an error."""
        self._should_fail = True
        self._error_message = error_message

    def reset_error(self) -> None:
        """Reset mock to normal operation."""
        self._should_fail = False
        self._error_message = ""

    def add_supported_symbol(self, symbol: str) -> None:
        """Add a symbol to the supported symbols list."""
        self._supported_symbols.add(symbol.upper())

    def remove_supported_symbol(self, symbol: str) -> None:
        """Remove a symbol from the supported symbols list."""
        self._supported_symbols.discard(symbol.upper())

    def clear_supported_symbols(self) -> None:
        """Clear all supported symbols."""
        self._supported_symbols.clear()

    def get_supported_symbols_count(self) -> int:
        """Get count of supported symbols."""
        return len(self._supported_symbols)

    def generate_batch_quotes(self, symbol_count: int = 10) -> list[StockQuote]:
        """Generate a batch of mock quotes for testing."""
        # Get random subset of supported symbols
        available_symbols = list(self._supported_symbols)
        if len(available_symbols) < symbol_count:
            symbol_count = len(available_symbols)

        selected_symbols = self.fake.random_choices(
            available_symbols, length=symbol_count
        )
        return self.fetch_quotes(list(selected_symbols))

    def simulate_rate_limit(self) -> None:
        """Simulate API rate limiting."""
        self.simulate_error("Rate limit exceeded. Please try again later.")

    def simulate_network_error(self) -> None:
        """Simulate network connectivity error."""
        self.simulate_error("Network timeout - unable to connect to Yahoo Finance")

    def simulate_invalid_symbol_response(self, symbol: str) -> None:
        """Simulate response for invalid symbol."""
        if symbol.upper() in self._supported_symbols:
            self._supported_symbols.remove(symbol.upper())


# Factory function for easy mock creation
def create_yahoo_finance_provider_mock(
    timeout: int = 30, seed: int = 12345
) -> YahooFinanceProviderMock:
    """Factory function to create a YahooFinanceProviderMock instance."""
    return YahooFinanceProviderMock(timeout=timeout, seed=seed)


# Example usage for testing
if __name__ == "__main__":
    # Create mock provider
    mock_provider = create_yahoo_finance_provider_mock()

    print(f"Mock provider name: {mock_provider.name}")
    print(f"Connection valid: {mock_provider.validate_connection()}")
    print(f"Supported symbols count: {mock_provider.get_supported_symbols_count()}")

    # Test fetching quotes for common symbols
    test_symbols = ["AAPL", "MSFT", "GOOGL", "INVALID_SYMBOL"]
    print("\n--- Testing Quote Fetching ---")
    print(f"Requesting quotes for: {test_symbols}")

    quotes = mock_provider.fetch_quotes(test_symbols)
    print(f"Received {len(quotes)} quotes")

    # Display first few quotes
    for quote in quotes[:2]:
        print(f"\n{quote.symbol}:")
        print(f"  Price: ${quote.price}")
        print(f"  Volume: {quote.volume:,}")
        print(
            f"  Market Cap: ${quote.market_cap:,}"
            if quote.market_cap
            else "  Market Cap: N/A"
        )
        print(f"  Day Range: ${quote.day_low} - ${quote.day_high}")
        print(
            f"  52-Week Range: ${quote.fifty_two_week_low} - ${quote.fifty_two_week_high}"
        )
        if quote.pe_ratio:
            print(f"  P/E Ratio: {quote.pe_ratio}")
        if quote.dividend_yield:
            print(f"  Dividend Yield: {quote.dividend_yield}%")

    # Test error simulation
    print("\n--- Testing Error Simulation ---")
    mock_provider.simulate_rate_limit()

    try:
        quotes = mock_provider.fetch_quotes(["AAPL"])
    except Exception as e:
        print(f"Caught expected error: {e}")

    # Reset and test again
    mock_provider.reset_error()
    quotes = mock_provider.fetch_quotes(["AAPL"])
    print(f"After reset: Generated {len(quotes)} quotes successfully")

    # Test connection validity
    print("\n--- Testing Connection Validity ---")
    mock_provider.set_connection_valid(False)
    print(f"Connection valid: {mock_provider.validate_connection()}")

    try:
        quotes = mock_provider.fetch_quotes(["AAPL"])
    except ConnectionError as e:
        print(f"Caught expected connection error: {e}")

    mock_provider.set_connection_valid(True)
    print(f"Connection reset to valid: {mock_provider.validate_connection()}")

    # Test batch generation
    print("\n--- Testing Batch Generation ---")
    batch_quotes = mock_provider.generate_batch_quotes(5)
    print(f"Generated batch of {len(batch_quotes)} quotes:")
    for quote in batch_quotes:
        print(f"  {quote.symbol}: ${quote.price}")

    # Test symbol management
    print("\n--- Testing Symbol Management ---")
    original_count = mock_provider.get_supported_symbols_count()
    mock_provider.add_supported_symbol("TEST123")
    new_count = mock_provider.get_supported_symbols_count()
    print(f"Added symbol: {original_count} -> {new_count}")

    mock_provider.remove_supported_symbol("TEST123")
    final_count = mock_provider.get_supported_symbols_count()
    print(f"Removed symbol: {new_count} -> {final_count}")
