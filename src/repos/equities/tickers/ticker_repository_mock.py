"""Mock implementation of TickerRepository for testing."""

from __future__ import annotations
import logging
from typing import List, Set, Optional, Dict
from faker import Faker

from src.data_sources.models.ticker import Ticker as TickerDataModel
from src.data_sources.models.test_providers import StockMarketProvider


logger = logging.getLogger(__name__)


class TickerRepositoryMock:
    """Mock implementation of TickerRepository for testing purposes."""
    
    def __init__(self, seed: int = 12345):
        """Initialize mock repository with Faker for realistic data."""
        self.fake = Faker()
        self.fake.add_provider(StockMarketProvider)
        Faker.seed(seed)
        
        # In-memory storage for mock data
        self._tickers: Dict[int, TickerDataModel] = {}
        self._next_id = 1
        self._symbol_to_ticker: Dict[str, int] = {}
        self._company_tickers: Dict[int, List[int]] = {}  # company_id -> list of ticker_ids
        
        # Initialize with some sample data
        self._initialize_sample_data()
    
    def _initialize_sample_data(self) -> None:
        """Initialize with realistic sample tickers."""
        sample_tickers = [
            {'symbol': 'AAPL', 'company_id': 1},
            {'symbol': 'MSFT', 'company_id': 2},
            {'symbol': 'AMZN', 'company_id': 3},
            {'symbol': 'GOOGL', 'company_id': 4},
            {'symbol': 'GOOG', 'company_id': 4},  # Multiple tickers for same company
            {'symbol': 'TSLA', 'company_id': 5},
            {'symbol': 'META', 'company_id': 6},
            {'symbol': 'NFLX', 'company_id': 7},
            {'symbol': 'NVDA', 'company_id': 8},
        ]
        
        for ticker_data in sample_tickers:
            ticker = TickerDataModel(
                id=self._next_id,
                **ticker_data
            )
            
            self._tickers[self._next_id] = ticker
            self._symbol_to_ticker[ticker.symbol] = self._next_id
            
            # Track company relationships
            if ticker.company_id not in self._company_tickers:
                self._company_tickers[ticker.company_id] = []
            self._company_tickers[ticker.company_id].append(self._next_id)
            
            self._next_id += 1
    
    def _create_fake_ticker(self, **overrides) -> TickerDataModel:
        """Create a realistic Ticker with Faker data."""
        default_data = {
            'id': self._next_id,
            'symbol': self.fake.stock_ticker(),
            'company_id': self.fake.random_int(1, 100)
        }
        
        default_data.update(overrides)
        return TickerDataModel(**default_data)
    
    # Base repository methods
    def get(self, filter_model: Optional[TickerDataModel] = None) -> List[TickerDataModel]:
        """Get tickers based on filter."""
        tickers = list(self._tickers.values())
        
        if filter_model is None:
            return tickers
        
        filtered = []
        for ticker in tickers:
            match = True
            
            if filter_model.id is not None and ticker.id != filter_model.id:
                match = False
            if (filter_model.symbol is not None and filter_model.symbol != "" 
                and ticker.symbol != filter_model.symbol):
                match = False
            if (filter_model.company_id is not None and filter_model.company_id != 0
                and ticker.company_id != filter_model.company_id):
                match = False
            
            if match:
                filtered.append(ticker)
        
        return filtered
    
    def get_one(self, filter_model: TickerDataModel) -> Optional[TickerDataModel]:
        """Get single ticker matching filter."""
        results = self.get(filter_model)
        return results[0] if results else None
    
    def get_by_id(self, id: int) -> Optional[TickerDataModel]:
        """Get ticker by ID."""
        return self._tickers.get(id)
    
    def count(self, filter_model: Optional[TickerDataModel] = None) -> int:
        """Count tickers matching filter."""
        return len(self.get(filter_model))
    
    def insert(self, data_model: TickerDataModel) -> TickerDataModel:
        """Insert single ticker."""
        if data_model.id is None:
            data_model.id = self._next_id
            self._next_id += 1
        
        self._tickers[data_model.id] = data_model
        self._symbol_to_ticker[data_model.symbol] = data_model.id
        
        # Track company relationships
        if data_model.company_id:
            if data_model.company_id not in self._company_tickers:
                self._company_tickers[data_model.company_id] = []
            if data_model.id not in self._company_tickers[data_model.company_id]:
                self._company_tickers[data_model.company_id].append(data_model.id)
        
        logger.info(f"Mock: Inserted ticker {data_model.symbol} with ID {data_model.id}")
        return data_model
    
    def insert_many(self, data_models: List[TickerDataModel]) -> int:
        """Insert multiple tickers."""
        count = 0
        for ticker in data_models:
            self.insert(ticker)
            count += 1
        
        logger.info(f"Mock: Bulk inserted {count} tickers")
        return count
    
    def update(self, filter_model: TickerDataModel, update_data: TickerDataModel) -> int:
        """Update tickers matching filter."""
        tickers_to_update = self.get(filter_model)
        count = 0
        
        for ticker in tickers_to_update:
            # Update non-empty fields from update_data
            if update_data.symbol and update_data.symbol != "":
                # Update symbol mapping
                if ticker.symbol in self._symbol_to_ticker:
                    del self._symbol_to_ticker[ticker.symbol]
                ticker.symbol = update_data.symbol
                self._symbol_to_ticker[ticker.symbol] = ticker.id
                
            if update_data.company_id is not None and update_data.company_id != 0:
                # Update company relationships
                old_company_id = ticker.company_id
                new_company_id = update_data.company_id
                
                if old_company_id and old_company_id in self._company_tickers:
                    if ticker.id in self._company_tickers[old_company_id]:
                        self._company_tickers[old_company_id].remove(ticker.id)
                
                ticker.company_id = new_company_id
                if new_company_id not in self._company_tickers:
                    self._company_tickers[new_company_id] = []
                if ticker.id not in self._company_tickers[new_company_id]:
                    self._company_tickers[new_company_id].append(ticker.id)
            
            count += 1
        
        logger.info(f"Mock: Updated {count} tickers")
        return count
    
    def update_by_id(self, id: int, update_data: TickerDataModel) -> bool:
        """Update ticker by ID."""
        filter_model = TickerDataModel(id=id, symbol="", company_id=0)
        return self.update(filter_model, update_data) > 0
    
    # Domain-specific methods
    def get_active_ticker_symbols(self) -> Set[str]:
        """Get all ticker symbols from the repository."""
        symbols = {ticker.symbol for ticker in self._tickers.values()}
        logger.info(f"Mock: Retrieved {len(symbols)} ticker symbols")
        return symbols
    
    def get_tickers_for_company(self, company_id: int) -> List[TickerDataModel]:
        """Get all tickers for a specific company."""
        ticker_ids = self._company_tickers.get(company_id, [])
        tickers = [self._tickers[tid] for tid in ticker_ids if tid in self._tickers]
        
        logger.info(f"Mock: Retrieved {len(tickers)} tickers for company {company_id}")
        return tickers
    
    def get_ticker_by_symbol(self, symbol: str) -> Optional[TickerDataModel]:
        """Get ticker by symbol."""
        ticker_id = self._symbol_to_ticker.get(symbol)
        if ticker_id:
            return self._tickers.get(ticker_id)
        return None
    
    def bulk_insert_tickers(self, tickers: List[TickerDataModel]) -> int:
        """Bulk insert tickers."""
        return self.insert_many(tickers)
    
    def get_all_tickers(self) -> List[TickerDataModel]:
        """Retrieve all tickers."""
        return self.get()
    
    def create_ticker_for_company(self, symbol: str, company_id: int) -> TickerDataModel:
        """Create a new ticker for a company."""
        ticker_data = TickerDataModel(
            symbol=symbol,
            company_id=company_id
        )
        return self.insert(ticker_data)
    
    def update_ticker_company(self, symbol: str, new_company_id: int) -> bool:
        """Update the company_id for a ticker symbol."""
        ticker = self.get_ticker_by_symbol(symbol)
        if ticker:
            filter_model = TickerDataModel(id=ticker.id, symbol="", company_id=0)
            update_data = TickerDataModel(symbol="", company_id=new_company_id)
            return self.update(filter_model, update_data) > 0
        return False
    
    # Utility methods for testing
    def reset(self) -> None:
        """Reset mock data to initial state."""
        self._tickers.clear()
        self._symbol_to_ticker.clear()
        self._company_tickers.clear()
        self._next_id = 1
        self._initialize_sample_data()
    
    def add_fake_tickers(self, count: int = 5, company_id: Optional[int] = None) -> List[TickerDataModel]:
        """Add fake tickers for testing."""
        tickers = []
        for _ in range(count):
            ticker_data = {}
            if company_id is not None:
                ticker_data['company_id'] = company_id
            
            ticker = self._create_fake_ticker(**ticker_data)
            self.insert(ticker)
            tickers.append(ticker)
        
        return tickers
    
    def get_ticker_count(self) -> int:
        """Get total number of tickers."""
        return len(self._tickers)
    
    def get_company_ticker_count(self, company_id: int) -> int:
        """Get number of tickers for a specific company."""
        return len(self._company_tickers.get(company_id, []))
    
    def simulate_database_error(self, method_name: str, error_message: str = "Database error"):
        """Simulate database error for testing error handling."""
        logger.warning(f"Mock: Simulating database error for {method_name}: {error_message}")
        raise Exception(error_message)
    
    def get_symbols_starting_with(self, prefix: str) -> List[str]:
        """Get ticker symbols starting with prefix (utility for testing)."""
        return [symbol for symbol in self._symbol_to_ticker.keys() 
                if symbol.startswith(prefix.upper())]


# Factory function for easy mock creation
def create_ticker_repository_mock(seed: int = 12345) -> TickerRepositoryMock:
    """Factory function to create a TickerRepositoryMock instance."""
    return TickerRepositoryMock(seed=seed)


# Example usage for testing
if __name__ == "__main__":
    # Create mock repository
    mock_repo = create_ticker_repository_mock()
    
    # Display sample data
    print(f"Mock repository initialized with {mock_repo.get_ticker_count()} tickers:")
    for ticker in mock_repo.get_all_tickers():
        print(f"  - {ticker.symbol} (Company ID: {ticker.company_id})")
    
    # Test company relationships
    google_tickers = mock_repo.get_tickers_for_company(4)  # Google has multiple tickers
    print(f"\nGoogle (Company ID 4) has {len(google_tickers)} tickers:")
    for ticker in google_tickers:
        print(f"  - {ticker.symbol}")
    
    # Add fake tickers
    fake_tickers = mock_repo.add_fake_tickers(3, company_id=999)
    print(f"\nAdded {len(fake_tickers)} fake tickers for company 999:")
    for ticker in fake_tickers:
        print(f"  - {ticker.symbol}")
    
    # Test symbol lookup
    aapl_ticker = mock_repo.get_ticker_by_symbol("AAPL")
    if aapl_ticker:
        print(f"\nFound AAPL ticker: ID {aapl_ticker.id}, Company ID {aapl_ticker.company_id}")