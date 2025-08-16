# Simple Company Ingestion Pipeline Design

## Overview

This document outlines a simple, practical company ingestion pipeline that can handle multiple data sources with minimal complexity. The design focuses on getting data from various sources into the database efficiently while keeping the code maintainable.

## Current State

**What we have:**
- `NasdaqScreenerSyncProcessor`: Works with NASDAQ screener files
- `CompanyDataSourceBase`: Base class for data sources
- `CompanyRepository`: Database operations (already using BaseRepository)

**What we want:**
- Simple way to add new data sources (Yahoo Finance, SEC, etc.)
- Basic validation to ensure data quality
- Easy way to run ingestion from different sources

## Simple Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│   Simple        │───▶│   Database      │
│                 │    │   Pipeline      │    │                 │
│ • NASDAQ Files  │    │                 │    │ • Companies     │
│ • Yahoo API     │    │ 1. Load Data    │    │ • Tickers       │
│ • Manual CSV    │    │ 2. Clean Data   │    │ • History       │
│                 │    │ 3. Save to DB   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Simple Data Source Interface

### Basic Data Source Contract

```python
from abc import ABC, abstractmethod
from typing import List
from src.data_sources.models.company import Company

class CompanyDataSource(ABC):
    """Simple interface that all company data sources must implement."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the data source (e.g., 'NASDAQ', 'Yahoo Finance')."""
        pass
    
    @abstractmethod
    def get_companies(self) -> List[Company]:
        """
        Get companies from this data source.
        
        Returns:
            List of Company objects
        """
        pass
    
    def is_available(self) -> bool:
        """Check if the data source is working. Override if needed."""
        return True
```

### Example Implementation

```python
class YahooFinanceSource(CompanyDataSource):
    """Yahoo Finance company data source."""
    
    @property
    def name(self) -> str:
        return "Yahoo Finance"
    
    def get_companies(self) -> List[Company]:
        """Get companies from Yahoo Finance API."""
        # Implementation here
        companies = []
        # ... fetch from Yahoo Finance
        return companies

class YahooFinanceSource(CompanyDataSource):
    """Yahoo Finance company data source (example for future extension)."""
    
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
    
    @property
    def name(self) -> str:
        return "Yahoo Finance API"
    
    def get_companies(self) -> List[Company]:
        """Get companies from Yahoo Finance API."""
        # Implementation here
        companies = []
        # ... fetch from Yahoo Finance API
        return companies
```

## Simple Ingestion Pipeline

### The Main Pipeline Class

```python
import logging
from typing import List, Optional, Dict
from src.data_sources.models.company import Company
from src.repos.equities.companies.company_repository import CompanyRepository

class SimpleCompanyPipeline:
    """Simple company ingestion pipeline."""
    
    def __init__(self):
        self.company_repo = CompanyRepository()
        self.logger = logging.getLogger(__name__)
    
    def run_ingestion(self, sources: List[CompanyDataSource]) -> Dict[str, int]:
        """
        Run ingestion from the given data sources.
        
        Args:
            sources: List of data sources to get companies from
            
        Returns:
            Dictionary with results: {"inserted": 5, "updated": 3, "skipped": 2}
        """
        results = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
        all_companies = []
        
        # Step 1: Get companies from all sources
        for source in sources:
            try:
                if not source.is_available():
                    self.logger.warning(f"Source {source.name} is not available")
                    continue
                
                self.logger.info(f"Getting companies from {source.name}")
                companies = source.get_companies()
                
                # Add source info to each company
                for company in companies:
                    company.data_source = source.name
                
                all_companies.extend(companies)
                self.logger.info(f"Got {len(companies)} companies from {source.name}")
                
            except Exception as e:
                self.logger.error(f"Error getting companies from {source.name}: {e}")
                results["errors"] += 1
        
        # Step 2: Clean and validate data
        clean_companies = self._clean_companies(all_companies)
        
        # Step 3: Save to database
        sync_results = self._sync_to_database(clean_companies)
        results.update(sync_results)
        
        return results
    
    def _clean_companies(self, companies: List[Company]) -> List[Company]:
        """Basic data cleaning - remove duplicates and invalid companies."""
        clean_companies = []
        seen_tickers = set()
        
        for company in companies:
            # Skip if no ticker
            if not company.ticker or not company.ticker.symbol:
                continue
            
            ticker = company.ticker.symbol.upper()
            
            # Skip duplicates (keep first occurrence)
            if ticker in seen_tickers:
                continue
            
            seen_tickers.add(ticker)
            
            # Basic cleaning
            if company.company_name:
                company.company_name = company.company_name.strip()
            if company.exchange:
                company.exchange = company.exchange.upper()
            
            clean_companies.append(company)
        
        self.logger.info(f"Cleaned data: {len(clean_companies)} companies after removing duplicates")
        return clean_companies
    
    def _sync_to_database(self, companies: List[Company]) -> Dict[str, int]:
        """Save companies to database."""
        results = {"inserted": 0, "updated": 0, "skipped": 0}
        
        existing_symbols = self.company_repo.get_active_company_symbols()
        
        for company in companies:
            ticker_symbol = company.ticker.symbol
            
            try:
                if ticker_symbol in existing_symbols:
                    # Update existing company if data has changed
                    if self.company_repo.update_company(ticker_symbol, company):
                        results["updated"] += 1
                    else:
                        results["skipped"] += 1
                else:
                    # Insert new company
                    self.company_repo.insert(company)
                    results["inserted"] += 1
                    
            except Exception as e:
                self.logger.error(f"Error syncing company {ticker_symbol}: {e}")
        
        return results
```

## Converting NASDAQ Screener to Data Source

### Wrap Existing Code

```python
from src.data_sources.nasdaq.screener import load_screener_files_from_directory

class NasdaqScreenerSource(CompanyDataSource):
    """Convert NASDAQ screener files into a data source."""
    
    def __init__(self, screener_dir: str = None):
        self.screener_dir = screener_dir
    
    @property
    def name(self) -> str:
        return "NASDAQ Screener Files"
    
    def get_companies(self) -> List[Company]:
        """Load companies from NASDAQ screener files."""
        return load_screener_files_from_directory(self.screener_dir)
```

## How to Use It

### Simple Usage Example

```python
# Create data sources  
nasdaq_source1 = NasdaqScreenerSource("/path/to/screener/files1")
nasdaq_source2 = NasdaqScreenerSource("/path/to/screener/files2")

# Create pipeline
pipeline = SimpleCompanyPipeline()

# Run ingestion from multiple sources
results = pipeline.run_ingestion([nasdaq_source1, nasdaq_source2])

# Print results
print(f"Inserted: {results['inserted']}")
print(f"Updated: {results['updated']}")
print(f"Errors: {results['errors']}")
```

### Command Line Script

```python
# scripts/simple_ingestion.py
"""Simple company ingestion script."""

import sys
from src.ingestion.simple_pipeline import SimpleCompanyPipeline
from src.data_sources.nasdaq.screener import NasdaqScreenerSource

def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_ingestion.py <screener_dir>")
        sys.exit(1)
    
    screener_dir = sys.argv[1]
    
    # Create source and pipeline
    source = NasdaqScreenerSource(screener_dir)
    pipeline = SimpleCompanyPipeline()
    
    # Run ingestion
    try:
        results = pipeline.run_ingestion([source])
        
        print("Ingestion completed:")
        print(f"  Inserted: {results['inserted']}")
        print(f"  Updated: {results['updated']}")
        print(f"  Skipped: {results['skipped']}")
        print(f"  Errors: {results['errors']}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Implementation Plan

### Step 1: Create the Interface (30 minutes)
- [ ] Create `src/data_sources/base/company_data_source.py` with the `CompanyDataSource` interface

### Step 2: Wrap NASDAQ Screener (30 minutes)  
- [ ] Add `NasdaqScreenerSource` class to existing `src/data_sources/nasdaq/screener.py`

### Step 3: Create Simple Pipeline (1 hour)
- [ ] Create `src/ingestion/simple_pipeline.py` with the `SimpleCompanyPipeline` class

### Step 4: Create Script (15 minutes)
- [ ] Create `scripts/simple_ingestion.py` for command-line usage

### Step 5: Test It (30 minutes)
- [ ] Test with existing NASDAQ screener files
- [ ] Verify data gets inserted/updated correctly

**Total Time: ~2.5 hours**

## Future Extensions (Later)

When you want to add more sources:

1. **Yahoo Finance Source:**
   ```python
   class YahooFinanceSource(CompanyDataSource):
       def get_companies(self):
           # Call Yahoo Finance API
   ```

2. **Manual Data Source:**
   ```python  
   class ManualDataSource(CompanyDataSource):
       def get_companies(self):
           # Return manually curated company list
   ```

3. **API Source:**
   ```python
   class APISource(CompanyDataSource):
       def get_companies(self):
           # Call external API
   ```

## Benefits of This Simple Approach

✅ **Easy to understand** - Just 3 classes, clear responsibilities  
✅ **Easy to extend** - Add new sources by implementing one interface  
✅ **Reuses existing code** - Wraps current NASDAQ screener logic  
✅ **Quick to implement** - Can be done in a few hours  
✅ **Works with current database** - Uses existing repositories  

This gives you the foundation for multi-source ingestion without the complexity of the original design. You can always add more sophisticated features later if needed.