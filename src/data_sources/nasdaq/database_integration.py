"""NASDAQ screener database integration functionality."""

from __future__ import annotations
import logging
from pathlib import Path
from typing import List, Set, Tuple
from datetime import date

from src.repos.equities.companies.company_repository import CompanyRepository
from src.repos.equities.tickers.ticker_repository import TickerRepository
from src.repos.equities.tickers.ticker_history_repository import TickerHistoryRepository
from src.data_sources.models.company import Company as CompanyDataModel
from src.data_sources.models.ticker import Ticker as TickerDataModel
from src.data_sources.models.ticker_history import TickerHistory as TickerHistoryDataModel
from src.data_sources.nasdaq.screener import load_screener_files_from_directory


logger = logging.getLogger(__name__)


class NasdaqScreenerSyncProcessor:
    """Process NASDAQ screener data synchronization with database."""
    
    def __init__(self, screener_dir: str | Path = None) -> None:
        """
        Initialize the processor.
        
        Args:
            screener_dir: Path to directory containing screener CSV files.
                         If None, uses default path.
        """
        self.screener_dir = screener_dir or Path(__file__).parent / "data" / "data_screener"
        self.company_repo = CompanyRepository()
        self.ticker_repo = TickerRepository()
        self.ticker_history_repo = TickerHistoryRepository()
        self.logger = logging.getLogger(__name__)
    
    def _identify_new_companies(self, screener_companies: List[CompanyDataModel], 
                               existing_symbols: Set[str]) -> List[CompanyDataModel]:
        """
        Identify new companies from screener data that don't exist in the database.
        
        Args:
            screener_companies: List of companies from NASDAQ screener
            existing_symbols: Set of existing ticker symbols in database
            
        Returns:
            List of new companies not in database
        """
        new_companies = []
        
        for company in screener_companies:
            ticker_symbol = company.ticker.symbol if company.ticker else None
            if ticker_symbol and ticker_symbol not in existing_symbols:
                new_companies.append(company)
        
        self.logger.info(f"Identified {len(new_companies)} new companies from screener data")
        
        # Log some examples
        if new_companies:
            self.logger.info("Sample new companies:")
            for company in new_companies[:5]:
                ticker_symbol = company.ticker.symbol if company.ticker else "No ticker"
                self.logger.info(f"  {ticker_symbol} - {company.company_name}")
        
        return new_companies
    
    def _identify_new_tickers(self, screener_companies: List[CompanyDataModel], 
                             existing_ticker_symbols: Set[str]) -> List[CompanyDataModel]:
        """
        Identify companies with new ticker symbols that don't exist in the database.
        
        Args:
            screener_companies: List of companies from NASDAQ screener
            existing_ticker_symbols: Set of existing ticker symbols in database
            
        Returns:
            List of companies with new ticker symbols
        """
        new_ticker_companies = []
        
        for company in screener_companies:
            ticker_symbol = company.ticker.symbol if company.ticker else None
            if ticker_symbol and ticker_symbol not in existing_ticker_symbols:
                new_ticker_companies.append(company)
        
        self.logger.info(f"Identified {len(new_ticker_companies)} companies with new ticker symbols")
        
        # Log some examples
        if new_ticker_companies:
            self.logger.info("Sample new ticker symbols:")
            for company in new_ticker_companies[:5]:
                ticker_symbol = company.ticker.symbol if company.ticker else "No ticker"
                self.logger.info(f"  {ticker_symbol} - {company.company_name}")
        
        return new_ticker_companies
    
    def _create_tickers_for_companies(self, companies_with_tickers: List[CompanyDataModel]) -> List[TickerDataModel]:
        """
        Create ticker data models for companies that have been inserted into the database.
        
        Args:
            companies_with_tickers: List of companies with ticker symbols and database IDs
            
        Returns:
            List of ticker data models ready for insertion
        """
        tickers = []
        
        for company in companies_with_tickers:
            if company.ticker and company.id:
                # Create a new TickerDataModel for database insertion
                ticker = TickerDataModel(
                    symbol=company.ticker.symbol,
                    company_id=company.id
                )
                tickers.append(ticker)
        
        self.logger.info(f"Created {len(tickers)} ticker data models")
        return tickers
    
    def _create_ticker_histories_for_companies(self, companies_with_tickers: List[CompanyDataModel]) -> List[TickerHistoryDataModel]:
        """
        Create ticker history data models for companies that have been inserted into the database.

        Args:
            companies_with_tickers: List of companies with ticker symbols and database IDs
            
        Returns:
            List of ticker history data models ready for insertion
        """
        ticker_histories = []
        today = date.today()
        
        for company in companies_with_tickers:
            if company.ticker and company.id:
                # Create a new TickerHistoryDataModel for database insertion
                ticker_history = TickerHistoryDataModel(
                    symbol=company.ticker.symbol,
                    company_id=company.id,
                    valid_from=today,
                    valid_to=None,  # Open-ended validity
                    active=True
                )
                ticker_histories.append(ticker_history)
        
        self.logger.info(f"Created {len(ticker_histories)} ticker history data models")
        return ticker_histories
    
    def _identify_companies_to_update(self, screener_companies: List[CompanyDataModel], 
                                    existing_symbols: Set[str]) -> List[CompanyDataModel]:
        """
        Identify existing companies that need to be updated with new data from screener.

        Args:
            screener_companies: List of companies from NASDAQ screener
            existing_symbols: Set of existing ticker symbols in database
            
        Returns:
            List of companies that exist and may need updates
        """
        companies_to_update = []
        
        for company in screener_companies:
            ticker_symbol = company.ticker.symbol if company.ticker else None
            if ticker_symbol and ticker_symbol in existing_symbols:
                companies_to_update.append(company)
        
        self.logger.info(f"Identified {len(companies_to_update)} companies that may need updates")
        return companies_to_update
    
    def _get_unused_tickers(self, active_screener_symbols: Set[str]) -> Set[str]:
        """
        Identify ticker symbols that are in the database but not in the current screener data.

        Args:
            active_screener_symbols: Set of ticker symbols from current screener data
            
        Returns:
            Set of ticker symbols that are in database but not in screener
        """
        try:
            # Get all active ticker symbols from database
            db_ticker_symbols = self.ticker_repo.get_active_ticker_symbols()
            
            # Find tickers in database that are not in current screener data
            unused_tickers = db_ticker_symbols - active_screener_symbols
            
            self.logger.info(f"Found {len(unused_tickers)} unused ticker symbols")
            return unused_tickers
            
        except Exception as e:
            self.logger.error(f"Error identifying unused tickers: {e}")
            raise
    
    def run_get_new_companies(self) -> tuple[List[CompanyDataModel], List[CompanyDataModel]]:
        """
        Get new companies from screener data that don't exist in database.
        
        Returns:
            Tuple of (new_companies, all_screener_companies)
            
        Raises:
            Exception: If process fails
        """
        self.logger.info("Starting NASDAQ screener new companies identification")
        try:
            self.logger.info("Loading NASDAQ screener data...")
            screener_companies = load_screener_files_from_directory(self.screener_dir)
            
            if not screener_companies:
                self.logger.warning("No screener companies found")
                return [], []

            self.logger.info("Retrieving active company symbols from database...")
            existing_symbols = self.company_repo.get_active_company_symbols()
            
            self.logger.info("Identifying new companies...")
            new_companies = self._identify_new_companies(screener_companies, existing_symbols)
            
            return new_companies, screener_companies
            
        except Exception as e:
            self.logger.error(f"Error during new companies identification: {e}")
            raise
    
    def run_sync_companies_and_tickers(self) -> dict:
        """
        Synchronize both companies and tickers from NASDAQ screener data with database.
        
        Returns:
            Dictionary with sync results containing:
            - total_screener_companies: Total companies in screener
            - existing_companies: Companies already in database
            - new_companies_found: New companies identified
            - companies_inserted: Companies successfully inserted
            - existing_tickers: Ticker symbols already in database
            - new_tickers_found: New ticker symbols identified
            - tickers_inserted: Tickers successfully inserted
            
        Raises:
            Exception: If sync process fails
        """
        self.logger.info("Starting NASDAQ screener companies and tickers synchronization")
        try:
            # Load screener data
            self.logger.info("Loading NASDAQ screener data...")
            screener_companies = load_screener_files_from_directory(self.screener_dir)
            
            if not screener_companies:
                self.logger.warning("No screener companies found")
                return {
                    'total_screener_companies': 0,
                    'existing_companies': 0,
                    'new_companies_found': 0,
                    'companies_inserted': 0,
                    'existing_tickers': 0,
                    'new_tickers_found': 0,
                    'tickers_inserted': 0
                }
            
            # Get existing data from database
            self.logger.info("Retrieving existing data from database...")
            existing_company_symbols = self.company_repo.get_active_company_symbols()
            existing_ticker_symbols = self.ticker_repo.get_active_ticker_symbols()
            
            # Identify new companies and tickers
            self.logger.info("Identifying new companies...")
            new_companies = self._identify_new_companies(screener_companies, existing_company_symbols)
            
            self.logger.info("Identifying new ticker symbols...")
            new_ticker_companies = self._identify_new_tickers(screener_companies, existing_ticker_symbols)
            
            companies_inserted = 0
            tickers_inserted = 0
            
            # Insert new companies first
            if new_companies:
                self.logger.info("Inserting new companies into database...")
                companies_inserted = self.company_repo.bulk_insert_companies(new_companies)
                
                # After inserting companies, we need to get their IDs to create tickers
                if companies_inserted > 0:
                    # Get the newly inserted companies with their database IDs
                    inserted_companies_with_ids = []
                    for company in new_companies:
                        if company.ticker:
                            # Look up the company by ticker symbol to get its ID
                            ticker_symbol = company.ticker.symbol
                            db_company = self.company_repo.get_company_by_ticker(ticker_symbol)
                            if db_company:
                                inserted_companies_with_ids.append(db_company)
                    
                    # Create tickers for the newly inserted companies
                    tickers_to_insert = self._create_tickers_for_companies(inserted_companies_with_ids)
                    if tickers_to_insert:
                        self.logger.info("Inserting tickers for new companies...")
                        tickers_inserted += self.ticker_repo.bulk_insert_tickers(tickers_to_insert)
            
            # Handle companies that exist but might have new ticker symbols
            existing_companies_with_new_tickers = []
            for ticker_company in new_ticker_companies:
                ticker_symbol = ticker_company.ticker.symbol if ticker_company.ticker else None
                new_company_tickers = [c.ticker.symbol for c in new_companies if c.ticker]
                
                if ticker_symbol and ticker_symbol not in new_company_tickers:
                    # This is an existing company with a new ticker symbol
                    existing_company = self.company_repo.get_company_by_ticker(ticker_symbol)
                    if not existing_company:
                        # Try to find by company name as fallback
                        # This would require additional repository method
                        continue
                    existing_companies_with_new_tickers.append(existing_company)
            
            # Create tickers for existing companies with new symbols
            if existing_companies_with_new_tickers:
                additional_tickers = self._create_tickers_for_companies(existing_companies_with_new_tickers)
                if additional_tickers:
                    self.logger.info("Inserting additional ticker symbols...")
                    tickers_inserted += self.ticker_repo.bulk_insert_tickers(additional_tickers)
            
            # Prepare results
            results = {
                'total_screener_companies': len(screener_companies),
                'existing_companies': len(screener_companies) - len(new_companies),
                'new_companies_found': len(new_companies),
                'companies_inserted': companies_inserted,
                'existing_tickers': len(screener_companies) - len(new_ticker_companies),
                'new_tickers_found': len(new_ticker_companies),
                'tickers_inserted': tickers_inserted
            }
            
            self.logger.info("NASDAQ screener companies and tickers synchronization completed successfully")
            self.logger.info(f"Results: {results}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error during screener companies and tickers sync: {e}")
            raise
    
    def run_sync_screener_with_database(self) -> dict:
        """
        Main function to synchronize NASDAQ screener data with database.
        
        Returns:
            Dictionary with sync results containing:
            - total_screener_companies: Total companies in screener
            - existing_companies: Companies already in database
            - new_companies_found: New companies identified
            - companies_inserted: Companies successfully inserted
            
        Raises:
            Exception: If sync process fails
        """
        self.logger.info("Starting NASDAQ screener database synchronization")
        try:
            new_companies, screener_companies = self.run_get_new_companies()
            
            if len(new_companies) == 0:
                return {
                    'total_screener_companies': len(screener_companies),
                    'existing_companies': len(screener_companies),
                    'new_companies_found': 0,
                    'companies_inserted': 0
                }

            self.logger.info("Inserting new companies into database...")
            companies_inserted = self.company_repo.bulk_insert_companies(new_companies)
            
            # Prepare results
            results = {
                'total_screener_companies': len(screener_companies),
                'existing_companies': len(screener_companies) - len(new_companies),
                'new_companies_found': len(new_companies),
                'companies_inserted': companies_inserted
            }
            
            self.logger.info("NASDAQ screener database synchronization completed successfully")
            self.logger.info(f"Results: {results}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error during screener database sync: {e}")
            raise
    
    def run_comprehensive_sync(self) -> dict:
        """
        Comprehensive synchronization of NASDAQ screener data with database.
        
        This method:
        1. Inserts new tickers with ticker_histories and companies
        2. Updates existing companies
        3. Identifies and reports unused tickers
        
        Returns:
            Dictionary with comprehensive sync results containing:
            - total_screener_companies: Total companies in screener
            - new_companies_inserted: New companies successfully inserted
            - companies_updated: Existing companies successfully updated
            - new_tickers_inserted: New tickers successfully inserted
            - ticker_histories_inserted: Ticker histories successfully inserted
            - unused_tickers: Set of unused ticker symbols
            - unused_ticker_count: Count of unused tickers
            
        Raises:
            Exception: If sync process fails
        """
        self.logger.info("Starting comprehensive NASDAQ screener database synchronization")
        try:
            # Load screener data
            self.logger.info("Loading NASDAQ screener data...")
            screener_companies = load_screener_files_from_directory(self.screener_dir)
            
            if not screener_companies:
                self.logger.warning("No screener companies found")
                return {
                    'total_screener_companies': 0,
                    'new_companies_inserted': 0,
                    'companies_updated': 0,
                    'new_tickers_inserted': 0,
                    'ticker_histories_inserted': 0,
                    'unused_tickers': set(),
                    'unused_ticker_count': 0
                }
            
            # Get screener ticker symbols
            screener_symbols = {
                company.ticker.symbol for company in screener_companies 
                if company.ticker and company.ticker.symbol
            }
            
            # Get existing data from database
            self.logger.info("Retrieving existing data from database...")
            existing_company_symbols = self.company_repo.get_active_company_symbols()
            
            # Identify different categories of companies
            self.logger.info("Categorizing companies...")
            new_companies = self._identify_new_companies(screener_companies, existing_company_symbols)
            companies_to_update = self._identify_companies_to_update(screener_companies, existing_company_symbols)
            unused_tickers = self._get_unused_tickers(screener_symbols)
            
            new_companies_inserted = 0
            companies_updated = 0
            new_tickers_inserted = 0
            ticker_histories_inserted = 0
            
            # 1. Insert new companies
            if new_companies:
                self.logger.info(f"Inserting {len(new_companies)} new companies...")
                new_companies_inserted = self.company_repo.bulk_insert_companies(new_companies)
                
                if new_companies_inserted > 0:
                    # Get the newly inserted companies with their database IDs
                    inserted_companies_with_ids = []
                    for company in new_companies:
                        if company.ticker:
                            ticker_symbol = company.ticker.symbol
                            db_company = self.company_repo.get_company_by_ticker(ticker_symbol)
                            if db_company:
                                inserted_companies_with_ids.append(db_company)
                    
                    # Create tickers for new companies
                    if inserted_companies_with_ids:
                        tickers_to_insert = self._create_tickers_for_companies(inserted_companies_with_ids)
                        if tickers_to_insert:
                            self.logger.info(f"Inserting {len(tickers_to_insert)} new tickers...")
                            new_tickers_inserted = self.ticker_repo.bulk_insert_tickers(tickers_to_insert)
                        
                        # Create ticker histories for new companies
                        ticker_histories_to_insert = self._create_ticker_histories_for_companies(inserted_companies_with_ids)
                        if ticker_histories_to_insert:
                            self.logger.info(f"Inserting {len(ticker_histories_to_insert)} new ticker histories...")
                            ticker_histories_inserted = self.ticker_history_repo.bulk_insert_ticker_histories(ticker_histories_to_insert)
            
            # 2. Update existing companies
            if companies_to_update:
                self.logger.info(f"Updating {len(companies_to_update)} existing companies...")
                for company in companies_to_update:
                    if company.ticker:
                        ticker_symbol = company.ticker.symbol
                        if self.company_repo.update_company(ticker_symbol, company):
                            companies_updated += 1
            
            # 3. Report unused tickers
            if unused_tickers:
                self.logger.info(f"Found {len(unused_tickers)} unused tickers:")
                for ticker in sorted(unused_tickers):
                    self.logger.info(f"  - {ticker}")
            
            # Prepare comprehensive results
            results = {
                'total_screener_companies': len(screener_companies),
                'new_companies_inserted': new_companies_inserted,
                'companies_updated': companies_updated,
                'new_tickers_inserted': new_tickers_inserted,
                'ticker_histories_inserted': ticker_histories_inserted,
                'unused_tickers': unused_tickers,
                'unused_ticker_count': len(unused_tickers)
            }
            
            self.logger.info("Comprehensive NASDAQ screener database synchronization completed successfully")
            self.logger.info(f"Results: {results}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error during comprehensive screener sync: {e}")
            raise


# Backward compatibility functions
def identify_new_companies(screener_companies: List[CompanyDataModel], 
                          existing_symbols: Set[str]) -> List[CompanyDataModel]:
    """Legacy function - use NasdaqScreenerSyncProcessor._identify_new_companies instead."""
    processor = NasdaqScreenerSyncProcessor()
    return processor._identify_new_companies(screener_companies, existing_symbols)


def sync_screener_with_database(screener_dir: str | Path = None) -> dict:
    """Legacy function - use NasdaqScreenerSyncProcessor.run_sync_screener_with_database instead."""
    processor = NasdaqScreenerSyncProcessor(screener_dir)
    return processor.run_sync_screener_with_database()


def get_new_companies_from_sync(screener_dir: str | Path = None) -> tuple[List[CompanyDataModel], List[CompanyDataModel]]:
    """Legacy function - use NasdaqScreenerSyncProcessor.run_get_new_companies instead."""
    processor = NasdaqScreenerSyncProcessor(screener_dir)
    return processor.run_get_new_companies()


def sync_companies_and_tickers_with_database(screener_dir: str | Path = None) -> dict:
    """
    Synchronize both companies and tickers from NASDAQ screener data with database.
    
    Args:
        screener_dir: Path to directory containing screener CSV files.
                     If None, uses default path.
        
    Returns:
        Dictionary with sync results for both companies and tickers
    """
    processor = NasdaqScreenerSyncProcessor(screener_dir)
    return processor.run_sync_companies_and_tickers()


def run_comprehensive_sync(screener_dir: str | Path = None) -> dict:
    """
    Run comprehensive synchronization of NASDAQ screener data with database.
    
    This function:
    1. Inserts new tickers with ticker_histories and companies
    2. Updates existing companies
    3. Identifies and reports unused tickers
    
    Args:
        screener_dir: Path to directory containing screener CSV files.
                     If None, uses default path.
        
    Returns:
        Dictionary with comprehensive sync results
    """
    processor = NasdaqScreenerSyncProcessor(screener_dir)
    return processor.run_comprehensive_sync()


def print_sync_results(results: dict) -> None:
    """
    Print sync results in a user-friendly format.
    
    Args:
        results: Dictionary with sync results from sync functions
    """
    print("\n=== NASDAQ Screener Database Sync Results ===")
    print(f"Total companies in screener: {results['total_screener_companies']:,}")
    
    # Handle comprehensive sync results
    if 'new_companies_inserted' in results:
        print(f"New companies inserted: {results['new_companies_inserted']:,}")
        print(f"Existing companies updated: {results['companies_updated']:,}")
        print(f"New tickers inserted: {results['new_tickers_inserted']:,}")
        print(f"Ticker histories inserted: {results['ticker_histories_inserted']:,}")
        
        # Print unused tickers information
        unused_count = results.get('unused_ticker_count', 0)
        print(f"\nUnused tickers (in database but not in screener): {unused_count:,}")
        
        if unused_count > 0 and 'unused_tickers' in results:
            unused_tickers = results['unused_tickers']
            if len(unused_tickers) <= 10:
                print("Unused ticker symbols:")
                for ticker in sorted(unused_tickers):
                    print(f"  - {ticker}")
            else:
                print("Sample unused ticker symbols (showing first 10):")
                for ticker in sorted(list(unused_tickers)[:10]):
                    print(f"  - {ticker}")
                print(f"  ... and {len(unused_tickers) - 10} more")
        
        # Determine overall status for comprehensive sync
        total_insertions = results['new_companies_inserted'] + results['new_tickers_inserted'] + results['ticker_histories_inserted']
        total_updates = results['companies_updated']
        
        if total_insertions > 0 or total_updates > 0:
            print("\n✓ Comprehensive database sync completed successfully")
        else:
            print("\n✓ Database is up to date - no new data found")
    
    # Handle legacy sync results format
    else:
        print(f"Companies already in database: {results.get('existing_companies', 0):,}")
        print(f"New companies found: {results.get('new_companies_found', 0):,}")
        print(f"Companies successfully inserted: {results.get('companies_inserted', 0):,}")
        
        # Print ticker results if available
        if 'new_tickers_found' in results:
            print(f"\nTicker Symbol Results:")
            print(f"Existing ticker symbols: {results['existing_tickers']:,}")
            print(f"New ticker symbols found: {results['new_tickers_found']:,}")
            print(f"Ticker symbols successfully inserted: {results['tickers_inserted']:,}")
        
        # Determine overall status for legacy results
        companies_success = results.get('companies_inserted', 0) > 0 or results.get('new_companies_found', 0) == 0
        tickers_success = True
        if 'new_tickers_found' in results:
            tickers_success = results['tickers_inserted'] > 0 or results['new_tickers_found'] == 0
        
        if companies_success and tickers_success:
            if results.get('companies_inserted', 0) > 0 or results.get('tickers_inserted', 0) > 0:
                print("\n✓ Database sync completed successfully")
            else:
                print("\n✓ Database is up to date - no new data found")
        else:
            print("\n⚠ Some data may not have been inserted - check logs")


if __name__ == "__main__":
    # Example usage
    import sys
    
    try:
        # Run the sync
        results = sync_screener_with_database()
        print_sync_results(results)
        
    except Exception as e:
        print(f"✗ Sync failed: {e}")
        sys.exit(1)