# EODHD API Review

Comprehensive overview of EODHD API endpoints and their data offerings based on official documentation.

## Historical Data APIs

### EOD
#### EOD Historical Data
**Endpoint**: `/eod/{symbol}?api_token={key}&from={date}&to={date}&period={d/w/m}&fmt={json/csv}`
**Purpose**: Retrieve end-of-day OHLCV (Open, High, Low, Close, Volume) historical data for stocks, ETFs, indices.
**Data**: Daily/weekly/monthly bars with date, open, high, low, close, adjusted_close, volume fields.
**Coverage**: US stocks from inception; non-US exchanges from Jan 3, 2000.
**Use Cases**: Backtesting strategies, historical analysis, charting, trend analysis.

#### Bulk EOD Prices
**Endpoint**: `/eod-bulk-get-prices?api_token={key}&symbol={ticker}&date_from={date}&date_to={date}&fmt={json/csv}`
**Purpose**: Batch download large volumes of historical EOD data efficiently.
**Data**: Same OHLCV fields as standard EOD endpoint but optimized for bulk retrieval.
**Coverage**: Multiple symbols or entire exchanges in single request.
**Use Cases**: Database population, large-scale backtesting, data warehouse updates.

##### End Of Day Historical Prices Update Time
We update each stock exchange 2-3 hours after the market closes. But except for major US exchanges (NYSE, NASDAQ), these exchanges are updated next 15 minutes after the market closes. However US mutual funds, PINK, OTCBB, and some indices do update only the next morning, the update starts at 3-4 am EST and usually ends at 5-6 am EST. For these types of symbols, we always get ‘updated price’ up to 3-4 am.


### 2. Intraday Historical Data
**Endpoint**: `/intraday-bulk-get-prices?api_token={key}&symbol={ticker}&interval={1m/5m/15m/30m/1h}&date_from={date}&fmt={json/csv}`
**Purpose**: Access minute-level granular price data for intraday trading analysis.
**Data**: Timestamp, open, high, low, close, volume for each interval (1min, 5min, 15min, 30min, 1hour).
**Coverage**: Limited historical depth depending on subscription tier.
**Use Cases**: Day trading algorithms, intraday pattern analysis, volatility studies.

### 3. Yahoo Finance Compatible
**Endpoint**: `/table.csv?s={symbol}&a={from_month}&b={from_day}&c={from_year}&d={to_month}&e={to_day}&f={to_year}&g={period}&api_token={key}&fmt=json`
**Purpose**: Provide backward compatibility for systems migrating from deprecated Yahoo Finance API.
**Data**: Historical OHLCV data formatted exactly like old Yahoo Finance responses (months 0-indexed).
**Coverage**: Same as standard EOD endpoint but with Yahoo-style parameter naming.
**Use Cases**: Legacy system migration, drop-in Yahoo Finance API replacement.

### Delisted Stock Historical Data
**Endpoint**: Two-step process: 1) `/exchange-symbol-list/{EXCHANGE}?api_token={key}&delisted=1` then 2) `/eod/{TICKER}?api_token={key}`
**Purpose**: Access historical price data for companies no longer trading to avoid survivorship bias in backtesting.
**Data**: Full OHLCV historical data using standard EOD endpoint after identifying delisted tickers.
**Coverage**: 26,000+ US stock tickers (mostly from Jan 2000); 42,000+ non-US tickers (mostly within latest 6-7 years).
**Use Cases**: Survivorship bias-free backtesting, delisting studies, comprehensive historical analysis.

## Corporate Actions APIs

### Splits API
**Endpoint**: `/splits/{SYMBOL}.{EXCHANGE}?api_token={key}&from={date}&to={date}&fmt={json/csv}`
**Purpose**: Retrieve historical stock split data for a given symbol.
**Data**: Split date, split ratio (old_shares to new_shares), optionability status.
**Coverage**: Free plan: 1 year; Paid plans: 30+ years of split history.
**Use Cases**: Adjusting historical prices, corporate action tracking, reconciliation.

### Dividends API
**Endpoint**: `/div/{SYMBOL}.{EXCHANGE}?api_token={key}&from={date}&to={date}&fmt={json/csv}`
**Purpose**: Retrieve historical dividend payments for a given symbol.
**Data**: Ex-dividend date, value, unadjusted value, currency. Enhanced data for major US tickers: declaration date, record date, payment date.
**Coverage**: Free plan: 1 year; Paid plans: 30+ years. Major exchanges: NYSE, NASDAQ, AMEX, European markets.
**Use Cases**: Dividend yield analysis, income investing, total return calculations.

## Real-Time Data APIs

### Live OHLCV Stock Prices API
**Endpoint**: `/real-time/{TICKER}?api_token={key}&s={additional_tickers}&fmt={json/csv}`
**Purpose**: Get live (delayed 15-20 min) OHLCV data with bid/ask, volume, and market metrics for stocks, forex, and crypto.
**Data**: Open, high, low, close, volume, timestamp, previous_close, change, change_percent, bid/ask with sizes, 52-week range, market cap.
**Coverage**: Nearly all global stocks, 1,100+ forex pairs, digital currencies, ETFs, mutual funds.
**Update Frequency**: Stocks update every 1 minute with 15-20 min delay; Forex ~1 min delay.
**Use Cases**: Quote tickers, watchlists, lightweight dashboards, trading decision support.

### 5. Live (Delayed) Stock Prices
**Endpoint**: `/live-bulk-get-prices?api_token={key}&symbols={AAPL.US,MSFT.US}&fmt={json/csv}`
**Purpose**: Get current delayed real-time prices for multiple symbols (typically 15-min delay).
**Data**: Code, exchange, timestamp, gmtoffset, open, high, low, close, volume, previous_close, change, change_percent.
**Coverage**: US and global stocks, currencies, commodities. Delay varies by exchange regulations.
**Use Cases**: Portfolio monitoring, price alerts, market dashboards, screening tools.

### 6. Real-Time WebSocket Streaming
**Endpoint**: `wss://eodhd.com/api/ws?api_token={key}` (WebSocket connection)
**Purpose**: Subscribe to streaming real-time price updates with minimal latency.
**Data**: JSON messages with code, price, change, change_percent, volume, timestamp for subscribed symbols.
**Subscription**: Send `{"action": "subscribe", "symbols": ["AAPL.US"]}` after connection.
**Use Cases**: Trading platforms, live dashboards, real-time alerts, high-frequency monitoring.

## Fundamental & News APIs

### 7. Fundamental Data
**Endpoint**: `/fundamentals?api_token={key}&symbol={ticker}&period_type={annual/quarterly}&fmt={json/csv}`
**Purpose**: Retrieve comprehensive fundamental financial data for stocks and ETFs.
**Data**: Financial statements (income, balance sheet, cash flow), ratios, earnings dates, company info, updated timestamps.
**Coverage**: Quarterly and annual reports for US and international stocks.
**Use Cases**: Value investing analysis, DCF models, financial ratios screening, earnings tracking.

### 8. Financial News Feed
**Endpoint**: `/financial-news?api_token={key}&s={symbol}&limit={count}&fmt={json/csv}`
**Purpose**: Access curated financial news articles with optional sentiment analysis.
**Data**: Title, content, publication date, link, sentiment scores (positive/negative/neutral).
**Coverage**: Global financial news; symbol-specific or general market news.
**Use Cases**: Sentiment analysis, event-driven trading, news aggregation, market monitoring.

## Calendar & Events APIs

### Earnings Calendar API
**Endpoint**: `/calendar/earnings?api_token={key}&symbols={AAPL.US,MSFT.US}&from={date}&to={date}&fmt={json/csv}`
**Purpose**: Track company earnings report dates with estimates and actuals.
**Data**: Report dates, EPS actuals/estimates, surprise percentages, before/after market timing, currency.
**Coverage**: Historical from 2018; forward-looking several months. Default window: today + 7 days.
**Use Cases**: Earnings tracking, event-driven trading, calendar planning, estimate comparison.

### Earnings Trends API
**Endpoint**: `/calendar/trends?api_token={key}&symbols={AAPL.US,MSFT.US}&fmt=json`
**Purpose**: Retrieve analyst consensus and EPS revisions over time.
**Data**: Forward/historical estimates by quarter/year, EPS revisions (7/30/60/90-day comparisons), revenue estimates, growth metrics, analyst counts.
**Coverage**: JSON-only due to nested structure. Requires symbol list parameter.
**Use Cases**: Analyst sentiment tracking, estimate revisions analysis, consensus monitoring.

### IPOs Calendar API
**Endpoint**: `/calendar/ipos?api_token={key}&from={date}&to={date}&fmt={json/csv}`
**Purpose**: Track upcoming and historical initial public offerings.
**Data**: Company names, exchanges, filing/amended dates, price ranges, offer prices, share counts, lifecycle states (Filed, Expected, Amended, Priced).
**Coverage**: January 2015 forward; 2-3 weeks into future.
**Use Cases**: IPO monitoring, new listing discovery, offering analysis.

### Economic Events Calendar API
**Endpoint**: `/economic-events?api_token={key}&from={date}&to={date}&country={ISO_CODE}&comparison={mom/qoq/yoy}&type={event_type}&fmt={json/csv}`
**Purpose**: Track macroeconomic events like retail sales, bond auctions, PMI releases.
**Data**: Event dates, countries, comparison metrics (mom/qoq/yoy), event types, values.
**Coverage**: Worldwide coverage; historical data from 2020. Supports pagination (offset/limit 0-1000).
**Use Cases**: Economic calendar tracking, macro event analysis, timing market movements.

## Symbol & Exchange APIs

### 9. Exchanges List
**Endpoint**: `/exchanges-list?api_token={key}&fmt={json/csv}`
**Purpose**: Get comprehensive list of supported exchanges worldwide with metadata.
**Data**: Exchange code, name, country, timezone information for each supported market.
**Coverage**: 70+ global exchanges including NYSE, NASDAQ, LSE, TSE, etc.
**Use Cases**: Exchange selection, timezone handling, coverage verification, symbol validation.

### 10. Active Symbol List
**Endpoint**: `/exchange-symbol-list/{EXCHANGE}?api_token={key}&delisted={0/1}&type={common_stock/etf/fund}&fmt={json/csv}`
**Purpose**: Retrieve all currently trading symbols for a specific exchange.
**Data**: Code, Name, Country, Exchange, Currency, Type (Common Stock/ETF/Preferred), ISIN.
**Coverage**: Use 'US' for all US exchanges combined, or specific codes (NYSE, NASDAQ, AMEX). Optional parameters: delisted=1 for inactive tickers, type filter for asset class.
**Use Cases**: Universe selection, symbol discovery, database initialization, screening lists.

### 11. Delisted Symbols
**Endpoint**: `/delisted-symbols?api_token={key}&fmt={json/csv}`
**Purpose**: Access historical company data for delisted/inactive securities.
**Data**: Code, Name, Exchange, Currency, Type for companies no longer trading.
**Coverage**: Worldwide delisted securities (filter by Exchange field for US: US/NYSE/NASDAQ/AMEX).
**Use Cases**: Historical backtesting with survivorship bias correction, delisting studies.

### 12. Last Close Price (Filtered)
**Endpoint**: `/eod/{symbol}?filter=last_close&api_token={key}&fmt=json`
**Purpose**: Quick endpoint to fetch only the most recent closing price for a symbol.
**Data**: Single data point with date, close price, adjusted close for latest trading day.
**Coverage**: All symbols with EOD data available; optimized for spreadsheet WEBSERVICE functions.
**Use Cases**: Excel/Google Sheets integration, quick price checks, portfolio value calculation.

### Search API
**Endpoint**: `/search/{query_string}?api_token={key}&limit={1-500}&type={stock/etf/fund/bond/index/crypto}&exchange={US/NYSE/NASDAQ}&fmt=json`
**Purpose**: Search for stocks, ETFs, mutual funds, indices by ticker, company name, or ISIN.
**Data**: Code, Exchange, Name, Type, Country, Currency, ISIN, previousClose, previousCloseDate, isPrimary.
**Coverage**: All active tickers; flexible pattern matching. Default limit: 15, max: 500. Demo API keys unsupported.
**Use Cases**: Symbol lookup, company search, ISIN resolution, ticker validation.

## Advanced Data APIs

### Technical Analysis Indicators API
**Endpoint**: `/technical/{SYMBOL}.{EXCHANGE}?api_token={key}&function={indicator}&period={2-100000}&from={date}&to={date}&fmt={json/csv}`
**Purpose**: Calculate 20+ technical indicators without custom code.
**Data**: SMA, EMA, WMA, RSI, Stochastic, MACD, Bollinger Bands, ATR, ADX, CCI, Beta, Average Volume, and more.
**Coverage**: All symbols with EOD data. Optional filters like 'last_ema' for most recent values only.
**Use Cases**: Technical analysis, backtesting strategies, signal generation, charting indicators.
**API Consumption**: 5 calls per request.

### Stock Market Screener API
**Endpoint**: `/screener?api_token={key}&filters=[["field","operation",value]]&signals={200d_new_lo/wallstreet_hi}&sort={field}&limit={1-100}&offset={0-999}`
**Purpose**: Filter and screen stocks by fundamental and technical criteria.
**Data**: Market cap, EPS, dividend yield, price changes, volume metrics, sector, industry. Supports string (=, match) and numeric (=, >, <, >=, <=) operations.
**Coverage**: Pre-calculated signals: 52-week highs/lows, book value status, analyst expectations.
**Use Cases**: Stock screening, universe filtering, investment idea generation.
**API Consumption**: 5 calls per request.

### Insider Transactions API
**Endpoint**: `/insider-transactions?api_token={key}&limit={1-1000}&from={date}&to={date}&code={AAPL.US}`
**Purpose**: Track insider buying and selling from SEC Form 4 filings.
**Data**: Transaction dates, types (P=Purchase, S=Sale), securities info, insider names.
**Coverage**: All US companies reporting Form 4 to SEC. Major symbols have 10+ years data. Default range: 1 year ago to current.
**Use Cases**: Insider sentiment analysis, ownership tracking, signal detection.
**API Consumption**: 10 calls per request.

### Macroeconomic Data API
**Endpoint**: `/macro-indicator/{COUNTRY}?api_token={key}&indicator={gdp_current_usd/real_interest_rate/inflation/etc}&fmt={json/csv}`
**Purpose**: Access 40+ macroeconomic indicators for global economies.
**Data**: GDP variants, debt, trade balances, inflation, interest rates, population, life expectancy, CO2 emissions, internet users, and more.
**Coverage**: 40 total indicators, most from December 1960 onward. Country codes: Alpha-3 ISO format (USA, FRA, DEU).
**Use Cases**: Macro analysis, country comparison, economic modeling, global trends.
**API Consumption**: 10 calls per request.

### Bulk Data API
**Endpoint**: `/eod-bulk-last-day/{EXCHANGE}?api_token={key}&date={YYYY-MM-DD}&symbols={MSFT,AAPL}&filter={extended}&type={splits/dividends}&fmt={json/csv}`
**Purpose**: Download entire exchange data or multiple symbols in single request for EOD, splits, or dividends.
**Data**: Complete daily market data for entire exchange. Extended filter adds: company name, EMA 50/200, 14/50/200-day average volumes.
**Coverage**: US exchanges (NYSE, NASDAQ, BATS, AMEX) and international. Exchange-wide downloads complete in 5-10 seconds.
**Use Cases**: Database population, exchange-wide analysis, bulk downloads.
**API Consumption**: Full exchange: 100 calls; Multi-symbol: 1 call per ticker + 100 base calls.

### US Stock Options API
**Endpoint**: Available through EODHD marketplace at `/marketplace/unicornbay/options`
**Purpose**: Access daily updated options chains with pricing and Greeks for 6,000 top-traded US stocks.
**Data**: 43 fields including bid/ask, last price, volume, open interest, Greeks (Delta, Gamma, Theta, Vega, Rho), implied volatility, moneyness, DTE.
**Coverage**: 6,000+ US stocks, 2-year historical data, 1.5M+ daily bid/ask/trade events. Parameters: symbol, exp_date, strike ranges, trade time filters.
**Use Cases**: Options trading, volatility analysis, Greeks calculation, options screening.
**Pricing**: $39.99/month standard; $29.99/month promotional (beta offer).

## Data Formats & Features

**Supported Formats**: JSON (default), CSV
**Authentication**: API token via query parameter `api_token={key}` or header
**Rate Limits**: Free tier: 20 req/day | Paid: 100k+ req/day (plan-dependent)
**Error Codes**: 200 (success), 401 (invalid key), 403 (rate limit), 404 (not found), 500 (server error)

## API Consumption Costs

| API Category | Calls Per Request |
|-------------|-------------------|
| Live OHLCV | 1 per ticker |
| EOD Historical | 1 |
| Intraday Historical | 5 |
| Dividends | 1 |
| Splits | 1 |
| Fundamental Data | 10 |
| Options Data | Varies (marketplace) |
| Calendar APIs | 1 |
| News API | 5 |
| Technical Indicators | 5 |
| Stock Screener | 5 |
| Search API | 1 |
| Exchanges API | 1 |
| Macro Indicators | 10 |
| Insider Transactions | 10 |
| Economic Events | 1 |
| Bulk EOD | 100 (full exchange) or 1/ticker + 100 |

**Daily Limit**: 100,000 requests/day (paid plans) | 20 requests/day (free plan)

## Additional APIs (Not Yet Fully Documented)

- **Tick Data API**: Granular tick-level pricing for US stocks
- **ESG Data API**: Environmental, Social, Governance metrics
- **S&P and Dow Jones Historical Constituents API**: Index composition changes over time
- **ID Mapping API**: Convert between CUSIP / ISIN / FIGI / LEI / CIK ↔ Symbol
- **40,000 Stock Market Logos API**: Company logo repository
- **List of Supported Crypto Currencies**: Available cryptocurrency symbols
- **List of Supported FOREX Currencies**: Forex pair coverage (1,100+ pairs)
- **Live v2 for US Stocks**: Extended quote information (2025 feature)
- **Bond Fundamentals API**: Fundamental data for bonds

## Integration Tools

- Python library: `eodhd` package
- Excel Add-on: `=EODHD_GET_HISTORICAL()` functions
- Google Sheets Add-on
- R library support
- FTP Alternative: EOD Data Downloader

## References

- [API Documentation](https://eodhd.com/financial-apis/)
- [Historical Data API](https://eodhd.com/financial-apis/api-for-historical-data-and-volumes/)
- [Live OHLCV API](https://eodhd.com/financial-apis/live-ohlcv-stocks-api)
- [Splits & Dividends API](https://eodhd.com/financial-apis/api-splits-dividends)
- [Delisted Companies Data](https://eodhd.com/financial-academy/financial-faq/historical-stock-prices-for-delisted-companies)
- [Exchanges API](https://eodhd.com/financial-apis/exchanges-api-list-of-tickers-and-trading-hours/)
- [Context7 EODHD Docs](https://context7.com/websites/eodhd)
