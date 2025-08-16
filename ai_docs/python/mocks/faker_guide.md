# Faker Usage Guide for Options-Deep

## Core Concepts

Faker is a Python library that generates realistic fake data for testing. It's perfect for creating diverse, realistic test data for your Options-Deep stock analysis platform without using real company data.

### Installation
```bash
pip install Faker
```

### Key Features
- **Realistic data**: Generates authentic-looking names, addresses, numbers
- **Localization**: Support for multiple countries and languages
- **Consistency**: Seeded random generation for reproducible tests
- **Extensibility**: Custom providers for domain-specific data

## Basic Faker Setup for Options-Deep

### 1. Simple Data Generation

```python
from faker import Faker

# Create Faker instance
fake = Faker()

# Generate basic data
print(fake.company())           # "Anderson, Roberts and Miller"
print(fake.random_number(digits=10))  # 4839572018
print(fake.date_this_year())    # 2025-03-15
print(fake.country())           # "United States"

# Generate financial-style data
print(fake.currency_code())     # "USD"
print(fake.pydecimal(left_digits=3, right_digits=2, positive=True))  # 145.67
```

### 2. Seeded Data for Consistent Testing

```python
# Create reproducible fake data
fake_seeded = Faker()
Faker.seed(12345)  # Same seed = same data every time

# These will always generate the same values
company_name = fake_seeded.company()      # Always the same company name
stock_price = fake_seeded.pyfloat(left_digits=3, right_digits=2, positive=True)
```

## Generating Stock Market Data

### Example: Realistic Company Information

```python
from faker import Faker
from faker.providers import BaseProvider
import random

fake = Faker('en_US')  # US locale for American companies

def generate_company_data():
    """Generate realistic company data for testing."""
    return {
        'company_name': fake.company(),
        'exchange': fake.random_element(['NASDAQ', 'NYSE', 'AMEX']),
        'sector': fake.random_element([
            'Technology', 'Healthcare', 'Financial', 'Consumer Discretionary',
            'Consumer Staples', 'Energy', 'Industrials', 'Materials',
            'Real Estate', 'Communication Services', 'Utilities'
        ]),
        'industry': fake.bs().title(),  # Business speak for industry names
        'country': 'United States',
        'market_cap': fake.random_int(min=1_000_000_000, max=3_000_000_000_000),
        'description': fake.text(max_nb_chars=500),
        'founded_year': fake.random_int(min=1900, max=2020),
        'employees': fake.random_int(min=50, max=500_000)
    }

# Generate sample companies
for _ in range(5):
    company = generate_company_data()
    print(f"{company['company_name']} - {company['sector']} - ${company['market_cap']:,}")
```

### Example: Stock Ticker Generation

```python
def generate_stock_ticker():
    """Generate realistic stock ticker symbols."""
    # Most tickers are 1-5 characters
    length = fake.random_element([3, 4, 4, 4, 5])  # Weighted toward 4 characters
    
    # Generate ticker with realistic letter combinations
    ticker = ''.join(fake.random_choices(
        elements=['A','B','C','D','E','F','G','H','I','J','K','L','M',
                 'N','O','P','Q','R','S','T','U','V','W','X','Y','Z'],
        length=length
    ))
    return ticker

# Generate realistic tickers
tickers = [generate_stock_ticker() for _ in range(10)]
print("Generated tickers:", tickers)
# Example output: ['ABCD', 'WXYZ', 'TECH', 'FINX', 'HEAL']
```

## Creating Custom Providers for Financial Data

### Example: Stock Market Provider

```python
from faker.providers import BaseProvider

class StockMarketProvider(BaseProvider):
    """Custom Faker provider for stock market data."""
    
    # Define realistic company sectors
    sectors = [
        'Technology', 'Healthcare', 'Financial Services', 'Consumer Discretionary',
        'Consumer Staples', 'Energy', 'Industrials', 'Materials',
        'Real Estate', 'Communication Services', 'Utilities'
    ]
    
    # Common ticker suffixes
    ticker_suffixes = ['', '.A', '.B', '-WT', '-RT']
    
    # Exchange list
    exchanges = ['NASDAQ', 'NYSE', 'AMEX', 'OTC']
    
    def stock_ticker(self):
        """Generate realistic stock ticker."""
        base_length = self.random_element([2, 3, 4, 4, 4, 5])  # Weighted toward 4
        base_ticker = ''.join(self.random_choices(
            elements='ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            length=base_length
        ))
        suffix = self.random_element(self.ticker_suffixes)
        return base_ticker + suffix
    
    def stock_sector(self):
        """Generate stock sector."""
        return self.random_element(self.sectors)
    
    def stock_exchange(self):
        """Generate stock exchange."""
        return self.random_element(self.exchanges)
    
    def market_cap(self):
        """Generate realistic market cap."""
        # Market caps range from millions to trillions
        size_category = self.random_element(['micro', 'small', 'mid', 'large', 'mega'])
        
        if size_category == 'micro':
            return self.random_int(50_000_000, 300_000_000)
        elif size_category == 'small':
            return self.random_int(300_000_000, 2_000_000_000)
        elif size_category == 'mid':
            return self.random_int(2_000_000_000, 10_000_000_000)
        elif size_category == 'large':
            return self.random_int(10_000_000_000, 200_000_000_000)
        else:  # mega
            return self.random_int(200_000_000_000, 3_000_000_000_000)
    
    def stock_price(self):
        """Generate realistic stock price."""
        price_range = self.random_element(['penny', 'low', 'medium', 'high', 'premium'])
        
        if price_range == 'penny':
            return round(self.pyfloat(left_digits=0, right_digits=2, positive=True, min_value=0.01, max_value=5.0), 2)
        elif price_range == 'low':
            return round(self.pyfloat(left_digits=1, right_digits=2, positive=True, min_value=5.0, max_value=50.0), 2)
        elif price_range == 'medium':
            return round(self.pyfloat(left_digits=2, right_digits=2, positive=True, min_value=50.0, max_value=500.0), 2)
        elif price_range == 'high':
            return round(self.pyfloat(left_digits=3, right_digits=2, positive=True, min_value=500.0, max_value=2000.0), 2)
        else:  # premium
            return round(self.pyfloat(left_digits=4, right_digits=2, positive=True, min_value=2000.0, max_value=50000.0), 2)

# Register the custom provider
fake = Faker()
fake.add_provider(StockMarketProvider)

# Use custom providers
def generate_realistic_stock():
    return {
        'symbol': fake.stock_ticker(),
        'company_name': fake.company(),
        'sector': fake.stock_sector(), 
        'exchange': fake.stock_exchange(),
        'market_cap': fake.market_cap(),
        'current_price': fake.stock_price(),
        'country': fake.country()
    }

# Generate sample stocks
stocks = [generate_realistic_stock() for _ in range(5)]
for stock in stocks:
    print(f"{stock['symbol']}: {stock['company_name']} - ${stock['current_price']} (${stock['market_cap']:,} market cap)")
```

## Integration with Options-Deep Models

### Example: Generate Test Data for Company Model

```python
from faker import Faker
from src.data_sources.models.company import Company
from src.data_sources.models.ticker import Ticker

fake = Faker()
fake.add_provider(StockMarketProvider)

def create_fake_company():
    """Create a Company model with realistic fake data."""
    
    # Generate ticker first
    ticker_symbol = fake.stock_ticker()
    ticker = Ticker(
        symbol=ticker_symbol,
        company_id=None  # Will be set when company is created
    )
    
    # Generate company
    company = Company(
        id=None,
        ticker=ticker,
        company_name=fake.company(),
        exchange=fake.stock_exchange(),
        sector=fake.stock_sector(),
        industry=fake.bs().title(),
        country=fake.country(),
        market_cap=fake.market_cap(),
        description=fake.text(max_nb_chars=500),
        source="FAKER_TEST"
    )
    
    return company

# Create test companies
test_companies = [create_fake_company() for _ in range(10)]

for company in test_companies[:3]:
    print(f"{company.ticker.symbol}: {company.company_name}")
    print(f"  Sector: {company.sector}")
    print(f"  Market Cap: ${company.market_cap:,}")
    print(f"  Exchange: {company.exchange}")
    print("---")
```

## Time-Based Data Generation

### Example: Historical Price Data

```python
from datetime import datetime, timedelta
import random

def generate_price_history(symbol, days=30):
    """Generate realistic historical price data."""
    
    fake = Faker()
    
    # Start with a base price
    base_price = fake.stock_price()
    
    price_history = []
    current_date = fake.date_between(start_date='-1y', end_date='today')
    
    for day in range(days):
        # Generate price with some volatility
        daily_change = random.uniform(-0.05, 0.05)  # ±5% daily change
        new_price = base_price * (1 + daily_change)
        
        # Generate OHLC data
        open_price = base_price * random.uniform(0.995, 1.005)
        high_price = max(open_price, new_price) * random.uniform(1.0, 1.02)
        low_price = min(open_price, new_price) * random.uniform(0.98, 1.0)
        close_price = new_price
        
        # Generate volume
        volume = fake.random_int(min=100_000, max=50_000_000)
        
        price_data = {
            'symbol': symbol,
            'date': current_date + timedelta(days=day),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        }
        
        price_history.append(price_data)
        base_price = new_price  # Use new price as base for next day
    
    return price_history

# Generate price history for a stock
aapl_history = generate_price_history("AAPL", days=7)
for day in aapl_history:
    print(f"{day['date']}: O${day['open']} H${day['high']} L${day['low']} C${day['close']} V{day['volume']:,}")
```

## Localization for International Markets

### Example: International Company Data

```python
# Different locales for international companies
locales = ['en_US', 'en_GB', 'de_DE', 'fr_FR', 'ja_JP', 'zh_CN']

def generate_international_company(locale='en_US'):
    """Generate company data for different regions."""
    
    fake_local = Faker(locale)
    
    # Map locales to typical exchanges
    locale_exchanges = {
        'en_US': ['NASDAQ', 'NYSE', 'AMEX'],
        'en_GB': ['LSE', 'AIM'],
        'de_DE': ['XETRA', 'Frankfurt'],
        'fr_FR': ['Euronext Paris'],
        'ja_JP': ['TSE', 'Nikkei'],
        'zh_CN': ['SSE', 'SZSE']
    }
    
    # Currency codes by locale
    locale_currencies = {
        'en_US': 'USD', 'en_GB': 'GBP', 'de_DE': 'EUR',
        'fr_FR': 'EUR', 'ja_JP': 'JPY', 'zh_CN': 'CNY'
    }
    
    company_data = {
        'company_name': fake_local.company(),
        'country': fake_local.country(),
        'exchange': fake_local.random_element(locale_exchanges.get(locale, ['UNKNOWN'])),
        'currency': locale_currencies.get(locale, 'USD'),
        'sector': fake_local.random_element([
            'Technology', 'Healthcare', 'Financial', 'Manufacturing',
            'Retail', 'Energy', 'Telecommunications'
        ]),
        'headquarters_city': fake_local.city(),
        'founded_year': fake_local.random_int(min=1850, max=2020),
        'market_cap_local': fake.market_cap()  # In local currency
    }
    
    return company_data

# Generate companies from different regions
print("International Companies:")
for locale in ['en_US', 'en_GB', 'de_DE', 'ja_JP']:
    company = generate_international_company(locale)
    print(f"{company['country']}: {company['company_name']} ({company['exchange']}) - {company['currency']}")
```

## Integration with Testing Frameworks

### Example: pytest Integration

```python
import pytest
from faker import Faker

@pytest.fixture
def fake_data():
    """Provide consistent fake data across tests."""
    fake = Faker()
    Faker.seed(12345)  # Consistent data for testing
    fake.add_provider(StockMarketProvider)
    return fake

@pytest.fixture
def sample_companies(fake_data):
    """Generate sample companies for testing."""
    companies = []
    for _ in range(5):
        company = create_fake_company()
        companies.append(company)
    return companies

def test_company_processing(sample_companies):
    """Test processing multiple companies."""
    assert len(sample_companies) == 5
    
    for company in sample_companies:
        assert company.company_name is not None
        assert company.ticker.symbol is not None
        assert company.market_cap > 0

def test_nasdaq_screener_simulation(fake_data):
    """Test with NASDAQ-style data."""
    
    nasdaq_companies = []
    for _ in range(50):
        company = {
            'Symbol': fake_data.stock_ticker(),
            'Name': fake_data.company(),
            'Sector': fake_data.stock_sector(),
            'Market Cap': str(fake_data.market_cap()),
            'Country': 'United States',
            'Industry': fake_data.bs().title()
        }
        nasdaq_companies.append(company)
    
    # Test your NASDAQ processing code
    assert len(nasdaq_companies) == 50
    assert all(comp['Country'] == 'United States' for comp in nasdaq_companies)
```

## Performance and Memory Considerations

### Example: Efficient Data Generation

```python
def generate_bulk_test_data(count=1000):
    """Generate large amounts of test data efficiently."""
    
    fake = Faker()
    fake.add_provider(StockMarketProvider)
    
    # Pre-generate some common data to reuse
    sectors = [fake.stock_sector() for _ in range(20)]
    exchanges = ['NASDAQ', 'NYSE', 'AMEX']
    countries = ['United States', 'Canada', 'United Kingdom']
    
    companies = []
    
    for i in range(count):
        # Use pre-generated data to improve performance
        company = {
            'id': i + 1,
            'symbol': fake.stock_ticker(),
            'company_name': fake.company(),
            'sector': fake.random_element(sectors),
            'exchange': fake.random_element(exchanges),
            'country': fake.random_element(countries),
            'market_cap': fake.market_cap(),
            'current_price': fake.stock_price()
        }
        companies.append(company)
        
        # Optional: Show progress for large datasets
        if i % 100 == 0:
            print(f"Generated {i}/{count} companies...")
    
    return companies

# Generate large dataset
large_dataset = generate_bulk_test_data(1000)
print(f"Generated {len(large_dataset)} companies")
```

## Best Practices for Options-Deep

### 1. Consistent Data with Seeds

```python
# Good: Reproducible test data
Faker.seed(12345)
fake = Faker()
test_companies = [create_fake_company() for _ in range(10)]
# Will generate same companies every test run

# Avoid: Random data that changes every run
# fake = Faker()  # No seed - data changes every time
```

### 2. Domain-Specific Providers

```python
# Create providers specific to your domain
class NASDAQProvider(BaseProvider):
    nasdaq_sectors = [
        'Technology', 'Healthcare', 'Financial Services',
        'Consumer Discretionary', 'Consumer Staples'
    ]
    
    def nasdaq_sector(self):
        return self.random_element(self.nasdaq_sectors)
    
    def nasdaq_ticker(self):
        # NASDAQ tickers are typically 4-5 characters
        return ''.join(self.random_choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', length=4))
```

### 3. Realistic Relationships

```python
def create_company_with_history():
    """Create company with related price history."""
    fake = Faker()
    fake.add_provider(StockMarketProvider)
    
    # Create company
    company = create_fake_company()
    
    # Create related price history
    price_history = generate_price_history(
        company.ticker.symbol,
        days=fake.random_int(min=30, max=365)
    )
    
    return {
        'company': company,
        'price_history': price_history
    }
```

## When to Use Faker in Options-Deep

✅ **Use For:**
- Generating realistic test data
- Creating varied datasets for testing
- Simulating different market conditions
- Performance testing with large datasets
- International market simulation

✅ **Benefits:**
- More realistic than static test data
- Consistent results with seeding
- Localization support for global markets
- Extensible with custom providers
- Integrates well with other testing tools

❌ **Avoid For:**
- Tests requiring exact, specific values
- Testing edge cases with extreme values
- Production data (use only for testing)
- When you need guaranteed unique values across runs

## Running Tests with Faker

```bash
# Install Faker
pip install Faker

# Run tests with consistent data
FAKER_SEED=12345 pytest tests/ -v

# Generate test data files
python scripts/generate_test_data.py --count 1000 --output test_companies.json

# Run performance tests with large datasets
pytest tests/performance/ -v -s
```

This guide shows you how to use Faker to generate realistic, varied test data for your Options-Deep project, making your tests more robust and closer to real-world scenarios.