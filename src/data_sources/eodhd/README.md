# EODHD Data Sources

This module provides two data sources for retrieving US stock market data from EODHD (EOD Historical Data) API.

## Data Sources

### 1. EodhdSymbolsSource
- **File**: `symbols.py`
- **Endpoints**: `/api/exchange-symbol-list/{exchange}` and `/api/delisted-symbols`
- **Methods**: `get_active_symbols()`, `get_delisted_symbols()`
- **Data**: Active and delisted US stock symbols (code, name, exchange, country, currency, type, isin)
- **Returns**: `Company` dataclass instances

### 2. EodhdDataSource
- **File**: `eod_data.py`
- **Endpoint**: `/api/eod/{SYMBOL}.US`
- **Methods**: `get_eod_data()`, `get_latest_eod()`
- **Data**: Historical end-of-day OHLCV price data with date ranges and period selection (daily/weekly/monthly)
- **Returns**: `HistoricalEndOfDayPricing` dataclass instances
- **Requires**: `EODHD_API_KEY` environment variable

## Usage
Both sources use the EODHD API with automatic `.US` suffix handling for US stocks. See `symbols.py` and `eod_data.py` for example usage in `if __name__ == "__main__"` blocks.
