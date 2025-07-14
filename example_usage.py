"""Example usage of the Yahoo Finance data source provider."""

from src.data_sources.providers.yahoo_finance import YahooFinanceProvider


def main() -> None:
    """Demonstrate usage of the Yahoo Finance data source."""
    
    print("=== Yahoo Finance Provider Usage ===")
    provider = YahooFinanceProvider()
    
    # Test connection
    if provider.validate_connection():
        print("✓ Connection to Yahoo Finance validated")
    else:
        print("✗ Failed to connect to Yahoo Finance")
        return
    
    # Fetch quotes for multiple symbols
    symbols = ["AAPL", "GOOGL", "MSFT"]
    print(f"\nFetching quotes for: {symbols}")
    
    quotes = provider.fetch_quotes(symbols)
    
    for quote in quotes:
        print(f"\n{quote.symbol}:")
        print(f"  Price: ${quote.price}")
        print(f"  Volume: {quote.volume:,}")
        print(f"  Day High: ${quote.day_high}")
        print(f"  Day Low: ${quote.day_low}")
        print(f"  Market Cap: ${quote.market_cap}")
        print(f"  Source: {quote.source}")
        print(f"  Timestamp: {quote.timestamp}")
    
    # Fetch additional single quote
    print("\n=== Single Quote Example ===")
    single_quote = provider.fetch_quotes(["TSLA"])
    if single_quote:
        quote = single_quote[0]
        print(f"\nTSLA Quote:")
        print(f"  Price: ${quote.price}")
        print(f"  P/E Ratio: {quote.pe_ratio}")
        print(f"  52-Week High: ${quote.fifty_two_week_high}")
        print(f"  52-Week Low: ${quote.fifty_two_week_low}")
    
    # Show sample supported symbols
    supported_symbols = provider.get_supported_symbols()
    print(f"\nSample supported symbols: {supported_symbols[:10]}...")


if __name__ == "__main__":
    main()