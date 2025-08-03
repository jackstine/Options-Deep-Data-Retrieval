"""Example usage of the NASDAQ company data source provider."""

import json
from pathlib import Path
from src.data_sources.nasdaq.nasdaq_company_provider import NasdaqCompanyProvider
from src.data_sources.nasdaq.company import get_dict_of_stocks


def main() -> None:
    """Demonstrate usage of the NASDAQ company data source."""
    
    print("=== NASDAQ Company Provider Usage ===")
    
    # First, save raw company data to JSON file
    print("\n=== Saving Raw Company Data ===")
    save_raw_companies_to_json()
    
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
    
    # Save companies to file
    print("\n=== File Operations ===")
    file_path = "data/nasdaq_companies.json"
    
    print(f"Saving all companies to {file_path}...")
    if provider.save_to_file(file_path):
        print("✓ Successfully saved companies to file")
    else:
        print("✗ Failed to save companies to file")
        return
    
    # Save filtered companies (tech companies)
    tech_file_path = "data/tech_companies.json"
    tech_companies = provider.search_companies("Tech")
    print(f"\nSaving {len(tech_companies)} tech companies to {tech_file_path}...")
    if provider.save_to_file(tech_file_path, tech_companies):
        print("✓ Successfully saved tech companies to file")
    else:
        print("✗ Failed to save tech companies to file")
    
    # Demonstrate loading from file
    print(f"\nLoading companies from {file_path}...")
    try:
        # Clear cache first to test loading
        provider.clear_cache()
        loaded_companies = provider.load_from_file(file_path)
        print(f"✓ Successfully loaded {len(loaded_companies)} companies from file")
        
        # Show first few loaded companies
        print("\nFirst 3 loaded companies:")
        for company in loaded_companies[:3]:
            print(f"  {company.ticker} - {company.company_name} ({company.exchange})")
            
    except FileNotFoundError:
        print("✗ File not found")
    except ValueError as e:
        print(f"✗ Invalid file format: {e}")
    except Exception as e:
        print(f"✗ Error loading file: {e}")


def save_raw_companies_to_json() -> None:
    """Fetch raw company data and save to JSON file."""
    try:
        print("Fetching raw company data from NASDAQ...")
        raw_companies = get_dict_of_stocks()
        
        if raw_companies is None:
            print("✗ Failed to fetch raw company data")
            return
        
        # Ensure data directory exists
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Save to JSON file with pretty formatting
        output_file = data_dir / "raw_companies.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(raw_companies, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Successfully saved {len(raw_companies)} raw company records to {output_file}")
        
    except Exception as e:
        print(f"✗ Error saving raw company data: {e}")


if __name__ == "__main__":
    main()