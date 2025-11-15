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

## Rate Limits
Free: 20 req/day | Paid: 100k+ req/day. Status codes: 200 (success), 401 (invalid key), 403 (rate limit)

## References
- [API Docs](https://eodhd.com/financial-apis/) | [Symbols List](https://eodhd.com/financial-apis/exchanges-api-list-of-tickers-and-trading-hours/) | [Historical Data](https://eodhd.com/financial-apis/api-for-historical-data-and-volumes/)
