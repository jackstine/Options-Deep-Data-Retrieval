"""Mock implementation of TickerHistoryRepository for testing."""

from src.data_sources.models.test_providers import StockMarketProvider
from src.data_sources.models.ticker_history import (
    TickerHistory as TickerHistoryDataModel,
)

from __future__ import annotations

from datetime import date, timedelta
import logging

from faker import Faker

logger = logging.getLogger(__name__)


class TickerHistoryRepositoryMock:
    """Mock implementation of TickerHistoryRepository for testing purposes."""

    def __init__(self, seed: int = 12345):
        """Initialize mock repository with Faker for realistic data."""
        self.fake = Faker()
        self.fake.add_provider(StockMarketProvider)
        Faker.seed(seed)

        # In-memory storage for mock data
        self._ticker_histories: dict[int, TickerHistoryDataModel] = {}
        self._next_id = 1
        self._symbol_histories: dict[
            str, list[int]
        ] = {}  # symbol -> list of history_ids
        self._company_histories: dict[
            int, list[int]
        ] = {}  # company_id -> list of history_ids

        # Initialize with some sample data
        self._initialize_sample_data()

    def _initialize_sample_data(self) -> None:
        """Initialize with realistic sample ticker histories."""
        today = date.today()

        sample_histories = [
            # Current active tickers
            {
                "symbol": "AAPL",
                "company_id": 1,
                "valid_from": today - timedelta(days=365 * 10),
                "valid_to": None,
                "active": True,
            },
            {
                "symbol": "MSFT",
                "company_id": 2,
                "valid_from": today - timedelta(days=365 * 15),
                "valid_to": None,
                "active": True,
            },
            {
                "symbol": "AMZN",
                "company_id": 3,
                "valid_from": today - timedelta(days=365 * 8),
                "valid_to": None,
                "active": True,
            },
            # Historical ticker changes
            {
                "symbol": "FB",
                "company_id": 6,
                "valid_from": today - timedelta(days=365 * 5),
                "valid_to": today - timedelta(days=365),
                "active": False,
            },
            {
                "symbol": "META",
                "company_id": 6,
                "valid_from": today - timedelta(days=365),
                "valid_to": None,
                "active": True,
            },
            # Multiple tickers for same company
            {
                "symbol": "GOOGL",
                "company_id": 4,
                "valid_from": today - timedelta(days=365 * 3),
                "valid_to": None,
                "active": True,
            },
            {
                "symbol": "GOOG",
                "company_id": 4,
                "valid_from": today - timedelta(days=365 * 3),
                "valid_to": None,
                "active": True,
            },
            # Some inactive historical entries
            {
                "symbol": "NFLX",
                "company_id": 7,
                "valid_from": today - timedelta(days=365 * 6),
                "valid_to": today - timedelta(days=30),
                "active": False,
            },
            {
                "symbol": "NFLX",
                "company_id": 7,
                "valid_from": today - timedelta(days=30),
                "valid_to": None,
                "active": True,
            },
        ]

        for history_data in sample_histories:
            history = TickerHistoryDataModel(id=self._next_id, **history_data)

            self._ticker_histories[self._next_id] = history

            # Track symbol relationships
            if history.symbol not in self._symbol_histories:
                self._symbol_histories[history.symbol] = []
            self._symbol_histories[history.symbol].append(self._next_id)

            # Track company relationships
            if history.company_id not in self._company_histories:
                self._company_histories[history.company_id] = []
            self._company_histories[history.company_id].append(self._next_id)

            self._next_id += 1

    def _create_fake_ticker_history(self, **overrides) -> TickerHistoryDataModel:
        """Create a realistic TickerHistory with Faker data."""
        today = date.today()

        default_data = {
            "id": self._next_id,
            "symbol": self.fake.stock_ticker(),
            "company_id": self.fake.random_int(1, 100),
            "valid_from": today - timedelta(days=self.fake.random_int(30, 365 * 3)),
            "valid_to": None
            if self.fake.boolean(chance_of_getting_true=70)
            else today - timedelta(days=self.fake.random_int(1, 30)),
            "active": self.fake.boolean(chance_of_getting_true=80),
        }

        default_data.update(overrides)
        return TickerHistoryDataModel(**default_data)

    def _is_currently_active(self, history: TickerHistoryDataModel) -> bool:
        """Check if a ticker history is currently active."""
        today = date.today()
        return (
            history.active
            and history.valid_from <= today
            and (history.valid_to is None or history.valid_to >= today)
        )

    # Base repository methods
    def get(
        self, filter_model: TickerHistoryDataModel | None = None, options=None
    ) -> list[TickerHistoryDataModel]:
        """Get ticker histories based on filter."""
        histories = list(self._ticker_histories.values())

        if filter_model is None:
            return histories

        filtered = []
        for history in histories:
            match = True

            if filter_model.id is not None and history.id != filter_model.id:
                match = False
            if (
                filter_model.symbol is not None
                and filter_model.symbol != ""
                and history.symbol != filter_model.symbol
            ):
                match = False
            if (
                filter_model.company_id is not None
                and filter_model.company_id != 0
                and history.company_id != filter_model.company_id
            ):
                match = False
            if (
                filter_model.active is not None
                and history.active != filter_model.active
            ):
                match = False

            if match:
                filtered.append(history)

        # Apply ordering if specified in options
        if (
            options
            and hasattr(options, "order_by")
            and options.order_by == "valid_from"
        ):
            filtered.sort(key=lambda h: h.valid_from)

        return filtered

    def get_one(
        self, filter_model: TickerHistoryDataModel
    ) -> TickerHistoryDataModel | None:
        """Get single ticker history matching filter."""
        results = self.get(filter_model)
        return results[0] if results else None

    def get_by_id(self, id: int) -> TickerHistoryDataModel | None:
        """Get ticker history by ID."""
        return self._ticker_histories.get(id)

    def count(self, filter_model: TickerHistoryDataModel | None = None) -> int:
        """Count ticker histories matching filter."""
        return len(self.get(filter_model))

    def insert(self, data_model: TickerHistoryDataModel) -> TickerHistoryDataModel:
        """Insert single ticker history."""
        if data_model.id is None:
            data_model.id = self._next_id
            self._next_id += 1

        self._ticker_histories[data_model.id] = data_model

        # Track symbol relationships
        if data_model.symbol not in self._symbol_histories:
            self._symbol_histories[data_model.symbol] = []
        if data_model.id not in self._symbol_histories[data_model.symbol]:
            self._symbol_histories[data_model.symbol].append(data_model.id)

        # Track company relationships
        if data_model.company_id not in self._company_histories:
            self._company_histories[data_model.company_id] = []
        if data_model.id not in self._company_histories[data_model.company_id]:
            self._company_histories[data_model.company_id].append(data_model.id)

        logger.info(
            f"Mock: Inserted ticker history {data_model.symbol} with ID {data_model.id}"
        )
        return data_model

    def insert_many(self, data_models: list[TickerHistoryDataModel]) -> int:
        """Insert multiple ticker histories."""
        count = 0
        for history in data_models:
            self.insert(history)
            count += 1

        logger.info(f"Mock: Bulk inserted {count} ticker histories")
        return count

    def update(
        self, filter_model: TickerHistoryDataModel, update_data: TickerHistoryDataModel
    ) -> int:
        """Update ticker histories matching filter."""
        histories_to_update = self.get(filter_model)
        count = 0

        for history in histories_to_update:
            # Update non-empty fields from update_data
            if update_data.symbol and update_data.symbol != "":
                # Update symbol mapping
                old_symbol = history.symbol
                history.symbol = update_data.symbol

                # Update symbol tracking
                if old_symbol in self._symbol_histories:
                    if history.id in self._symbol_histories[old_symbol]:
                        self._symbol_histories[old_symbol].remove(history.id)
                    if not self._symbol_histories[old_symbol]:
                        del self._symbol_histories[old_symbol]

                if history.symbol not in self._symbol_histories:
                    self._symbol_histories[history.symbol] = []
                if history.id not in self._symbol_histories[history.symbol]:
                    self._symbol_histories[history.symbol].append(history.id)

            if update_data.company_id is not None and update_data.company_id != 0:
                # Update company relationships
                old_company_id = history.company_id
                new_company_id = update_data.company_id

                if old_company_id in self._company_histories:
                    if history.id in self._company_histories[old_company_id]:
                        self._company_histories[old_company_id].remove(history.id)

                history.company_id = new_company_id
                if new_company_id not in self._company_histories:
                    self._company_histories[new_company_id] = []
                if history.id not in self._company_histories[new_company_id]:
                    self._company_histories[new_company_id].append(history.id)

            if update_data.valid_to is not None:
                history.valid_to = update_data.valid_to

            if update_data.active is not None:
                history.active = update_data.active

            count += 1

        logger.info(f"Mock: Updated {count} ticker histories")
        return count

    def update_by_id(self, id: int, update_data: TickerHistoryDataModel) -> bool:
        """Update ticker history by ID."""
        filter_model = TickerHistoryDataModel(
            id=id, symbol="", company_id=0, valid_from=date.today()
        )
        return self.update(filter_model, update_data) > 0

    # Domain-specific methods
    def get_active_ticker_history_symbols(self) -> set[str]:
        """Get all currently active ticker symbols from ticker history."""
        active_symbols = set()

        for history in self._ticker_histories.values():
            if self._is_currently_active(history):
                active_symbols.add(history.symbol)

        logger.info(
            f"Mock: Retrieved {len(active_symbols)} active ticker history symbols"
        )
        return active_symbols

    def get_ticker_history_for_company(
        self, company_id: int
    ) -> list[TickerHistoryDataModel]:
        """Get all ticker history records for a specific company."""
        history_ids = self._company_histories.get(company_id, [])
        histories = [
            self._ticker_histories[hid]
            for hid in history_ids
            if hid in self._ticker_histories
        ]

        # Sort by valid_from date
        histories.sort(key=lambda h: h.valid_from)

        logger.info(
            f"Mock: Retrieved {len(histories)} ticker histories for company {company_id}"
        )
        return histories

    def get_ticker_history_by_symbol(self, symbol: str) -> list[TickerHistoryDataModel]:
        """Get all ticker history records for a symbol."""
        history_ids = self._symbol_histories.get(symbol, [])
        histories = [
            self._ticker_histories[hid]
            for hid in history_ids
            if hid in self._ticker_histories
        ]

        # Sort by valid_from date
        histories.sort(key=lambda h: h.valid_from)

        logger.info(
            f"Mock: Retrieved {len(histories)} ticker histories for symbol {symbol}"
        )
        return histories

    def bulk_insert_ticker_histories(
        self, ticker_histories: list[TickerHistoryDataModel]
    ) -> int:
        """Bulk insert ticker histories."""
        return self.insert_many(ticker_histories)

    def get_all_ticker_histories(self) -> list[TickerHistoryDataModel]:
        """Retrieve all ticker histories."""
        return self.get()

    def create_ticker_history_for_company(
        self,
        symbol: str,
        company_id: int,
        valid_from: date | None = None,
        valid_to: date | None = None,
        active: bool = True,
    ) -> TickerHistoryDataModel:
        """Create a new ticker history record for a company."""
        if valid_from is None:
            valid_from = date.today()

        ticker_history_data = TickerHistoryDataModel(
            symbol=symbol,
            company_id=company_id,
            valid_from=valid_from,
            valid_to=valid_to,
            active=active,
        )
        return self.insert(ticker_history_data)

    def get_active_ticker_histories(self) -> list[TickerHistoryDataModel]:
        """Get all active ticker history records."""
        return [
            history
            for history in self._ticker_histories.values()
            if self._is_currently_active(history)
        ]

    def deactivate_ticker_history(
        self, symbol: str, company_id: int, end_date: date | None = None
    ) -> bool:
        """Deactivate a ticker history record."""
        if end_date is None:
            end_date = date.today()

        # Find matching active records
        matching_histories = []
        for history in self._ticker_histories.values():
            if (
                history.symbol == symbol
                and history.company_id == company_id
                and history.active
                and (history.valid_to is None or history.valid_to >= end_date)
            ):
                matching_histories.append(history)

        count = 0
        for history in matching_histories:
            history.valid_to = end_date
            history.active = False
            count += 1

        logger.info(f"Mock: Deactivated {count} ticker history records for {symbol}")
        return count > 0

    # Utility methods for testing
    def reset(self) -> None:
        """Reset mock data to initial state."""
        self._ticker_histories.clear()
        self._symbol_histories.clear()
        self._company_histories.clear()
        self._next_id = 1
        self._initialize_sample_data()

    def add_fake_ticker_histories(
        self, count: int = 5, company_id: int | None = None, symbol: str | None = None
    ) -> list[TickerHistoryDataModel]:
        """Add fake ticker histories for testing."""
        histories = []
        for _ in range(count):
            history_data = {}
            if company_id is not None:
                history_data["company_id"] = company_id
            if symbol is not None:
                history_data["symbol"] = symbol

            history = self._create_fake_ticker_history(**history_data)
            self.insert(history)
            histories.append(history)

        return histories

    def get_ticker_history_count(self) -> int:
        """Get total number of ticker histories."""
        return len(self._ticker_histories)

    def get_active_count(self) -> int:
        """Get count of currently active ticker histories."""
        return len(self.get_active_ticker_histories())

    def get_symbols_with_multiple_histories(self) -> list[str]:
        """Get symbols that have multiple history records (useful for testing)."""
        return [
            symbol
            for symbol, history_ids in self._symbol_histories.items()
            if len(history_ids) > 1
        ]

    def simulate_database_error(
        self, method_name: str, error_message: str = "Database error"
    ):
        """Simulate database error for testing error handling."""
        logger.warning(
            f"Mock: Simulating database error for {method_name}: {error_message}"
        )
        raise Exception(error_message)

    def get_history_for_date_range(
        self, start_date: date, end_date: date
    ) -> list[TickerHistoryDataModel]:
        """Get ticker histories valid within a date range (utility for testing)."""
        histories = []
        for history in self._ticker_histories.values():
            if history.valid_from <= end_date and (
                history.valid_to is None or history.valid_to >= start_date
            ):
                histories.append(history)

        return histories


# Factory function for easy mock creation
def create_ticker_history_repository_mock(
    seed: int = 12345,
) -> TickerHistoryRepositoryMock:
    """Factory function to create a TickerHistoryRepositoryMock instance."""
    return TickerHistoryRepositoryMock(seed=seed)


# Example usage for testing
if __name__ == "__main__":
    # Create mock repository
    mock_repo = create_ticker_history_repository_mock()

    # Display sample data
    print(
        f"Mock repository initialized with {mock_repo.get_ticker_history_count()} ticker histories"
    )
    print(f"Active ticker histories: {mock_repo.get_active_count()}")

    # Show currently active symbols
    active_symbols = mock_repo.get_active_ticker_history_symbols()
    print(f"\nCurrently active symbols ({len(active_symbols)}):")
    for symbol in sorted(active_symbols):
        print(f"  - {symbol}")

    # Show symbols with multiple histories
    multi_history_symbols = mock_repo.get_symbols_with_multiple_histories()
    print(f"\nSymbols with multiple histories ({len(multi_history_symbols)}):")
    for symbol in multi_history_symbols:
        histories = mock_repo.get_ticker_history_by_symbol(symbol)
        print(f"  - {symbol}: {len(histories)} records")
        for history in histories:
            status = "ACTIVE" if mock_repo._is_currently_active(history) else "INACTIVE"
            valid_to_str = (
                history.valid_to.strftime("%Y-%m-%d") if history.valid_to else "Present"
            )
            print(
                f"    {history.valid_from.strftime('%Y-%m-%d')} to {valid_to_str} [{status}]"
            )

    # Add fake data
    fake_histories = mock_repo.add_fake_ticker_histories(3, company_id=999)
    print(f"\nAdded {len(fake_histories)} fake ticker histories for company 999")
