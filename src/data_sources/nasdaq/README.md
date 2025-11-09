# Nasdaq Data Sources

This module provides two data sources for retrieving company information from Nasdaq.

## Data Sources

### 1. NasdaqCompanySource (API-based)
- **File**: `company.py`
- **Endpoint**: `https://data.nasdaq.com/api/v3/datatables/QUOTEMEDIA/TICKERS?api_key={api_key}&qopts.export=true`
- **Data**: Company listings (ticker, company_name, exchange)
- **Format**: Downloads ZIP file containing CSV from Nasdaq API
- **Requires**: `NASDAQ_API_KEY` environment variable

### 2. NasdaqScreenerSource (CSV file loader)
- **File**: `screener.py`
- **Endpoint**: `https://www.nasdaq.com/market-activity/stocks/screener` download using the `Download CSV` link
- **Source**: Local CSV files from nasdaq.com screener (manual download)
- **Data**: Symbol, Name, Market Cap, Country, Sector, Industry
- **Location**: `data/data_screener/nasdaq_screener_*.csv`
- **Format**: CSV files with naming pattern `nasdaq_screener_MONTH_DAY_YEAR.csv`

## Usage
Both sources implement the `CompanyDataSource` interface and return `Company` objects. See `company.py` and `screener.py` for example usage in `if __name__ == "__main__"` blocks.
