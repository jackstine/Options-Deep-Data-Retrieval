"""NASDAQ screener database integration functionality."""

from __future__ import annotations
import logging
from pathlib import Path
from typing import List, Set

from src.repos.equities.companies.company_repository import CompanyRepository
from src.data_sources.models.company import Company as CompanyDataModel
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
            if company.ticker not in existing_symbols:
                new_companies.append(company)
        
        self.logger.info(f"Identified {len(new_companies)} new companies from screener data")
        
        # Log some examples
        if new_companies:
            self.logger.info("Sample new companies:")
            for company in new_companies[:5]:
                self.logger.info(f"  {company.ticker} - {company.company_name}")
        
        return new_companies
    
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


def print_sync_results(results: dict) -> None:
    """
    Print sync results in a user-friendly format.
    
    Args:
        results: Dictionary with sync results from sync_screener_with_database
    """
    print("\n=== NASDAQ Screener Database Sync Results ===")
    print(f"Total companies in screener: {results['total_screener_companies']:,}")
    print(f"Companies already in database: {results['existing_companies']:,}")
    print(f"New companies found: {results['new_companies_found']:,}")
    print(f"Companies successfully inserted: {results['companies_inserted']:,}")
    
    if results['companies_inserted'] > 0:
        print("✓ Database sync completed successfully")
    elif results['new_companies_found'] == 0:
        print("✓ Database is up to date - no new companies found")
    else:
        print("⚠ Some companies may not have been inserted - check logs")


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