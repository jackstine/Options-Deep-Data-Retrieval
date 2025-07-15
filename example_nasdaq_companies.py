"""Example usage of the NASDAQ company data source provider."""

from src.data_sources.nasdaq.nasdaq_company_provider import NasdaqCompanyProvider


def main() -> None:
    """Demonstrate usage of the NASDAQ company data source."""
    
    print("=== NASDAQ Company Provider Usage ===")
    provider = NasdaqCompanyProvider()
    
    # Fetch all companies
    print("\n=== Fetching All Companies ===")
    companies = provider.fetch_companies()
    print(f"Fetched {len(companies)} companies")
    
    # Show first 10 companies
    print("\nFirst 10 companies:")
    for i, company in enumerate(companies[:10]):
        company.print()
        if i < 9:  # Don't print separator after last item
            print("-" * 40)
    
    # Search for specific companies
    print("\n=== Company Search Examples ===")
    
    # Search by ticker
    apple = provider.get_company_by_ticker("AAPL")
    if apple:
        print("Found Apple Inc.:")
        apple.print()
    else:
        print("Apple Inc. (AAPL) not found")
    
    # Search by name
    print("\nSearching for companies with 'Tech' in name:")
    tech_companies = provider.search_companies("Tech")
    for company in tech_companies[:5]:  # Show first 5 results
        print(f"  {company.ticker} - {company.company_name}")
    
    # Filter by exchange
    print("\n=== Companies by Exchange ===")
    nasdaq_companies = provider.get_companies_by_exchange("NASDAQ")
    nyse_companies = provider.get_companies_by_exchange("NYSE")
    
    print(f"NASDAQ companies: {len(nasdaq_companies):,}")
    print(f"NYSE companies: {len(nyse_companies):,}")
    
    # Show sample from each exchange
    if nasdaq_companies:
        print(f"\nSample NASDAQ companies:")
        for company in nasdaq_companies[:3]:
            print(f"  {company.ticker} - {company.company_name}")
    
    if nyse_companies:
        print(f"\nSample NYSE companies:")
        for company in nyse_companies[:3]:
            print(f"  {company.ticker} - {company.company_name}")


if __name__ == "__main__":
    main()