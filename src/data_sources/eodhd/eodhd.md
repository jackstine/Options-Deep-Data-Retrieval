# EODHD API Quick Reference

**Base URL**: `https://eodhd.com/api` | **Auth**: Set `EODHD_API_KEY` env variable | **Format**: csv

## Endpoints

**Active Symbols**: `/exchange-symbol-list/{EXCHANGE}` - Get currently trading symbols (use `US` for all US exchanges)
```bash
curl "https://eodhd.com/api/exchange-symbol-list/US?api_token=${EODHD_API_KEY}&fmt=csv"
```

**Delisted Symbols**: `/delisted-symbols` - Get inactive symbols (filter by `Exchange` field for US: `US`, `NYSE`, `NASDAQ`, `AMEX`)
```bash
curl "https://eodhd.com/api/delisted-symbols?api_token=${EODHD_API_KEY}&fmt=csv"
```

**EOD Historical**: `/eod/{SYMBOL}.US` - Get end-of-day OHLCV data (use `from`/`to` date params, `period` for d/w/m)
```bash
curl "https://eodhd.com/api/eod/AAPL.US?api_token=${EODHD_API_KEY}&fmt=csv&from=2024-01-01"
```

**Stock Splits (Individual)**: `/splits/{SYMBOL}.US` - Get historical stock splits for a ticker (use `from`/`to` date params)
```bash
curl "https://eodhd.com/api/splits/AAPL.US?api_token=${EODHD_API_KEY}&fmt=csv"
curl "https://eodhd.com/api/splits/TSLA.US?api_token=${EODHD_API_KEY}&fmt=csv&from=2020-01-01"
```
Response format: `Date,"Stock Splits"` (e.g., `2014-11-03,1398.000000/1000.000000`)

**Stock Splits (Bulk)**: `/eod-bulk-last-day/US?type=splits` - Get all splits for a specific date (use `date` param, defaults to last trading day)
```bash
curl "https://eodhd.com/api/eod-bulk-last-day/US?api_token=${EODHD_API_KEY}&type=splits&fmt=csv&date=2025-11-21"
curl "https://eodhd.com/api/eod-bulk-last-day/US?api_token=${EODHD_API_KEY}&type=splits&fmt=csv"
```
Response format: `Code,Ex,Date,Split` (e.g., `BLMZ,US,2025-11-21,1.000000/10.000000`)
Note: `symbols` parameter does NOT work for splits - you get entire exchange or use individual endpoint

## Rate Limits
Free: 20 req/day | Paid: 100k+ req/day. Status codes: 200 (success), 401 (invalid key), 403 (rate limit)

## References
- [API Docs](https://eodhd.com/financial-apis/)
- [Symbols List](https://eodhd.com/financial-apis/exchanges-api-list-of-tickers-and-trading-hours/)
- [Historical Data](https://eodhd.com/financial-apis/api-for-historical-data-and-volumes/)
- [Splits and Dividends](https://eodhd.com/financial-apis/api-splits-dividends)
- [Bulk Splits API](https://eodhd.com/financial-apis/bulk-api-eod-splits-dividends)
