# unittest.mock + Faker + Factory Boy: Ultimate Testing Integration Guide for Options-Deep

## Core Concepts

Combining all three libraries creates the most comprehensive testing approach possible:
- **unittest.mock**: Controls external dependencies and infrastructure
- **Faker**: Generates realistic, varied data content
- **Factory Boy**: Creates complex object relationships and structures

This trinity provides **complete control over your testing environment** while maintaining **maximum realism** in your test data.

### The Power of Three

🎯 **unittest.mock** = **Control** (What you interact with)
🎲 **Faker** = **Variety** (What the data looks like)  
🏭 **Factory Boy** = **Structure** (How objects relate to each other)

### When to Use This Ultimate Combination

✅ **Perfect For:**
- **Comprehensive integration testing** with realistic data but controlled environment
- **End-to-end business logic testing** with complex object relationships
- **Performance testing** with large, realistic datasets but no external dependencies
- **Scenario testing** with multiple realistic data variations and edge cases
- **Production-like testing** without production risks

## Pattern 1: The Ultimate Repository Test

### Example: Complete Company Repository Testing with All Three Libraries

```python
import unittest
from unittest.mock import MagicMock, patch, mock_open
import factory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker
from faker.providers import BaseProvider
import json
import csv
import io

from src.repos.equities.companies.company_repository import CompanyRepository
from src.database.equities.tables.company import Company
from src.database.equities.tables.ticker import Ticker

# Step 1: Custom Faker Provider for Financial Data
class StockMarketProvider(BaseProvider):
    """Enhanced provider combining market knowledge with Faker randomness."""
    
    sectors = [
        'Technology', 'Healthcare', 'Financial Services', 'Consumer Discretionary',
        'Consumer Staples', 'Energy', 'Industrials', 'Materials', 'Real Estate',
        'Communication Services', 'Utilities'
    ]
    
    exchanges = ['NASDAQ', 'NYSE', 'AMEX']
    
    # Real-world company name patterns
    tech_suffixes = ['Inc.', 'Corp.', 'LLC', 'Technologies', 'Systems', 'Solutions']
    health_suffixes = ['Pharmaceuticals', 'Biotech', 'Healthcare', 'Medical', 'Therapeutics']
    
    def realistic_company_name(self, sector=None):
        """Generate company names that match sector patterns."""
        base_name = self.generator.company()
        
        if sector == 'Technology':
            if self.random_int(0, 100) > 70:  # 30% get tech suffix
                suffix = self.random_element(self.tech_suffixes)
                return f"{base_name.replace(' Inc', '')} {suffix}"
        elif sector == 'Healthcare':
            if self.random_int(0, 100) > 60:  # 40% get health suffix  
                suffix = self.random_element(self.health_suffixes)
                return f"{base_name.replace(' Inc', '')} {suffix}"
        
        return base_name
    
    def stock_ticker(self, length=None):
        """Generate realistic stock tickers."""
        length = length or self.random_element([3, 4, 4, 4, 5])  # Weighted toward 4
        return ''.join(self.random_choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', length=length))
    
    def market_cap_by_sector(self, sector):
        """Generate realistic market caps based on sector characteristics."""
        if sector == 'Technology':
            return self.random_int(5_000_000_000, 3_000_000_000_000)  # Tech companies can be huge
        elif sector == 'Healthcare':
            return self.random_int(1_000_000_000, 500_000_000_000)   # Large but not as huge
        elif sector == 'Energy':
            return self.random_int(10_000_000_000, 800_000_000_000)  # Capital intensive
        else:
            return self.random_int(500_000_000, 200_000_000_000)     # General range

# Step 2: Factory Boy with Faker Integration
class EnhancedCompanyFactory(SQLAlchemyModelFactory):
    """Factory that combines structure with realistic Faker data."""
    
    class Meta:
        model = Company
        sqlalchemy_session = None  # We'll mock this
    
    id = factory.Sequence(lambda n: n + 1)
    
    # Use Faker with sector-aware logic
    sector = factory.Faker('random_element', elements=StockMarketProvider.sectors)
    company_name = factory.LazyAttribute(lambda obj: fake.realistic_company_name(obj.sector))
    market_cap = factory.LazyAttribute(lambda obj: fake.market_cap_by_sector(obj.sector))
    
    # Other realistic attributes
    exchange = factory.Faker('random_element', elements=StockMarketProvider.exchanges)
    industry = factory.LazyAttribute(lambda obj: f"{obj.sector} - {fake.bs().title()}")
    country = factory.Iterator(['United States', 'Canada', 'United Kingdom'])
    description = factory.Faker('text', max_nb_chars=500)
    active = factory.Faker('boolean', chance_of_getting_true=90)  # Most companies active
    source = 'TRIPLE_INTEGRATION_TEST'
    
    # Timestamps
    created_at = factory.Faker('date_time_this_year')
    updated_at = factory.LazyAttribute(lambda obj: fake.date_time_between(
        start_date=obj.created_at, end_date='now'
    ))

class EnhancedTickerFactory(SQLAlchemyModelFactory):
    """Ticker factory with realistic symbol generation."""
    
    class Meta:
        model = Ticker
        sqlalchemy_session = None
    
    id = factory.Sequence(lambda n: n + 1)
    symbol = factory.LazyFunction(lambda: fake.stock_ticker())
    company = factory.SubFactory(EnhancedCompanyFactory)
    primary_ticker = True
    created_at = factory.Faker('date_time_this_year')

# Step 3: Setup Faker with Custom Provider
fake = Faker()
fake.add_provider(StockMarketProvider)
Faker.seed(12345)  # Reproducible tests

# Step 4: The Ultimate Test Class
class UltimateCompanyRepositoryTest(unittest.TestCase):
    
    def setUp(self):
        """Initialize all three libraries consistently."""
        factory.Faker.seed(12345)  # Keep Factory Boy in sync
        
    def generate_realistic_external_api_response(self, companies):
        """Use Faker to create realistic API response content."""
        return {
            'status': 'success',
            'timestamp': fake.iso8601(),
            'total_count': len(companies),
            'companies': [
                {
                    'symbol': company.tickers[0].symbol if company.tickers else fake.stock_ticker(),
                    'name': company.company_name,
                    'sector': company.sector,
                    'market_cap': company.market_cap,
                    'last_price': float(fake.pydecimal(left_digits=3, right_digits=2, positive=True)),
                    'volume': fake.random_int(min=100_000, max=50_000_000),
                    'change_percent': float(fake.pydecimal(left_digits=1, right_digits=2, min_value=-10, max_value=10)),
                    'exchange': company.exchange,
                    'currency': fake.currency_code(),
                    'last_updated': fake.iso8601()
                }
                for company in companies
            ],
            'metadata': {
                'source': 'MockAPI',
                'rate_limit_remaining': fake.random_int(min=100, max=1000),
                'next_reset': fake.future_datetime(end_date='+1h').isoformat()
            }
        }
    
    @patch('src.external_apis.market_data_client.MarketDataClient')
    @patch('src.config.configuration.CONFIG')
    @patch('sqlalchemy.create_engine')
    @patch('sqlalchemy.orm.sessionmaker')
    def test_complete_repository_workflow(self, mock_sessionmaker, mock_create_engine, 
                                         mock_config, mock_market_client):
        """Ultimate test: realistic objects + mocked infrastructure + varied data."""
        
        # === FACTORY BOY: Generate Complex Object Relationships ===
        companies_with_tickers = EnhancedCompanyFactory.build_batch(20)
        
        # Create variety in the data using Factory Boy traits
        tech_companies = EnhancedCompanyFactory.build_batch(5, sector='Technology')
        healthcare_companies = EnhancedCompanyFactory.build_batch(3, sector='Healthcare') 
        international_companies = EnhancedCompanyFactory.build_batch(2, country='Canada')
        
        all_companies = companies_with_tickers + tech_companies + healthcare_companies + international_companies
        
        # === UNITTEST.MOCK: Control Infrastructure ===
        
        # Mock database session
        mock_session = MagicMock()
        mock_sessionmaker.return_value.return_value = mock_session
        
        # Mock configuration
        mock_db_config = MagicMock()
        mock_db_config.connection_string.return_value = "postgresql://test:test@localhost/test"
        mock_config.get_equities_config.return_value = mock_db_config
        
        # === FAKER: Generate Realistic Response Content ===
        
        # Mock external market data API with Faker-generated responses
        mock_client = MagicMock()
        mock_market_client.return_value = mock_client
        
        # Generate realistic API response using Faker
        api_response = self.generate_realistic_external_api_response(tech_companies)
        mock_client.get_market_data.return_value = api_response
        
        # === COMBINE ALL THREE: Repository Behavior Simulation ===
        
        def realistic_find_by_symbol(symbol):
            """Simulate database lookup with realistic scenarios."""
            # Use Faker to determine if company exists (80% exist, 20% are new)
            exists = fake.boolean(chance_of_getting_true=80)
            
            if exists:
                # Return a Factory Boy object matching the symbol
                matching_companies = [c for c in all_companies 
                                    if c.tickers and c.tickers[0].symbol == symbol]
                if matching_companies:
                    found_company = matching_companies[0]
                    found_company.id = fake.random_int(min=1, max=10000)
                    return found_company
            return None
        
        def realistic_create_company(company_data):
            """Simulate company creation with realistic outcomes."""
            # Use Faker to simulate occasional failures
            success_rate = 95  # 95% success rate
            if fake.boolean(chance_of_getting_true=success_rate):
                # Create successful response using Factory Boy structure
                created_company = EnhancedCompanyFactory.build(
                    id=fake.random_int(min=10001, max=20000),
                    company_name=company_data.company_name,
                    sector=company_data.sector,
                    market_cap=company_data.market_cap
                )
                return created_company
            else:
                # Simulate realistic database errors
                error_types = [
                    'Duplicate key violation',
                    'Connection timeout', 
                    'Invalid sector code',
                    'Market cap out of range'
                ]
                raise Exception(fake.random_element(error_types))
        
        # Configure mock behavior
        mock_session.query.return_value.filter.return_value.first.side_effect = realistic_find_by_symbol
        mock_session.add.return_value = None
        mock_session.commit.side_effect = realistic_create_company
        
        # === TEST THE COMPLETE WORKFLOW ===
        
        repo = CompanyRepository()
        results = {'created': [], 'updated': [], 'failed': []}
        
        # Process each company through the complete workflow
        for company in all_companies[:10]:  # Test subset for performance
            try:
                symbol = company.tickers[0].symbol if company.tickers else fake.stock_ticker()
                
                # Check if exists
                existing = repo.find_by_symbol(symbol)
                
                if existing:
                    # Update existing company
                    updated = repo.update_company(company)
                    results['updated'].append(updated)
                else:
                    # Create new company
                    created = repo.create_company(company)
                    results['created'].append(created)
                    
            except Exception as e:
                results['failed'].append({'company': company, 'error': str(e)})
        
        # === VERIFY REALISTIC OUTCOMES ===
        
        # Should have realistic distribution of outcomes
        total_processed = len(results['created']) + len(results['updated']) + len(results['failed'])
        self.assertEqual(total_processed, 10)
        
        # Most should succeed (realistic success rate)
        success_rate = (len(results['created']) + len(results['updated'])) / total_processed
        self.assertGreater(success_rate, 0.8)  # At least 80% success
        
        # Verify Factory Boy objects maintain realistic relationships
        for created_company in results['created']:
            self.assertIsInstance(created_company, Company)
            self.assertIn(created_company.sector, StockMarketProvider.sectors)
            self.assertGreater(created_company.market_cap, 0)
            
        # Verify Faker-generated API response was used
        mock_client.get_market_data.assert_called()
        
        # Verify realistic database interactions occurred
        self.assertGreater(mock_session.query.call_count, 5)  # Multiple lookups
        self.assertGreater(mock_session.add.call_count, 0)    # Some creates
```

## Pattern 2: Ultimate Data Pipeline Testing

### Example: Complete NASDAQ Screener to Database Pipeline

```python
class UltimateDataPipelineTest(unittest.TestCase):
    
    def setUp(self):
        factory.Faker.seed(54321)
        fake.seed_(54321)
    
    def generate_realistic_screener_file_with_factory_structure(self, num_companies=50):
        """Combine Factory Boy structure with Faker content generation."""
        
        # Use Factory Boy to create structured company data
        companies = EnhancedCompanyFactory.build_batch(num_companies)
        
        # Convert to CSV format using Faker for additional realistic details
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        
        # Write header
        writer.writerow([
            'Symbol', 'Name', 'Last Sale', 'Net Change', '% Change',
            'Market Cap', 'Country', 'IPO Year', 'Volume', 'Sector', 'Industry'
        ])
        
        # Write company data combining Factory Boy structure with Faker variety
        for company in companies:
            writer.writerow([
                company.tickers[0].symbol if company.tickers else fake.stock_ticker(),
                company.company_name,
                f"{fake.pydecimal(left_digits=3, right_digits=2, positive=True, min_value=1, max_value=1000):.2f}",
                f"{fake.pydecimal(left_digits=2, right_digits=2, min_value=-50, max_value=50):.2f}",
                f"{fake.pydecimal(left_digits=1, right_digits=2, min_value=-15, max_value=15):.2f}%",
                str(company.market_cap),
                company.country,
                str(fake.random_int(min=1980, max=2023)),
                str(fake.random_int(min=100_000, max=200_000_000)),
                company.sector,
                company.industry
            ])
        
        return csv_buffer.getvalue(), companies
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    @patch('builtins.open')
    @patch('src.config.configuration.CONFIG')
    @patch('src.repos.equities.companies.company_repository.CompanyRepository')
    def test_complete_screener_pipeline(self, mock_repo_class, mock_config, 
                                      mock_file, mock_glob, mock_exists):
        """Test complete pipeline from file to database with all three libraries."""
        
        # === FACTORY BOY + FAKER: Generate Realistic File Content ===
        
        csv_content, source_companies = self.generate_realistic_screener_file_with_factory_structure(25)
        
        # === UNITTEST.MOCK: Control File System and Database ===
        
        # Mock file system
        mock_exists.return_value = True
        mock_glob.return_value = [MagicMock(name='nasdaq_screener_test.csv')]
        mock_file.return_value = mock_open(read_data=csv_content).return_value
        
        # Mock configuration
        mock_db_config = MagicMock()
        mock_config.get_equities_config.return_value = mock_db_config
        
        # Mock repository with realistic behavior
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        
        # === FAKER: Generate Realistic Processing Outcomes ===
        
        def realistic_processing_outcome(company_data):
            """Use Faker to simulate realistic processing results."""
            # 85% success, 10% updates, 5% failures
            outcome = fake.random_int(1, 100)
            
            if outcome <= 85:  # Create new
                return EnhancedCompanyFactory.build(
                    id=fake.random_int(min=1, max=10000),
                    company_name=company_data.company_name,
                    sector=company_data.sector
                )
            elif outcome <= 95:  # Update existing
                existing_company = EnhancedCompanyFactory.build(
                    id=fake.random_int(min=1, max=1000),
                    company_name=company_data.company_name,
                    market_cap=company_data.market_cap * fake.pydecimal(
                        left_digits=1, right_digits=2, positive=True, 
                        min_value=0.8, max_value=1.2
                    )  # Slight variation
                )
                return existing_company
            else:  # Failure
                error_messages = [
                    f"Invalid market cap for {company_data.company_name}",
                    f"Duplicate ticker symbol: {company_data.ticker.symbol}",
                    f"Sector validation failed for {company_data.sector}",
                    "Database connection timeout"
                ]
                raise Exception(fake.random_element(error_messages))
        
        # Configure repository mock behavior
        mock_repo.find_by_symbol.side_effect = lambda symbol: (
            EnhancedCompanyFactory.build(id=fake.random_int(1, 1000))
            if fake.boolean(chance_of_getting_true=10)  # 10% already exist
            else None
        )
        
        mock_repo.create_company.side_effect = realistic_processing_outcome
        mock_repo.update_company.side_effect = realistic_processing_outcome
        
        # === TEST COMPLETE PIPELINE ===
        
        from src.data_sources.nasdaq.screener import load_screener_files_from_directory
        from src.pipelines.companies.simple_pipeline import CompanyPipeline
        
        # Load companies from mocked file
        loaded_companies = load_screener_files_from_directory("/mock/directory")
        
        # Process through pipeline
        pipeline = CompanyPipeline(mock_db_config)
        results = pipeline.process_companies(loaded_companies)
        
        # === VERIFY REALISTIC OUTCOMES ===
        
        # Should have loaded all companies from Factory Boy generation
        self.assertEqual(len(loaded_companies), 25)
        
        # All loaded companies should have Factory Boy + Faker characteristics
        for company in loaded_companies:
            self.assertIsNotNone(company.company_name)
            self.assertIn(company.sector, StockMarketProvider.sectors)
            self.assertIn(company.exchange, StockMarketProvider.exchanges)
            self.assertGreater(company.market_cap, 0)
        
        # Processing results should show realistic distribution
        total_processed = len(results.successful) + len(results.failed)
        self.assertEqual(total_processed, 25)
        
        # Most should succeed (based on our Faker probability)
        success_rate = len(results.successful) / total_processed
        self.assertGreater(success_rate, 0.8)  # Should be around 85-95%
        
        # Verify repository interactions match realistic patterns
        self.assertEqual(mock_repo.find_by_symbol.call_count, 25)  # Check each company
        self.assertGreater(mock_repo.create_company.call_count, 15)  # Most are new
```

## Pattern 3: Ultimate Error Handling and Edge Cases

### Example: Comprehensive Error Scenario Testing

```python
class UltimateErrorHandlingTest(unittest.TestCase):
    
    def setUp(self):
        factory.Faker.seed(99999)
        fake.seed_(99999)
    
    def create_error_scenario_companies(self):
        """Use Factory Boy traits with Faker variety for error scenarios."""
        
        # Define problematic company scenarios
        scenarios = {
            'invalid_market_cap': EnhancedCompanyFactory.build_batch(
                3, market_cap=fake.random_int(min=-1000000, max=0)  # Invalid negative
            ),
            'missing_sector': EnhancedCompanyFactory.build_batch(
                2, sector=None  # Missing required field
            ),
            'invalid_ticker_format': [],
            'future_ipo_date': EnhancedCompanyFactory.build_batch(
                2, created_at=fake.future_datetime(end_date='+1y')  # Future date
            ),
            'duplicate_tickers': [],
            'extreme_values': EnhancedCompanyFactory.build_batch(
                2, market_cap=fake.random_int(min=10_000_000_000_000, max=100_000_000_000_000)  # Too large
            )
        }
        
        # Create invalid ticker scenarios using Faker
        for _ in range(3):
            company = EnhancedCompanyFactory.build()
            # Override with invalid ticker
            company.tickers = [MagicMock(
                symbol=fake.random_element(['', '1234', 'TOOLONG', '!@#$'])  # Various invalid formats
            )]
            scenarios['invalid_ticker_format'].append(company)
        
        # Create duplicate ticker scenario
        duplicate_symbol = fake.stock_ticker()
        for _ in range(3):
            company = EnhancedCompanyFactory.build()
            company.tickers = [MagicMock(symbol=duplicate_symbol)]  # Same symbol
            scenarios['duplicate_tickers'].append(company)
        
        return scenarios
    
    @patch('src.validation.company_validator.CompanyValidator')
    @patch('src.repos.equities.companies.company_repository.CompanyRepository')
    def test_comprehensive_error_handling(self, mock_repo_class, mock_validator):
        """Test error handling with realistic error scenarios and responses."""
        
        # === FACTORY BOY: Create Problematic Object Structures ===
        error_scenarios = self.create_error_scenario_companies()
        
        # === UNITTEST.MOCK: Control Validation and Database Responses ===
        
        # Mock validator to simulate realistic validation failures
        mock_validator_instance = MagicMock()
        mock_validator.return_value = mock_validator_instance
        
        def realistic_validation_response(company):
            """Use Faker to generate realistic validation error messages."""
            errors = []
            
            if hasattr(company, 'market_cap') and company.market_cap <= 0:
                errors.append(f"Market cap must be positive, got {company.market_cap}")
            
            if not hasattr(company, 'sector') or not company.sector:
                errors.append("Sector is required but not provided")
            
            if hasattr(company, 'tickers') and company.tickers:
                ticker = company.tickers[0]
                if not ticker.symbol or len(ticker.symbol) < 1 or len(ticker.symbol) > 5:
                    errors.append(f"Invalid ticker format: '{ticker.symbol}'")
                if not ticker.symbol.isalpha():
                    errors.append(f"Ticker must contain only letters: '{ticker.symbol}'")
            
            return {'valid': len(errors) == 0, 'errors': errors}
        
        mock_validator_instance.validate.side_effect = realistic_validation_response
        
        # Mock repository to simulate database constraint errors
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        
        def realistic_database_error_response(company_data):
            """Use Faker to generate realistic database error responses."""
            # Simulate various database errors with realistic messages
            if fake.boolean(chance_of_getting_true=30):  # 30% chance of constraint violation
                error_types = [
                    f"Duplicate key violation: ticker '{company_data.ticker.symbol}' already exists",
                    f"Check constraint violation: market_cap must be > 0, got {company_data.market_cap}",
                    f"Foreign key violation: sector '{company_data.sector}' not found in valid_sectors",
                    "Connection timeout: database server not responding",
                    f"Data too long for column 'company_name': '{company_data.company_name}'"
                ]
                raise Exception(fake.random_element(error_types))
            
            # Successful creation
            return EnhancedCompanyFactory.build(
                id=fake.random_int(min=1, max=10000),
                company_name=company_data.company_name
            )
        
        mock_repo.create_company.side_effect = realistic_database_error_response
        
        # === FAKER: Generate Realistic Error Context ===
        
        def create_processing_context():
            """Generate realistic processing context using Faker."""
            return {
                'batch_id': fake.uuid4(),
                'processing_timestamp': fake.iso8601(),
                'source_file': fake.file_name(extension='csv'),
                'processor_version': f"{fake.random_int(1, 3)}.{fake.random_int(0, 9)}.{fake.random_int(0, 9)}",
                'environment': fake.random_element(['dev', 'staging', 'prod']),
                'user_id': fake.user_name(),
                'retry_count': fake.random_int(0, 3)
            }
        
        # === TEST COMPREHENSIVE ERROR SCENARIOS ===
        
        processing_context = create_processing_context()
        all_error_results = {}
        
        for scenario_name, companies in error_scenarios.items():
            with self.subTest(scenario=scenario_name):
                scenario_results = {'processed': [], 'validation_errors': [], 'database_errors': []}
                
                for company in companies:
                    try:
                        # Validate using mocked validator
                        validation_result = mock_validator_instance.validate(company)
                        
                        if not validation_result['valid']:
                            scenario_results['validation_errors'].append({
                                'company': company.company_name,
                                'errors': validation_result['errors'],
                                'context': processing_context
                            })
                            continue
                        
                        # Attempt database operation
                        result = mock_repo.create_company(company)
                        scenario_results['processed'].append(result)
                        
                    except Exception as db_error:
                        scenario_results['database_errors'].append({
                            'company': company.company_name,
                            'error': str(db_error),
                            'context': processing_context
                        })
                
                all_error_results[scenario_name] = scenario_results
        
        # === VERIFY REALISTIC ERROR HANDLING ===
        
        # Should have caught validation errors for problematic data
        self.assertGreater(len(all_error_results['invalid_market_cap']['validation_errors']), 0)
        self.assertGreater(len(all_error_results['missing_sector']['validation_errors']), 0)
        self.assertGreater(len(all_error_results['invalid_ticker_format']['validation_errors']), 0)
        
        # Should have some database errors due to Faker probability
        total_db_errors = sum(len(result['database_errors']) for result in all_error_results.values())
        self.assertGreater(total_db_errors, 0)
        
        # Error messages should be realistic and informative
        for scenario_results in all_error_results.values():
            for validation_error in scenario_results['validation_errors']:
                self.assertIsInstance(validation_error['errors'], list)
                self.assertGreater(len(validation_error['errors']), 0)
                # Each error message should be descriptive
                for error_msg in validation_error['errors']:
                    self.assertGreater(len(error_msg), 10)  # Meaningful message length
            
            for db_error in scenario_results['database_errors']:
                self.assertIsInstance(db_error['error'], str)
                self.assertGreater(len(db_error['error']), 10)
                # Should include processing context
                self.assertIn('batch_id', db_error['context'])
                self.assertIn('timestamp', db_error['context'])
```

## Pattern 4: Ultimate Performance and Load Testing

### Example: Large-Scale Realistic Data Processing

```python
class UltimatePerformanceTest(unittest.TestCase):
    
    def setUp(self):
        factory.Faker.seed(11111)
        fake.seed_(11111)
    
    def generate_large_realistic_dataset(self, size=1000):
        """Generate large dataset combining all three libraries efficiently."""
        
        # Use Factory Boy for consistent structure, Faker for variety
        print(f"Generating {size} realistic companies...")
        
        # Create batches to avoid memory issues
        batch_size = 100
        all_companies = []
        
        # Create different company profiles for realism
        profiles = [
            {'sector': 'Technology', 'weight': 0.25, 'min_cap': 1_000_000_000, 'max_cap': 3_000_000_000_000},
            {'sector': 'Healthcare', 'weight': 0.20, 'min_cap': 500_000_000, 'max_cap': 500_000_000_000},
            {'sector': 'Financial', 'weight': 0.15, 'min_cap': 5_000_000_000, 'max_cap': 1_000_000_000_000},
            {'sector': 'Energy', 'weight': 0.10, 'min_cap': 10_000_000_000, 'max_cap': 800_000_000_000},
            {'sector': 'Consumer Discretionary', 'weight': 0.30, 'min_cap': 100_000_000, 'max_cap': 200_000_000_000}
        ]
        
        for i in range(0, size, batch_size):
            current_batch_size = min(batch_size, size - i)
            batch_companies = []
            
            for _ in range(current_batch_size):
                # Use Faker to select profile based on realistic weights
                profile = fake.random_element(profiles)
                
                company = EnhancedCompanyFactory.build(
                    sector=profile['sector'],
                    market_cap=fake.random_int(min=profile['min_cap'], max=profile['max_cap']),
                    # Add processing metadata
                    source=f'PERFORMANCE_TEST_BATCH_{i // batch_size + 1}'
                )
                batch_companies.append(company)
            
            all_companies.extend(batch_companies)
            
            if i % 500 == 0:  # Progress reporting
                print(f"Generated {i + current_batch_size}/{size} companies...")
        
        return all_companies
    
    @patch('src.external_apis.bulk_data_client.BulkDataClient')
    @patch('src.repos.equities.companies.company_repository.CompanyRepository')
    @patch('time.sleep')  # Mock sleep to speed up retry logic
    def test_large_scale_processing_performance(self, mock_sleep, mock_repo_class, mock_bulk_client):
        """Test performance with large, realistic datasets and mocked infrastructure."""
        
        import time
        
        # === FACTORY BOY + FAKER: Generate Large Realistic Dataset ===
        
        dataset_size = 2000  # Large but manageable for testing
        start_time = time.time()
        
        large_dataset = self.generate_large_realistic_dataset(dataset_size)
        
        generation_time = time.time() - start_time
        print(f"Dataset generation: {generation_time:.2f}s for {dataset_size} companies")
        
        # === UNITTEST.MOCK: Simulate Realistic Infrastructure Performance ===
        
        # Mock bulk data client with realistic response times
        mock_client = MagicMock()
        mock_bulk_client.return_value = mock_client
        
        def realistic_bulk_api_response(company_batch):
            """Simulate realistic API response times and occasional failures."""
            batch_size = len(company_batch)
            
            # Simulate API processing time (10ms per company + base overhead)
            simulated_time = (batch_size * 0.01) + fake.pyfloat(min_value=0.1, max_value=0.5)
            
            # Simulate occasional API failures (5% chance)
            if fake.boolean(chance_of_getting_true=5):
                error_messages = [
                    f"Rate limit exceeded for batch of {batch_size} companies",
                    "Temporary service unavailable - please retry",
                    f"Request timeout after {simulated_time:.2f}s",
                    "Invalid request format - batch too large"
                ]
                raise Exception(fake.random_element(error_messages))
            
            # Generate realistic response data using Faker
            return {
                'batch_id': fake.uuid4(),
                'processed_count': batch_size,
                'processing_time': simulated_time,
                'enriched_data': [
                    {
                        'symbol': company.tickers[0].symbol if company.tickers else fake.stock_ticker(),
                        'current_price': float(fake.pydecimal(left_digits=3, right_digits=2, positive=True)),
                        'day_volume': fake.random_int(min=10_000, max=10_000_000),
                        'analyst_rating': fake.random_element(['BUY', 'HOLD', 'SELL']),
                        'price_target': float(fake.pydecimal(left_digits=3, right_digits=2, positive=True)),
                        'last_updated': fake.iso8601()
                    }
                    for company in company_batch
                ]
            }
        
        mock_client.enrich_company_data.side_effect = realistic_bulk_api_response
        
        # Mock repository with realistic database performance characteristics
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        
        def realistic_bulk_database_operation(company_batch):
            """Simulate realistic database bulk operations."""
            batch_size = len(company_batch)
            
            # Simulate database processing time (5ms per company + transaction overhead)
            simulated_time = (batch_size * 0.005) + fake.pyfloat(min_value=0.05, max_value=0.2)
            
            # Simulate occasional database issues (2% chance)
            if fake.boolean(chance_of_getting_true=2):
                error_types = [
                    f"Deadlock detected in batch of {batch_size} companies",
                    "Connection pool exhausted - please retry",
                    f"Transaction timeout after {simulated_time:.2f}s",
                    "Constraint violation in batch operation"
                ]
                raise Exception(fake.random_element(error_types))
            
            # Generate realistic result IDs
            return [
                EnhancedCompanyFactory.build(
                    id=fake.random_int(min=100000, max=999999),
                    company_name=company.company_name,
                    sector=company.sector
                )
                for company in company_batch
            ]
        
        mock_repo.bulk_create_companies.side_effect = realistic_bulk_database_operation
        
        # === TEST LARGE-SCALE PROCESSING WITH REALISTIC CONSTRAINTS ===
        
        processing_start = time.time()
        
        # Process in realistic batch sizes
        batch_size = 50  # Realistic batch size for external APIs
        results = {
            'successful_batches': [],
            'failed_batches': [],
            'total_processed': 0,
            'total_api_calls': 0,
            'total_db_operations': 0,
            'retry_attempts': 0
        }
        
        for i in range(0, len(large_dataset), batch_size):
            batch = large_dataset[i:i + batch_size]
            batch_number = i // batch_size + 1
            
            try:
                # Simulate retry logic for failed operations
                max_retries = 3
                for retry in range(max_retries + 1):
                    try:
                        # API enrichment
                        enriched_data = mock_client.enrich_company_data(batch)
                        results['total_api_calls'] += 1
                        
                        # Database bulk operation
                        db_results = mock_repo.bulk_create_companies(batch)
                        results['total_db_operations'] += 1
                        
                        results['successful_batches'].append({
                            'batch_number': batch_number,
                            'size': len(batch),
                            'api_response': enriched_data,
                            'db_results': db_results
                        })
                        results['total_processed'] += len(batch)
                        break
                        
                    except Exception as e:
                        if retry < max_retries:
                            results['retry_attempts'] += 1
                            # Simulate exponential backoff
                            # mock_sleep would be called here
                            continue
                        else:
                            # Final failure
                            results['failed_batches'].append({
                                'batch_number': batch_number,
                                'size': len(batch),
                                'error': str(e),
                                'retry_count': retry
                            })
                            break
            
            except Exception as unexpected_error:
                results['failed_batches'].append({
                    'batch_number': batch_number,
                    'size': len(batch),
                    'error': f"Unexpected error: {str(unexpected_error)}",
                    'retry_count': 0
                })
            
            # Progress reporting
            if batch_number % 10 == 0:
                print(f"Processed batch {batch_number}/{len(large_dataset) // batch_size}")
        
        processing_time = time.time() - processing_start
        
        # === VERIFY REALISTIC PERFORMANCE CHARACTERISTICS ===
        
        print(f"\n=== Performance Test Results ===")
        print(f"Dataset size: {dataset_size} companies")
        print(f"Generation time: {generation_time:.2f}s")
        print(f"Processing time: {processing_time:.2f}s")
        print(f"Total processed: {results['total_processed']}")
        print(f"Success rate: {results['total_processed']/(dataset_size)*100:.1f}%")
        print(f"Failed batches: {len(results['failed_batches'])}")
        print(f"Retry attempts: {results['retry_attempts']}")
        print(f"API calls made: {results['total_api_calls']}")
        print(f"DB operations: {results['total_db_operations']}")
        
        # Performance assertions
        self.assertLess(generation_time, 10.0, "Dataset generation should be under 10 seconds")
        self.assertLess(processing_time, 30.0, "Processing should be under 30 seconds")
        
        # Realistic success rates (should handle some failures gracefully)
        success_rate = results['total_processed'] / dataset_size
        self.assertGreater(success_rate, 0.90, "Should achieve >90% success rate")
        
        # Should have made reasonable number of API calls (with retries)
        expected_batches = (dataset_size + batch_size - 1) // batch_size  # Ceiling division
        self.assertGreaterEqual(results['total_api_calls'], expected_batches)
        self.assertLessEqual(results['total_api_calls'], expected_batches * 4)  # Max 4 attempts per batch
        
        # Verify realistic failure patterns
        if results['failed_batches']:
            for failed_batch in results['failed_batches']:
                self.assertIsInstance(failed_batch['error'], str)
                self.assertGreaterEqual(failed_batch['retry_count'], 0)
                self.assertLessEqual(failed_batch['retry_count'], 3)
        
        # Verify Factory Boy data maintained consistency throughout
        for successful_batch in results['successful_batches'][:5]:  # Check first 5 batches
            for company in successful_batch['db_results']:
                self.assertIn(company.sector, StockMarketProvider.sectors)
                self.assertGreater(company.market_cap, 0)
                self.assertIsNotNone(company.company_name)
```

## Type-Safe Ultimate Integration

### Comprehensive Type Safety with All Three Libraries

When using all three libraries together, maintaining type safety becomes crucial for catching errors and improving code maintainability:

```python
from unittest.mock import MagicMock, create_autospec
from typing import List, Optional, TYPE_CHECKING, cast
import factory
from faker import Faker
from faker.providers import BaseProvider

if TYPE_CHECKING:
    from src.repos.equities.companies.company_repository import CompanyRepository
    from src.database.equities.tables.company import Company
    from src.database.equities.tables.ticker import Ticker

class TypedStockMarketProvider(BaseProvider):
    """Type-safe custom Faker provider with proper return type annotations."""
    
    def stock_ticker(self) -> str:
        """Generate realistic stock ticker with proper return typing."""
        length = self.random_element([3, 4, 4, 4, 5])
        return ''.join(self.random_choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', length=length))
    
    def stock_sector(self) -> str:
        """Return properly typed sector string."""
        sectors = ['Technology', 'Healthcare', 'Financial Services', 'Consumer Discretionary']
        return self.random_element(sectors)
    
    def market_cap_by_sector(self, sector: str) -> int:
        """Generate realistic market cap with type safety."""
        if sector == 'Technology':
            return self.random_int(5_000_000_000, 3_000_000_000_000)
        elif sector == 'Healthcare':
            return self.random_int(1_000_000_000, 500_000_000_000)
        else:
            return self.random_int(500_000_000, 200_000_000_000)

class TypedEnhancedCompanyFactory(SQLAlchemyModelFactory):
    """Type-safe Factory Boy with proper model typing."""
    
    class Meta:
        model = Company
        sqlalchemy_session = None
    
    id = factory.Sequence(lambda n: n + 1)
    company_name = factory.Faker('company')
    sector = factory.LazyFunction(lambda: typed_fake.stock_sector())
    market_cap = factory.LazyAttribute(lambda obj: typed_fake.market_cap_by_sector(obj.sector))
    exchange = factory.Iterator(['NASDAQ', 'NYSE', 'AMEX'])
    active = True
    source = 'TYPED_INTEGRATION_TEST'
    
    @classmethod
    def build_typed(cls, **kwargs) -> 'Company':
        """Build company with enforced typing."""
        company = cls.build(**kwargs)
        
        # Ensure proper typing for mock integration
        if not isinstance(company, Company):
            typed_company = MagicMock(spec=Company)
            for attr in ['id', 'company_name', 'sector', 'market_cap', 'exchange', 'active']:
                if hasattr(company, attr):
                    setattr(typed_company, attr, getattr(company, attr))
            return cast('Company', typed_company)
        
        return company

# Setup typed Faker instance
typed_fake = Faker()
typed_fake.add_provider(TypedStockMarketProvider)
Faker.seed(12345)

class UltimateTypedTestCase(unittest.TestCase):
    
    def setUp(self):
        """Setup all three libraries with consistent typing."""
        factory.Faker.seed(12345)
        
        # Type-safe helpers
        self.typed_repo_mock = self.create_typed_repo_mock()
        self.typed_companies = self.generate_typed_test_companies()
    
    def create_typed_repo_mock(self) -> 'CompanyRepository':
        """Create fully typed repository mock."""
        return cast('CompanyRepository', create_autospec(CompanyRepository, spec_set=True))
    
    def generate_typed_test_companies(self) -> List['Company']:
        """Generate typed companies using all three libraries."""
        companies = []
        
        for _ in range(10):
            # Factory Boy creates structure
            factory_company = TypedEnhancedCompanyFactory.build_typed()
            
            # Faker adds variety within type constraints
            enhanced_company = MagicMock(spec=Company)
            enhanced_company.id = factory_company.id
            enhanced_company.company_name = factory_company.company_name
            enhanced_company.sector = factory_company.sector
            enhanced_company.market_cap = factory_company.market_cap
            
            # Add Faker-generated details
            enhanced_company.description = typed_fake.text(max_nb_chars=500)
            enhanced_company.founded_year = typed_fake.random_int(min=1900, max=2023)
            enhanced_company.employee_count = typed_fake.random_int(min=50, max=500000)
            
            companies.append(cast('Company', enhanced_company))
        
        return companies
    
    def test_ultimate_typed_repository_workflow(self):
        """Test complete workflow with type safety enforced."""
        
        # === ARRANGE: Setup typed mocks and data ===
        
        # Mock external API with typed responses
        mock_api = create_autospec('src.external_apis.MarketDataClient', spec_set=True)
        
        # Generate realistic API response using Faker with types
        api_response_data = {
            'companies': [
                {
                    'symbol': typed_fake.stock_ticker(),
                    'current_price': float(typed_fake.pydecimal(left_digits=3, right_digits=2, positive=True)),
                    'volume': typed_fake.random_int(min=100_000, max=50_000_000),
                    'market_cap': typed_fake.market_cap_by_sector('Technology'),
                    'last_updated': typed_fake.iso8601()
                }
                for company in self.typed_companies
            ],
            'total_count': len(self.typed_companies),
            'timestamp': typed_fake.iso8601()
        }
        
        mock_api.bulk_get_market_data.return_value = api_response_data
        
        # Setup typed repository mock behavior
        def typed_find_by_symbol(symbol: str) -> Optional['Company']:
            """Type-safe symbol lookup."""
            matching = [c for c in self.typed_companies if hasattr(c, 'symbol') and c.symbol == symbol]
            return matching[0] if matching else None
        
        def typed_create_company(company_data) -> 'Company':
            """Type-safe company creation."""
            created_company = MagicMock(spec=Company)
            created_company.id = typed_fake.random_int(min=1, max=10000)
            created_company.company_name = company_data.company_name
            created_company.sector = company_data.sector
            created_company.market_cap = company_data.market_cap
            return cast('Company', created_company)
        
        # Configure typed mock behavior
        self.typed_repo_mock.find_by_symbol.side_effect = typed_find_by_symbol
        self.typed_repo_mock.create_company.side_effect = typed_create_company
        
        # === ACT: Execute typed workflow ===
        
        results: List['Company'] = []
        
        for company in self.typed_companies[:5]:  # Test subset
            # API enrichment with type safety
            enriched_data = mock_api.bulk_get_market_data([company])
            
            # Repository operations with type safety
            existing = self.typed_repo_mock.find_by_symbol(company.company_name)
            
            if existing is None:
                created = self.typed_repo_mock.create_company(company)
                results.append(created)
        
        # === ASSERT: Verify typed results ===
        
        # Type-safe assertions
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 5)
        
        for result_company in results:
            # Verify proper typing
            self.assertIsInstance(result_company.id, int)
            self.assertIsInstance(result_company.company_name, str)
            self.assertIsInstance(result_company.sector, str)
            self.assertIsInstance(result_company.market_cap, int)
            
            # Verify realistic data ranges (Faker constraints)
            self.assertGreater(result_company.market_cap, 0)
            self.assertIn(result_company.sector, ['Technology', 'Healthcare', 'Financial Services', 'Consumer Discretionary'])
        
        # Verify API calls were made with proper types
        mock_api.bulk_get_market_data.assert_called()
        
        # Verify repository calls with proper signatures
        self.assertEqual(self.typed_repo_mock.find_by_symbol.call_count, 5)
        self.assertEqual(self.typed_repo_mock.create_company.call_count, 5)

### Advanced Typed Error Handling

```python
def test_comprehensive_typed_error_scenarios(self):
    """Test error scenarios with proper exception typing."""
    
    from src.utils.exceptions import ValidationError, DatabaseError, APIError
    
    # Create error scenarios using Factory Boy with type constraints
    error_companies = [
        TypedEnhancedCompanyFactory.build_typed(market_cap=-1000),     # Invalid market cap
        TypedEnhancedCompanyFactory.build_typed(sector="Invalid"),    # Invalid sector
        TypedEnhancedCompanyFactory.build_typed(company_name=""),     # Empty name
    ]
    
    # Setup typed error responses
    mock_validator = create_autospec('src.validation.CompanyValidator', spec_set=True)
    mock_api = create_autospec('src.external_apis.MarketDataClient', spec_set=True)
    
    def typed_validation_error(company: 'Company') -> None:
        """Type-safe validation with proper exception types."""
        if company.market_cap <= 0:
            raise ValidationError(
                message=f"Invalid market cap: {company.market_cap}",
                field="market_cap",
                value=company.market_cap,
                company_id=company.id
            )
        
        if company.sector not in ['Technology', 'Healthcare', 'Financial Services']:
            raise ValidationError(
                message=f"Invalid sector: {company.sector}",
                field="sector",
                value=company.sector,
                company_id=company.id
            )
        
        if not company.company_name or not company.company_name.strip():
            raise ValidationError(
                message="Company name cannot be empty",
                field="company_name", 
                value=company.company_name,
                company_id=company.id
            )
    
    def typed_api_error(*args, **kwargs) -> None:
        """Type-safe API error simulation."""
        error_scenarios = [
            APIError(f"Rate limit exceeded: {typed_fake.sentence()}", status_code=429),
            APIError(f"Service unavailable: {typed_fake.sentence()}", status_code=503),
            APIError(f"Invalid request: {typed_fake.sentence()}", status_code=400)
        ]
        raise typed_fake.random_element(error_scenarios)
    
    # Configure typed error behavior
    mock_validator.validate_company.side_effect = typed_validation_error
    mock_api.get_company_data.side_effect = typed_api_error
    
    # Test each error scenario with proper typing
    for i, company in enumerate(error_companies):
        with self.subTest(scenario=i):
            
            # Test validation errors
            with self.assertRaises(ValidationError) as validation_context:
                mock_validator.validate_company(company)
            
            # Verify typed exception attributes
            validation_error = validation_context.exception
            self.assertIsInstance(validation_error.message, str)
            self.assertIsInstance(validation_error.field, str)
            self.assertIsInstance(validation_error.company_id, int)
            
            # Test API errors
            with self.assertRaises(APIError) as api_context:
                mock_api.get_company_data(company.id)
            
            # Verify typed API exception
            api_error = api_context.exception
            self.assertIsInstance(api_error.args[0], str)
            self.assertIsInstance(api_error.status_code, int)
            self.assertIn(api_error.status_code, [400, 429, 503])

### Type-Safe Performance Testing

```python
def test_typed_large_scale_processing(self):
    """Test large-scale processing with type safety maintained."""
    
    from typing import Dict, Any
    
    # Generate large typed dataset
    large_dataset_size = 1000
    
    typed_companies: List['Company'] = []
    for batch_start in range(0, large_dataset_size, 100):
        batch_companies = TypedEnhancedCompanyFactory.build_batch(
            min(100, large_dataset_size - batch_start)
        )
        
        # Convert to typed mocks for performance testing
        typed_batch = [
            cast('Company', MagicMock(spec=Company, **{
                'id': company.id,
                'company_name': company.company_name,
                'sector': company.sector,
                'market_cap': company.market_cap,
                'active': company.active
            }))
            for company in batch_companies
        ]
        
        typed_companies.extend(typed_batch)
    
    # Setup typed bulk processing mocks
    mock_bulk_processor = create_autospec('src.services.BulkProcessingService', spec_set=True)
    
    def typed_bulk_response(company_batch: List['Company']) -> Dict[str, Any]:
        """Type-safe bulk processing response."""
        return {
            'processed_count': len(company_batch),
            'successful': [c.id for c in company_batch if typed_fake.boolean(chance_of_getting_true=95)],
            'failed': [c.id for c in company_batch if typed_fake.boolean(chance_of_getting_true=5)],
            'processing_time': typed_fake.pyfloat(min_value=0.1, max_value=2.0),
            'timestamp': typed_fake.iso8601()
        }
    
    mock_bulk_processor.process_batch.side_effect = typed_bulk_response
    
    # Process in type-safe batches
    batch_size = 50
    total_processed = 0
    
    for i in range(0, len(typed_companies), batch_size):
        batch = typed_companies[i:i + batch_size]
        
        # Type-safe batch processing
        result = mock_bulk_processor.process_batch(batch)
        
        # Verify typed results
        self.assertIsInstance(result['processed_count'], int)
        self.assertIsInstance(result['successful'], list)
        self.assertIsInstance(result['failed'], list)
        self.assertIsInstance(result['processing_time'], float)
        self.assertIsInstance(result['timestamp'], str)
        
        total_processed += result['processed_count']
    
    # Verify complete processing with type safety
    self.assertEqual(total_processed, large_dataset_size)
    
    # Verify all objects maintained proper typing
    for company in typed_companies[:10]:  # Sample check
        self.assertIsInstance(company.id, int)
        self.assertIsInstance(company.company_name, str)
        self.assertIsInstance(company.active, bool)
```

## Best Practices for the Ultimate Integration

### 1. Library Responsibility Separation

```python
class TestingLibraryResponsibilities:
    """Clear separation of what each library handles."""
    
    # unittest.mock - CONTROL
    @patch('external_api.client')           # Mock external dependencies
    @patch('database.connection')           # Mock infrastructure
    @patch('file_system.operations')        # Mock I/O operations
    
    # Factory Boy - STRUCTURE  
    def create_related_objects(self):
        companies = CompanyFactory.build_batch(10)      # Complex object relationships
        return companies
    
    # Faker - CONTENT
    def generate_realistic_content(self):
        return {
            'api_response': fake.json(),                 # Realistic response content
            'error_message': fake.sentence(),            # Realistic error messages
            'timestamp': fake.iso8601(),                 # Realistic timestamps
            'user_data': fake.profile()                  # Realistic user data
        }
```

### 2. Consistent Seeding Strategy

```python
def setUp(self):
    """Ensure all three libraries use consistent seeds."""
    # Primary seed for reproducibility
    master_seed = 12345
    
    # Seed all libraries consistently
    unittest.mock.Mock.seed = master_seed
    factory.Faker.seed(master_seed)
    fake.seed_(master_seed)
    
    # Can use different seeds for different test classes
    # but keep them consistent within each test
```

### 3. Realistic Data Relationships

```python
class RealisticDataPattern:
    """Pattern for maintaining realistic relationships across all three libraries."""
    
    def create_consistent_test_scenario(self):
        # Factory Boy creates the structure
        company = EnhancedCompanyFactory.build(sector="Technology")
        
        # Faker generates content that matches the structure
        api_response = {
            'company_data': {
                'symbol': company.tickers[0].symbol,
                'sector_analysis': fake.text() if company.sector == "Technology" else fake.bs(),
                'market_metrics': fake.pydecimal() if company.market_cap > 1_000_000_000 else fake.pyfloat()
            }
        }
        
        # unittest.mock controls how these are delivered
        with patch('external_api.get_data') as mock_api:
            mock_api.return_value = api_response
            # Test with realistic, consistent data
```

### 4. Performance Optimization

```python
class PerformanceOptimizedTesting:
    """Optimize the combination for large test suites."""
    
    @classmethod
    def setUpClass(cls):
        """One-time expensive setup for entire test class."""
        # Pre-generate expensive Factory Boy objects
        cls.company_templates = EnhancedCompanyFactory.build_batch(100)
        
        # Pre-generate common Faker content
        cls.common_responses = {
            'api_success': [fake.json() for _ in range(10)],
            'api_errors': [fake.sentence() for _ in range(10)],
            'timestamps': [fake.iso8601() for _ in range(20)]
        }
    
    def test_with_pregenerated_data(self):
        """Use pre-generated data for faster test execution."""
        # Reuse pre-generated Factory Boy objects
        company = fake.random_element(self.company_templates)
        
        # Reuse pre-generated Faker content
        api_response = fake.random_element(self.common_responses['api_success'])
        
        # Mock with pre-generated realistic data
        with patch('api.client') as mock_client:
            mock_client.get_data.return_value = api_response
            # Fast test execution with realistic data
```

## When to Use the Ultimate Combination

✅ **Perfect For:**
- **Comprehensive integration testing** that needs to be both realistic and controlled
- **End-to-end business logic testing** with complex data relationships
- **Performance testing** with realistic data volumes and patterns
- **Scenario testing** covering multiple realistic edge cases
- **Production simulation** without production risks or dependencies

✅ **Ultimate Benefits:**
- **Maximum realism**: Factory Boy structure + Faker variety = production-like data
- **Complete control**: unittest.mock isolates all external dependencies
- **Comprehensive coverage**: Test realistic scenarios, edge cases, and error conditions
- **Maintainable**: Changes to one library don't break the others
- **Scalable**: Can generate large, realistic datasets efficiently

❌ **Don't Use When:**
- **Simple unit tests** where basic mocks are sufficient
- **Performance is critical** and the overhead isn't justified
- **Team familiarity** with all three libraries is limited
- **Test complexity** would exceed the benefit gained

## Running the Ultimate Tests

```bash
# Install all dependencies
pip install factory_boy Faker  # unittest.mock is built-in

# Run ultimate integration tests
python -m unittest discover tests/ultimate/ -v

# Run with performance profiling
python -m cProfile -s cumulative -m unittest tests.ultimate.test_complete_integration

# Run with memory profiling
python -m memory_profiler tests/ultimate/test_performance.py

# Run with coverage
coverage run -m unittest discover tests/ultimate/
coverage report --show-missing
```

This ultimate integration provides the most comprehensive, realistic, and controlled testing environment possible for your Options-Deep project - combining the structure of Factory Boy, the variety of Faker, and the control of unittest.mock into a powerful testing trinity.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "1", "content": "Create unittest.mock + Faker + Factory Boy integration guide", "status": "completed", "priority": "high"}]