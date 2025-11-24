# Options-Deep: Advanced Stock Analysis Platform

<div align="center">

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-%23316192.svg?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/sqlalchemy-2.0+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

*A comprehensive Python-based stock analysis platform for multi-source data ingestion, normalization, and algorithmic analysis.*

[Features](#-features) •
[Quick Start](#-quick-start) •
[Architecture](#-architecture) •
[Documentation](#-documentation) •
[Contributing](#-contributing)

</div>

---

## 🎯 Overview

Options-Deep is a modular, extensible platform designed for sophisticated stock market analysis. It provides a unified interface for ingesting data from multiple financial data sources, performing advanced transformations, and running analytical algorithms on normalized datasets.

### Key Capabilities

- **Multi-Source Data Ingestion**: Seamlessly integrate data from NASDAQ, Yahoo Finance, Alpha Vantage, and more
- **Intelligent Data Normalization**: Automatic data cleaning, validation, and standardization across sources  
- **Advanced Analytics Engine**: Built-in technical indicators, fundamental analysis, and machine learning algorithms
- **Enterprise-Grade Database**: PostgreSQL with SQLAlchemy ORM for reliable data persistence
- **Extensible Architecture**: Plugin-based design for easy addition of new data sources and algorithms

## ✨ Features

### 📈 Data Sources
- **NASDAQ Screener** - CSV import with company fundamentals
- **Yahoo Finance** - Real-time quotes and historical data  
- **Polygon.io** - Professional-grade market data
- **CSV/JSON Files** - Custom data import capabilities
- **Extensible Framework** - Add new sources with simple wrapper pattern

### 🔧 Data Processing
- **Automatic Data Validation** - Ensures data quality and consistency
- **Symbol Normalization** - Handles different ticker formats across exchanges
- **Timezone Management** - UTC normalization for global markets
- **Duplicate Detection** - Intelligent handling of overlapping data sources

### 🏗️ Database Architecture
- **Companies Table** - Core business information and fundamentals
- **Tickers Table** - Symbol mapping and metadata
- **Ticker History** - Time-series price and volume data
- **Migration System** - Alembic-powered database versioning
- **Multi-Database Support** - Separate schemas for equities and algorithms

### 🧮 Analysis Capabilities
- **Technical Indicators** - Moving averages, RSI, MACD, Bollinger Bands
- **Fundamental Analysis** - P/E ratios, market cap analysis, sector comparisons
- **Machine Learning** - Price prediction models and clustering analysis
- **Custom Algorithms** - Framework for building proprietary analysis tools

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+** with pip
- **PostgreSQL 12+** 
- **Git** for version control
- **Virtual Environment** (recommended: venv, conda, or pyenv)

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/options-deep.git
   cd options-deep
   ```

2. **Set Up Python Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate environment
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit configuration (see Configuration section below)
   nano .env
   ```

4. **Set Up Database**
   ```bash
   # Set database password environment variable
   export OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD=your_password
   
   # Run database migrations
   cd src/database/equities
   alembic upgrade head
   ```

5. **Verify Installation**
   ```bash
   # Run example company ingestion
   python examples/company_pipeline_usage.py
   
   # Sync NASDAQ screener data
   python src/cmd/nasdaq_screener_sync/main.py
   ```

### First Steps

1. **Load Sample Data**
   ```python
   from src.pipelines.companies.new_company_pipeline import CompanyPipeline
   from src.data_sources.nasdaq.screener import load_screener_file
   
   # Load companies from NASDAQ screener
   companies = load_screener_file("data/nasdaq_screener_companies.json")
   
   # Process through pipeline
   pipeline = CompanyPipeline()
   results = pipeline.process_companies(companies)
   ```

2. **Query Your Data**
   ```python
   from src.repos.equities.companies.company_repository import CompanyRepository
   from src.config.configuration import CONFIG
   
   # Get database configuration
   db_config = CONFIG.get_equities_config()
   
   # Initialize repository
   repo = CompanyRepository(db_config)
   
   # Find companies by sector
   tech_companies = repo.find_by_sector("Technology")
   print(f"Found {len(tech_companies)} technology companies")
   ```

## 🏛️ Architecture

### System Design

```
┌─────────────────┐    ┌───────────────────┐    ┌──────────────────┐
│   Data Sources  │────│   Data Pipeline   │────│    Database      │
│                 │    │                   │    │                  │
│ • NASDAQ        │    │ • Validation      │    │ • Companies      │
│ • Yahoo Finance │    │ • Normalization   │    │ • Tickers        │
│ • Polygon       │    │ • Transformation  │    │ • Price History  │
│ • CSV/JSON      │    │ • Deduplication   │    │ • Analysis       │
└─────────────────┘    └───────────────────┘    └──────────────────┘
                                  │
                       ┌───────────────────┐
                       │  Analysis Engine  │
                       │                   │
                       │ • Technical       │
                       │ • Fundamental     │
                       │ • ML Models       │
                       │ • Custom Algos    │
                       └───────────────────┘
```

### Project Structure

```
options-deep/
├── src/
│   ├── cmd/                     # Command-line applications
│   │   └── nasdaq_screener_sync/# NASDAQ data synchronization
│   ├── config/                  # Configuration management
│   │   ├── models/              # Configuration data models
│   │   └── environment_configs/ # Environment-specific settings
│   ├── data_sources/            # Data ingestion layer
│   │   ├── base/                # Abstract base classes
│   │   ├── models/              # Data models (Company, Ticker)
│   │   ├── nasdaq/              # NASDAQ data provider
│   │   └── yahoo_finance/       # Yahoo Finance integration
│   ├── database/                # Database layer
│   │   ├── equities/            # Equities database schema
│   │   │   ├── tables/          # SQLAlchemy models
│   │   │   └── migrations/      # Alembic migrations
│   │   └── algorithms/          # Algorithms database schema
│   ├── repos/                   # Repository pattern implementations
│   │   └── equities/            # Equity data repositories
│   └── pipelines/               # Data processing pipelines
├── tests/                       # Comprehensive test suite
├── data/                        # Sample data files
├── examples/                    # Usage examples
└── scripts/                     # Utility scripts
```

### Key Components

#### 🔌 Data Source Abstraction
```python
# All data sources implement common interface
class CompanyDataSource(ABC):
    @abstractmethod
    def fetch_companies(self) -> List[Company]:
        """Fetch company data from source"""
        pass
    
    @abstractmethod  
    def validate_connection(self) -> bool:
        """Test data source connectivity"""
        pass
```

#### 🗄️ Repository Pattern
```python
# Clean separation of data access logic
class CompanyRepository:
    def create_company(self, company: Company) -> Company:
        """Create new company record"""
        
    def find_by_symbol(self, symbol: str) -> Optional[Company]:
        """Find company by ticker symbol"""
        
    def find_by_sector(self, sector: str) -> List[Company]:
        """Find all companies in sector"""
```

#### ⚙️ Configuration Management
```python
# Environment-aware configuration system
from src.config.configuration import CONFIG

# Get database configuration for current environment
db_config = CONFIG.get_equities_config()

# Automatic environment detection: local, dev, prod
engine = create_engine(db_config.connection_string())
```

## 📊 Database Schema

### Core Tables

#### Companies
```sql
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(500) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    sector VARCHAR(100) INDEX,
    industry VARCHAR(200) INDEX, 
    country VARCHAR(100),
    market_cap BIGINT,
    description TEXT,
    active BOOLEAN DEFAULT TRUE INDEX,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Tickers
```sql
CREATE TABLE tickers (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE INDEX,
    company_id INTEGER REFERENCES companies(id),
    primary_ticker BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Ticker History
```sql
CREATE TABLE ticker_history (
    id SERIAL PRIMARY KEY,
    ticker_id INTEGER REFERENCES tickers(id),
    company_id INTEGER REFERENCES companies(id),
    price_date DATE NOT NULL,
    open_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    close_price DECIMAL(10,2),
    volume BIGINT,
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(ticker_id, price_date)
);
```

## ⚡ Performance & Scaling

### Database Optimizations
- **Strategic Indexing** - Optimized indexes on frequently queried columns
- **Connection Pooling** - SQLAlchemy connection pool management
- **Query Optimization** - Efficient joins and bulk operations
- **Partitioning Ready** - Architecture supports table partitioning for large datasets

### Data Processing
- **Batch Operations** - Bulk inserts for high-throughput data loading
- **Async Support** - Asynchronous data fetching capabilities
- **Memory Efficient** - Streaming processing for large datasets
- **Caching Layer** - Built-in caching for frequently accessed data

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Environment (local, dev, prod)
ENVIRONMENT=local

# Database Password
OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD=your_secure_password

# API Keys (optional)
YAHOO_FINANCE_API_KEY=your_yahoo_key
POLYGON_API_KEY=your_polygon_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# Logging
LOG_LEVEL=INFO
```

### Database Configuration

The system supports multiple environments with different database configurations:

```json
// src/config/environment_configs/local.json
{
    "databases": {
        "equities": {
            "host": "localhost",
            "port": 5432,
            "database": "options_deep_equities_local",
            "username": "e-user"
        },
        "algorithm": {
            "host": "localhost", 
            "port": 5432,
            "database": "options_deep_algorithm_local",
            "username": "e-user"
        }
    }
}
```

## 🧪 Testing

### Test Suite Structure

```
tests/
├── unit/                    # Fast, isolated unit tests
│   ├── test_data_sources/   # Data source testing
│   ├── test_models/         # Model validation tests
│   └── test_repositories/   # Repository logic tests
├── integration/             # Database integration tests
│   ├── test_pipelines/      # End-to-end pipeline tests
│   └── test_database/       # Database operation tests
└── fixtures/                # Test data and mocks
```

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test category
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only

# Run with database (requires test database setup)
pytest tests/integration/ --db
```

### Test Database Setup

```bash
# Create test database
createdb options_deep_test

# Set test environment
export ENVIRONMENT=test
export OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD=test_password

# Run migrations
cd src/database/equities
alembic upgrade head
```

## 📈 Usage Examples

### 1. Company Data Ingestion

```python
from src.data_sources.nasdaq.screener import load_screener_file
from src.pipelines.companies.new_company_pipeline import CompanyPipeline
from src.config.configuration import CONFIG

# Load NASDAQ screener data
companies = load_screener_file("data/nasdaq_screener_8_3_2025.csv")

# Process through pipeline
db_config = CONFIG.get_equities_config() 
pipeline = CompanyPipeline(db_config)

# Batch process companies
results = pipeline.process_companies(companies)
print(f"Processed {len(results.successful)} companies successfully")
```

### 2. Querying Company Data

```python
from src.repos.equities.companies.company_repository import CompanyRepository

# Initialize repository
repo = CompanyRepository(CONFIG.get_equities_config())

# Find companies by criteria
apple = repo.find_by_symbol("AAPL")
tech_companies = repo.find_by_sector("Technology")
large_caps = repo.find_by_market_cap_range(10_000_000_000, None)

# Get company statistics
stats = repo.get_sector_statistics()
print(f"Technology sector has {stats['Technology']['count']} companies")
```

### 3. Multi-Source Data Integration

```python
from src.data_sources.factory import DataSourceFactory

# Create different data source providers
nasdaq_source = DataSourceFactory.create("nasdaq_screener", 
                                         file_path="data/screener.csv")
yahoo_source = DataSourceFactory.create("yahoo_finance",
                                       api_key="your_key")

# Fetch and merge data
nasdaq_data = nasdaq_source.fetch_companies()
yahoo_data = yahoo_source.fetch_historical_prices(["AAPL", "GOOGL"])

# Process through unified pipeline
pipeline.merge_and_process([nasdaq_data, yahoo_data])
```

### 4. Custom Analysis Pipeline

```python
from src.algorithms.technical.moving_averages import SMACalculator
from src.algorithms.fundamental.valuation import PERatioAnalyzer

# Create analysis pipeline
sma_calc = SMACalculator(period=20)
pe_analyzer = PERatioAnalyzer()

# Run analysis on company data
for company in tech_companies:
    # Technical analysis
    price_data = repo.get_price_history(company.ticker.symbol)
    sma_result = sma_calc.calculate(price_data)
    
    # Fundamental analysis
    pe_result = pe_analyzer.analyze(company)
    
    # Store results
    results_repo.save_analysis_result({
        'company_id': company.id,
        'sma_20': sma_result.current_value,
        'pe_ratio': pe_result.pe_ratio,
        'analysis_date': datetime.now()
    })
```

## 🛠️ Development

### Setting Up Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run code formatting
black src/ tests/
isort src/ tests/

# Run type checking
mypy src/

# Run linting
flake8 src/ tests/
```

### Code Standards

- **Type Annotations**: Mandatory for all functions and variables
- **Docstrings**: Google-style docstrings for all public functions
- **Error Handling**: Comprehensive exception handling with custom exception types
- **Testing**: Minimum 90% code coverage required
- **Formatting**: Black code formatter with 88-character line limit

### Contributing Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Implement** your changes with tests
4. **Run** the full test suite (`pytest`)
5. **Commit** your changes (`git commit -m 'Add amazing feature'`)
6. **Push** to the branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

### Database Migrations

```bash
# Create new migration
cd src/database/equities
alembic revision --autogenerate -m "Description of changes"

# Review generated migration file
# Edit migration file if needed

# Apply migration
alembic upgrade head

# Rollback migration (if needed)
alembic downgrade -1
```

## 📚 Documentation

### Additional Resources

- **[Developer Guide](DEVELOPER.md)** - Detailed development setup and guidelines
- **[Project Plan](PROJECT_PLAN.md)** - High-level project architecture and roadmap
- **[Database Setup](src/database/database-setup.md)** - Database configuration guide
- **[API Documentation](docs/api/)** - Generated API documentation
- **[Algorithm Guide](docs/algorithms.md)** - Analysis algorithm documentation

### API Documentation

Generate API documentation:

```bash
# Install documentation dependencies
pip install sphinx sphinx-autodoc-typehints

# Generate docs
cd docs/
make html

# View documentation
open _build/html/index.html
```

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Problems
```bash
# Check PostgreSQL is running
pg_ctl status

# Verify database exists
psql -l | grep options_deep

# Test connection
psql -h localhost -U e-user -d options_deep_equities_local
```

#### Environment Configuration Issues
```bash
# Verify environment variables
echo $ENVIRONMENT
echo $OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD

# Check configuration file exists
ls src/config/environment_configs/$ENVIRONMENT.json

# Validate JSON configuration
python -c "import json; print(json.load(open('src/config/environment_configs/local.json')))"
```

#### Data Import Problems
```bash
# Check data file format
head -5 data/nasdaq_screener_companies.json

# Validate data structure
python -c "
from src.data_sources.nasdaq.screener import load_screener_file
companies = load_screener_file('your_file.csv')
print(f'Loaded {len(companies)} companies')
"
```

## 🔮 Roadmap

### Phase 1: Core Infrastructure ✅
- [x] Multi-source data ingestion framework
- [x] Database schema and migrations  
- [x] Configuration management system
- [x] Repository pattern implementation

### Phase 2: Advanced Analytics 🚧
- [ ] Technical indicator library
- [ ] Fundamental analysis algorithms
- [ ] Machine learning price prediction models
- [ ] Real-time data streaming support

### Phase 3: API & Web Interface 📋
- [ ] REST API development
- [ ] Web dashboard for data visualization
- [ ] Authentication and user management
- [ ] Portfolio tracking capabilities

### Phase 4: Performance & Scale 📋
- [ ] Data pipeline optimization
- [ ] Caching layer implementation
- [ ] Horizontal scaling support
- [ ] Advanced monitoring and alerting

## 🤝 Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, improving documentation, or sharing ideas, your input is valuable.

### Ways to Contribute

- **🐛 Bug Reports** - Found an issue? Open a detailed bug report
- **💡 Feature Requests** - Have an idea? We'd love to hear it
- **📝 Documentation** - Help improve our docs and examples  
- **🔧 Code Contributions** - Submit pull requests for fixes and features
- **🧪 Testing** - Help expand our test coverage
- **📊 Data Sources** - Add support for new financial data providers

### Development Setup

See our [Developer Guide](DEVELOPER.md) for detailed setup instructions and coding standards.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💬 Support

- **Documentation**: Start with this README and [Developer Guide](DEVELOPER.md)
- **Issues**: Open an issue on GitHub for bugs and feature requests  
- **Discussions**: Use GitHub Discussions for questions and general discussion
- **Email**: Contact the maintainers at [your-email@domain.com]

---

<div align="center">

**Built with ❤️ for the financial analysis community**

[⭐ Star this repo](https://github.com/your-username/options-deep) if you find it helpful!

</div>