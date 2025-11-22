# Simple Pipeline Explanation

## Overview
The `src/pipelines/companies/new_company_pipeline.py` implements a comprehensive company ingestion pipeline that synchronizes company data from external sources to the database.

## Core Functionality

### Main Components
- **CompanyPipeline**: Primary class that orchestrates the entire ingestion process
- **Data Sources**: Interfaces with external APIs (NASDAQ, screeners) to fetch company data
- **Database Repositories**: Manages persistence to companies, tickers, and ticker history tables

### Key Methods

#### run_ingestion(sources)
- **Purpose**: Main entry point for standard company ingestion
- **Process**:
  - Fetches companies from all provided data sources
  - Validates source availability before processing
  - Handles errors gracefully (continues processing other sources)
  - Cleans and validates company data
  - Performs comprehensive database synchronization
- **Returns**: Dictionary with counts of inserted, updated, skipped, and error records

#### run_comprehensive_sync(sources)
- **Purpose**: Enhanced ingestion with unused ticker detection
- **Process**:
  - Executes standard ingestion first
  - Identifies ticker symbols in database that are no longer in active screener data
  - Provides visibility into potentially delisted or inactive tickers
- **Returns**: Standard results plus unused ticker information

### Data Processing Pipeline

#### Step 1: Data Collection
- Iterates through all provided data sources
- Checks source availability via `is_available()`
- Fetches company data using `get_companies()`
- Tags each company with source information
- Accumulates companies from all sources

#### Step 2: Data Cleaning
- **Duplicate Removal**: Eliminates companies with identical ticker symbols
- **Validation**: Removes companies without valid ticker symbols
- **Normalization**: Standardizes company names and exchange formats
- **Data Quality**: Ensures only valid, processable companies proceed

#### Step 3: Database Synchronization
- **Company Analysis**: Categorizes companies as new vs. existing
- **Bulk Operations**: Uses efficient bulk insert/update operations
- **Ticker Management**: Creates ticker records for new companies
- **History Tracking**: Maintains ticker history with validity dates
- **Error Handling**: Continues processing despite individual record failures

### Database Operations

#### New Company Processing
- Identifies companies not in existing database
- Performs bulk insert for efficiency
- Retrieves database-assigned IDs for inserted companies
- Creates corresponding ticker records
- Establishes ticker history with validity dates

#### Existing Company Updates
- Identifies companies already in database by ticker symbol
- Updates company information (name, sector, market cap, etc.)
- Handles update failures gracefully
- Tracks successful vs. failed updates

#### Ticker Symbol Management
- Manages relationship between companies and their ticker symbols
- Handles cases where companies have multiple ticker symbols
- Creates ticker history records for audit trail
- Tracks active vs. inactive ticker periods

### Advanced Features

#### Comprehensive Synchronization
- **Unused Ticker Detection**: Identifies tickers in database not found in current screener data
- **Data Consistency**: Ensures database reflects current market reality
- **Audit Trail**: Maintains history of all ticker symbol changes
- **Bulk Operations**: Optimizes database performance with batch processing

#### Error Handling & Resilience
- **Source Failures**: Continues processing if individual sources fail
- **Partial Success**: Handles scenarios where some operations succeed, others fail
- **Logging**: Comprehensive logging for monitoring and debugging
- **Transaction Safety**: Ensures database consistency during failures

## Usage Patterns

### Standard Ingestion
```python
pipeline = CompanyPipeline()
sources = [nasdaq_screener, nasdaq_api]
results = pipeline.run_ingestion(sources)
```

### Comprehensive Sync with Unused Detection
```python
pipeline = CompanyPipeline()
results = pipeline.run_comprehensive_sync(sources)
unused_count = results["unused_ticker_count"]
```

## Dependencies
- **Data Sources**: Must implement CompanyDataSource interface
- **Repositories**: CompanyRepository, TickerRepository, TickerHistoryRepository
- **Models**: Company, Ticker, TickerHistory data models

## Performance Characteristics
- **Bulk Operations**: Uses batch inserts/updates for efficiency
- **Memory Efficient**: Processes data in manageable chunks
- **Fault Tolerant**: Individual failures don't stop entire pipeline
- **Scalable**: Handles variable numbers of companies and data sources