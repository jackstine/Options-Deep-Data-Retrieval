# Equities Database Tables

## Company
Core company information that persists over time.
- **Fields**: id, company_name, exchange, sector, industry, country, market_cap, description, active, source, created_at, updated_at
- **Associations**: Has many Tickers, Has many Ticker History records

## Ticker
Maps currently active ticker symbols to companies.
- **Fields**: id, symbol (unique), company_id, created_at, updated_at
- **Associations**: Belongs to Company, Has many Historical EOD Pricing records
- **Purpose**: Active symbol-to-company mapping

## Ticker History
Tracks all ticker symbols over time, including delisted ones.
- **Fields**: id, symbol, company_id, valid_from, valid_to, active, created_at, updated_at
- **Associations**: Belongs to Company
- **Purpose**: Historical symbol tracking with temporal validity

## Historical EOD Pricing
End-of-day OHLCV pricing data for tickers.
- **Fields**: id, ticker_id, date, open, high, low, close, adjusted_close, volume
- **Associations**: Belongs to Ticker
- **Constraints**: Unique (ticker_id, date)
- **Indexes**: ticker_id, date
- **Price Storage**: Prices stored as BIGINT (multiply by 10,000): $1.00 = 10,000
- **Purpose**: Historical pricing data linked to ticker symbols

## Relationships
```
Company (1) ←→ (many) Ticker
Company (1) ←→ (many) Ticker History
Ticker (1) ←→ (many) Historical EOD Pricing
```

## Delisted Symbols
Delisted companies tracked via:
- Company.active = False
- Ticker History.valid_to = delisting date
- Historical EOD Pricing remains linked via ticker_id (CASCADE on delete)

