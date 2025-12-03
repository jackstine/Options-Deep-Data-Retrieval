"""Split-adjusted pricing service for retrieving historical stock prices with split adjustments."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from src.models.date_price import DatePrice
from src.models.eod_split_adjusted_pricing import EODSplitAdjustedPricing
from src.models.historical_eod_pricing import HistoricalEndOfDayPricing
from src.models.split import Split
from src.models.split_adjusted_pricing import SplitAdjustedPricing
from src.repos.equities.pricing.historical_eod_pricing_repository import (
    HistoricalEodPricingRepository,
)
from src.repos.equities.splits.splits_repository import SplitsRepository
from src.repos.equities.tickers.ticker_history_repository import (
    TickerHistoryRepository,
)
from src.repos.equities.tickers.ticker_repository import TickerRepository

logger = logging.getLogger(__name__)


class SplitAdjustedPricingService:
    """Service for retrieving split-adjusted historical pricing data.

    This service provides methods to retrieve historical stock prices with
    split adjustments applied. It supports queries by symbol, ticker_history_id,
    or company_id, and can return either simple closing prices or full OHLCV data.

    Split Adjustment Logic:
        For each historical price, all stock splits that occurred AFTER that date
        are found. The cumulative split ratio is calculated by multiplying all
        future split ratios together. Prices are then adjusted by dividing by
        this cumulative ratio.

        Example:
            - Stock at $100 on 2020-01-01
            - 2-for-1 split on 2021-01-01 (ratio = 2.0)
            - 3-for-1 split on 2022-01-01 (ratio = 3.0)
            - Cumulative ratio for 2020 prices = 2.0 × 3.0 = 6.0
            - Adjusted price for 2020-01-01 = $100 / 6.0 = $16.67
    """

    def __init__(
        self,
        pricing_repo: HistoricalEodPricingRepository | None = None,
        splits_repo: SplitsRepository | None = None,
        ticker_repo: TickerRepository | None = None,
        ticker_history_repo: TickerHistoryRepository | None = None,
        logger_instance: logging.Logger | None = None,
    ) -> None:
        """Initialize the split-adjusted pricing service.

        Args:
            pricing_repo: Repository for historical pricing data
            splits_repo: Repository for stock splits data
            ticker_repo: Repository for active ticker symbols
            ticker_history_repo: Repository for ticker history (active + delisted)
            logger_instance: Logger instance for service operations
        """
        self.pricing_repo = pricing_repo or HistoricalEodPricingRepository()
        self.splits_repo = splits_repo or SplitsRepository()
        self.ticker_repo = ticker_repo or TickerRepository()
        self.ticker_history_repo = ticker_history_repo or TickerHistoryRepository()
        self.logger = logger_instance or logger

    def get_split_adjusted_pricing_with_symbol(
        self,
        symbol: str,
        from_date: date | None = None,
        to_date: date | None = None,
        include_ohlc: bool = False,
    ) -> SplitAdjustedPricing[DatePrice] | SplitAdjustedPricing[EODSplitAdjustedPricing]:
        """Get split-adjusted pricing data for a stock symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            from_date: Start date for pricing data (inclusive)
            to_date: End date for pricing data (inclusive)
            include_ohlc: If True, return full OHLCV data; if False, return only close prices

        Returns:
            SplitAdjustedPricing with either DatePrice or EODSplitAdjustedPricing data

        Raises:
            ValueError: If symbol is not found in database
        """
        self.logger.info(
            f"Fetching split-adjusted pricing for symbol={symbol}, "
            f"from={from_date}, to={to_date}, include_ohlc={include_ohlc}"
        )

        # Look up ticker_history_id from symbol
        ticker = self.ticker_repo.get_ticker_by_symbol(symbol)
        if not ticker:
            raise ValueError(f"Symbol '{symbol}' not found in database")

        if ticker.ticker_history_id is None:
            raise ValueError(f"Symbol '{symbol}' has no ticker_history_id")

        # Use the ticker_history_id method
        result = self.get_split_adjusted_pricing_with_ticker_history_id(
            ticker_history_id=ticker.ticker_history_id,
            from_date=from_date,
            to_date=to_date,
            include_ohlc=include_ohlc,
        )

        # Update the symbol in the result
        result.symbol = symbol

        return result

    def get_split_adjusted_pricing_with_ticker_history_id(
        self,
        ticker_history_id: int,
        from_date: date | None = None,
        to_date: date | None = None,
        include_ohlc: bool = False,
    ) -> SplitAdjustedPricing[DatePrice] | SplitAdjustedPricing[EODSplitAdjustedPricing]:
        """Get split-adjusted pricing data for a ticker_history_id.

        Args:
            ticker_history_id: Ticker history ID reference
            from_date: Start date for pricing data (inclusive)
            to_date: End date for pricing data (inclusive)
            include_ohlc: If True, return full OHLCV data; if False, return only close prices

        Returns:
            SplitAdjustedPricing with either DatePrice or EODSplitAdjustedPricing data
        """
        self.logger.info(
            f"Fetching split-adjusted pricing for ticker_history_id={ticker_history_id}, "
            f"from={from_date}, to={to_date}, include_ohlc={include_ohlc}"
        )

        # Fetch pricing data for the date range
        pricing_data = self.pricing_repo.get_pricing_by_ticker(
            ticker_history_id=ticker_history_id,
            from_date=from_date,
            to_date=to_date,
        )

        if not pricing_data:
            self.logger.warning(
                f"No pricing data found for ticker_history_id={ticker_history_id}"
            )
            # Return empty result
            if include_ohlc:
                return SplitAdjustedPricing[EODSplitAdjustedPricing](
                    prices=[],
                    from_date=from_date,
                    to_date=to_date,
                    ticker_history_id=ticker_history_id,
                )
            else:
                return SplitAdjustedPricing[DatePrice](
                    prices=[],
                    from_date=from_date,
                    to_date=to_date,
                    ticker_history_id=ticker_history_id,
                )

        # Fetch all splits for this ticker (need all splits to calculate cumulative ratio)
        splits_data = self.splits_repo.get_splits_by_ticker(
            ticker_history_id=ticker_history_id
        )

        self.logger.info(
            f"Found {len(pricing_data)} price records and {len(splits_data)} splits"
        )

        # Apply split adjustments based on output format
        if include_ohlc:
            adjusted_prices = self._calculate_split_adjusted_prices_ohlc(
                pricing_data, splits_data
            )
            return SplitAdjustedPricing[EODSplitAdjustedPricing](
                prices=adjusted_prices,
                from_date=from_date,
                to_date=to_date,
                ticker_history_id=ticker_history_id,
            )
        else:
            adjusted_prices = self._calculate_split_adjusted_prices_simple(
                pricing_data, splits_data
            )
            return SplitAdjustedPricing[DatePrice](
                prices=adjusted_prices,
                from_date=from_date,
                to_date=to_date,
                ticker_history_id=ticker_history_id,
            )

    def get_split_adjusted_pricing_with_company_id(
        self,
        company_id: int,
        include_ohlc: bool = False,
    ) -> SplitAdjustedPricing[DatePrice] | SplitAdjustedPricing[EODSplitAdjustedPricing]:
        """Get split-adjusted pricing data for all ticker histories of a company.

        This method retrieves pricing for ALL ticker histories associated with a company,
        which can include name changes, symbol changes, and delisted symbols. All pricing
        data is combined and sorted by date.

        Args:
            company_id: Company ID reference
            include_ohlc: If True, return full OHLCV data; if False, return only close prices

        Returns:
            SplitAdjustedPricing with either DatePrice or EODSplitAdjustedPricing data
        """
        self.logger.info(
            f"Fetching split-adjusted pricing for company_id={company_id}, "
            f"include_ohlc={include_ohlc}"
        )

        # Get all ticker histories for this company
        ticker_histories = self.ticker_history_repo.get_ticker_history_for_company(
            company_id=company_id
        )

        if not ticker_histories:
            self.logger.warning(
                f"No ticker histories found for company_id={company_id}"
            )
            # Return empty result
            if include_ohlc:
                return SplitAdjustedPricing[EODSplitAdjustedPricing](
                    prices=[],
                    from_date=None,
                    to_date=None,
                    company_id=company_id,
                )
            else:
                return SplitAdjustedPricing[DatePrice](
                    prices=[],
                    from_date=None,
                    to_date=None,
                    company_id=company_id,
                )

        self.logger.info(
            f"Found {len(ticker_histories)} ticker histories for company_id={company_id}"
        )

        # Collect all pricing data from all ticker histories
        all_adjusted_prices: list[DatePrice] | list[EODSplitAdjustedPricing] = []
        earliest_date: date | None = None
        latest_date: date | None = None

        for ticker_history in ticker_histories:
            if ticker_history.id is None:
                continue

            # Fetch pricing for this ticker history
            pricing_data = self.pricing_repo.get_pricing_by_ticker(
                ticker_history_id=ticker_history.id
            )

            if not pricing_data:
                continue

            # Fetch splits for this ticker history
            splits_data = self.splits_repo.get_splits_by_ticker(
                ticker_history_id=ticker_history.id
            )

            # Apply split adjustments
            if include_ohlc:
                adjusted = self._calculate_split_adjusted_prices_ohlc(
                    pricing_data, splits_data
                )
                all_adjusted_prices.extend(adjusted)
            else:
                adjusted = self._calculate_split_adjusted_prices_simple(
                    pricing_data, splits_data
                )
                all_adjusted_prices.extend(adjusted)

            # Track date range
            for price in pricing_data:
                if earliest_date is None or price.date < earliest_date:
                    earliest_date = price.date
                if latest_date is None or price.date > latest_date:
                    latest_date = price.date

        # Sort all prices by date (oldest first)
        all_adjusted_prices.sort(key=lambda p: p.date)

        self.logger.info(
            f"Retrieved {len(all_adjusted_prices)} total price records for company_id={company_id}"
        )

        if include_ohlc:
            return SplitAdjustedPricing[EODSplitAdjustedPricing](
                prices=all_adjusted_prices,
                from_date=earliest_date,
                to_date=latest_date,
                company_id=company_id,
            )
        else:
            return SplitAdjustedPricing[DatePrice](
                prices=all_adjusted_prices,
                from_date=earliest_date,
                to_date=latest_date,
                company_id=company_id,
            )

    def _calculate_split_adjusted_prices_simple(
        self,
        prices: list[HistoricalEndOfDayPricing],
        splits: list[Split],
    ) -> list[DatePrice]:
        """Calculate split-adjusted closing prices.

        Args:
            prices: List of historical pricing data
            splits: List of stock splits

        Returns:
            List of DatePrice with split-adjusted closing prices
        """
        if not prices:
            return []

        # Sort data by date (oldest first) - always sort for consistency
        sorted_prices = sorted(prices, key=lambda p: p.date)

        # If no splits, just convert to DatePrice with close prices
        if not splits:
            return [
                DatePrice(date=price.date, price=price.close)
                for price in sorted_prices
            ]
        sorted_splits = sorted(splits, key=lambda s: s.date)

        adjusted_prices: list[DatePrice] = []

        for price in sorted_prices:
            # Find all splits that occurred AFTER this price date
            future_splits = [s for s in sorted_splits if s.date > price.date]

            # Calculate cumulative split ratio
            cumulative_ratio = Decimal("1.0")
            for split in future_splits:
                cumulative_ratio *= split.get_split_ratio()

            # Adjust the close price
            adjusted_close = price.close / cumulative_ratio

            adjusted_prices.append(
                DatePrice(
                    date=price.date,
                    price=adjusted_close,
                )
            )

        return adjusted_prices

    def _calculate_split_adjusted_prices_ohlc(
        self,
        prices: list[HistoricalEndOfDayPricing],
        splits: list[Split],
    ) -> list[EODSplitAdjustedPricing]:
        """Calculate split-adjusted OHLCV prices.

        Args:
            prices: List of historical pricing data
            splits: List of stock splits

        Returns:
            List of EODSplitAdjustedPricing with split-adjusted OHLCV data
        """
        if not prices:
            return []

        # Sort data by date (oldest first) - always sort for consistency
        sorted_prices = sorted(prices, key=lambda p: p.date)

        # If no splits, just convert to EODSplitAdjustedPricing
        if not splits:
            return [
                EODSplitAdjustedPricing(
                    date=price.date,
                    open=price.open,
                    high=price.high,
                    low=price.low,
                    close=price.close,
                    volume=price.volume,
                    adjusted_close=price.adjusted_close,
                )
                for price in sorted_prices
            ]
        sorted_splits = sorted(splits, key=lambda s: s.date)

        adjusted_prices: list[EODSplitAdjustedPricing] = []

        for price in sorted_prices:
            # Find all splits that occurred AFTER this price date
            future_splits = [s for s in sorted_splits if s.date > price.date]

            # Calculate cumulative split ratio
            cumulative_ratio = Decimal("1.0")
            for split in future_splits:
                cumulative_ratio *= split.get_split_ratio()

            # Adjust all price fields (divide by ratio) and volume (multiply by ratio)
            adjusted_prices.append(
                EODSplitAdjustedPricing(
                    date=price.date,
                    open=price.open / cumulative_ratio,
                    high=price.high / cumulative_ratio,
                    low=price.low / cumulative_ratio,
                    close=price.close / cumulative_ratio,
                    volume=int(price.volume * cumulative_ratio),
                    adjusted_close=price.adjusted_close / cumulative_ratio,
                )
            )

        return adjusted_prices
