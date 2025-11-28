"""Low/High pattern processor - core algorithm logic.

This module contains the state machine logic for processing price patterns.
It is a mirror of the high_low implementation with inverted logic.

Pattern States:
1. Searching for high_threshold: Price rises by threshold% from low_start
2. Tracking highest: Price continues to rise after high_threshold
3. Waiting for low_threshold: Price declines by threshold% from highest
4. Waiting for reversal: Price returns to low_start (pattern completes)

Key Behaviors:
- Pattern spawning: When price hits low_threshold, a new pattern can spawn
- Highest tracking: If price rises above highest after hitting low_threshold, reset
- Reversal completion: When price <= low_start, pattern moves to reversals table
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.models.date_price import DatePrice
from src.algorithms.low_highs.models.high import High
from src.algorithms.low_highs.models.reversal import Reversal

logger = logging.getLogger(__name__)


@dataclass
class ProcessedPatterns:
	"""Result of processing patterns."""

	active_highs: list[High]
	completed_reversals: list[Reversal]


def process_low_high_patterns(
	current_patterns: list[High],
	new_prices: list[DatePrice],
	threshold: Decimal,
) -> ProcessedPatterns:
	"""Process low/high patterns with new price data.

	This is the core algorithm that updates pattern states based on new price data.
	Logic is inverted from high_low implementation.

	Key behaviors:
	- Spawned patterns process remaining prices in the same call
	- Patterns that reverse without spawning create new pattern at reversal price
	- Multiple reversals can occur in a single processing call

	Args:
		current_patterns: List of existing High patterns to update
		new_prices: List of new DatePrice data to process (should be chronological)
		threshold: Threshold as decimal (e.g., Decimal("0.20") for 20%)

	Returns:
		ProcessedPatterns with updated active highs and any completed reversals

	Algorithm:
	-----------
	For each price (chronologically), update all active patterns:

	State 1: Searching for high_threshold (high_threshold is None)
		- If price >= low_start * (1 + threshold):
			Set high_threshold = price
			Set highest = price
		- Elif price < low_start:
			Update low_start = price (still looking for trough)

	State 2: Tracking highest (high_threshold set, low_threshold is None)
		- If price <= highest / (1 + threshold):
			Set low_threshold = price
			Spawn new pattern if not already spawned
			If price <= low_start, set reversal (COMPLETE)
		- Elif price >= highest:
			Update highest = price

	State 3: Waiting for reversal (low_threshold set, reversal is None)
		- If price <= low_start:
			Set reversal = price (PATTERN COMPLETE)
			Create new pattern at reversal if didn't spawn
		- Elif price >= highest:
			Update highest = price
			Clear low_threshold (reset to State 2)
	"""
	completed_reversals: list[Reversal] = []

	# Ensure prices are sorted chronologically
	sorted_prices = sorted(new_prices, key=lambda p: p.date)

	# Track currently active patterns (starts with input patterns)
	currently_active: list[High] = list(current_patterns)

	# Process each price with all active patterns
	for price_data in sorted_prices:
		# Track changes during this price
		completed_this_round: list[High] = []
		new_patterns: list[High] = []

		# Update each active pattern with this price
		for pattern in currently_active:
			# Skip if we've already processed this date
			if price_data.date <= pattern.last_updated:
				continue

			# Skip null prices
			if price_data.price is None:
				continue

			# Update last_updated date
			pattern.last_updated = price_data.date
			price = price_data.price

			# STATE 1: Searching for high_threshold
			if pattern.high_threshold_price is None:
				# Check if price rose by threshold
				if price >= pattern.low_start_price * (Decimal("1") + threshold):
					pattern.high_threshold_price = price
					pattern.high_threshold_date = price_data.date
					pattern.highest_price = price
					pattern.highest_date = price_data.date
					logger.debug(
						f"Pattern {pattern.id or 'new'}: High threshold reached at {price}"
					)

				# Or if price fell below low_start, update the trough
				elif price < pattern.low_start_price:
					pattern.low_start_price = price
					pattern.low_start_date = price_data.date
					logger.debug(
						f"Pattern {pattern.id or 'new'}: New low start at {price}"
					)

			# STATE 2: Tracking highest, waiting for low_threshold
			elif pattern.low_threshold_price is None:
				if pattern.highest_price is None:
					raise ValueError(f"must have highest_price set for {pattern.id}")
				# Check if price declined by threshold
				if price <= pattern.highest_price / (Decimal("1") + threshold):
					pattern.low_threshold_price = price
					pattern.low_threshold_date = price_data.date
					pattern.number_of_low_thresholds += 1
					logger.debug(
						f"Pattern {pattern.id or 'new'}: Low threshold reached at {price} "
						f"(count={pattern.number_of_low_thresholds})"
					)

					# Spawn new pattern if not already spawned
					if not pattern.spawned:
						new_pattern = High(
							ticker_history_id=pattern.ticker_history_id,
							threshold=threshold,
							low_start_price=price,
							low_start_date=price_data.date,
							last_updated=price_data.date,
						)
						new_patterns.append(new_pattern)
						pattern.spawned = True
						logger.debug(
							f"Pattern {pattern.id or 'new'}: Spawned new pattern"
						)

					# Check if this is also a reversal (price <= low_start)
					if price <= pattern.low_start_price:
						# Pattern is complete!
						reversal = _create_reversal_from_high(pattern, price, price_data.date)
						completed_reversals.append(reversal)
						completed_this_round.append(pattern)
						logger.debug(
							f"Pattern {pattern.id or 'new'}: Completed reversal at {price}"
						)
						# Already spawned above, don't create another pattern
						continue  # Move to next pattern

				# Or if price continued to rise, update highest
				elif price >= pattern.highest_price:
					pattern.highest_price = price
					pattern.highest_date = price_data.date
					logger.debug(
						f"Pattern {pattern.id or 'new'}: New highest at {price}"
					)

			# STATE 3: Waiting for reversal
			else:  # low_threshold is set
				if pattern.highest_price is None:
					raise ValueError(f"must have highest_price set for {pattern.id}")
				# Check if price returned to low_start (REVERSAL!)
				if price <= pattern.low_start_price:
					# Pattern is complete!
					reversal = _create_reversal_from_high(pattern, price, price_data.date)
					completed_reversals.append(reversal)
					completed_this_round.append(pattern)
					logger.debug(
						f"Pattern {pattern.id or 'new'}: Completed reversal at {price}"
					)

					# Create new pattern at reversal if didn't spawn
					if not pattern.spawned:
						new_pattern = High(
							ticker_history_id=pattern.ticker_history_id,
							threshold=threshold,
							low_start_price=price,
							low_start_date=price_data.date,
							last_updated=price_data.date,
						)
						new_patterns.append(new_pattern)
						logger.debug(
							f"Pattern {pattern.id or 'new'}: Created new pattern at reversal price {price}"
						)

					continue  # Move to next pattern

				# Or if price rose above highest, reset low_threshold
				elif price >= pattern.highest_price:
					pattern.highest_price = price
					pattern.highest_date = price_data.date
					pattern.low_threshold_price = None
					pattern.low_threshold_date = None
					logger.debug(
						f"Pattern {pattern.id or 'new'}: Rose above highest, reset low threshold"
					)

		# Update active patterns list after processing this price
		for pattern in completed_this_round:
			currently_active.remove(pattern)
		currently_active.extend(new_patterns)

	# Remaining patterns are still active
	active_highs = currently_active

	return ProcessedPatterns(
		active_highs=active_highs, completed_reversals=completed_reversals
	)


def _create_reversal_from_high(high: High, reversal_price: Decimal, reversal_date: date) -> Reversal:
	"""Create a Reversal from a completed High pattern.

	Args:
		high: The completed High pattern
		reversal_price: Price at which reversal occurred
		reversal_date: Date of reversal

	Returns:
		Reversal instance

	Raises:
		ValueError: If High pattern is missing required fields
	"""
	if (
		high.high_threshold_price is None
		or high.high_threshold_date is None
		or high.highest_price is None
		or high.highest_date is None
		or high.low_threshold_price is None
		or high.low_threshold_date is None
	):
		raise ValueError("Cannot create reversal from incomplete high pattern")

	return Reversal(
		ticker_history_id=high.ticker_history_id,
		threshold=high.threshold,
		low_start_price=high.low_start_price,
		low_start_date=high.low_start_date,
		high_threshold_price=high.high_threshold_price,
		high_threshold_date=high.high_threshold_date,
		highest_price=high.highest_price,
		highest_date=high.highest_date,
		low_threshold_price=high.low_threshold_price,
		low_threshold_date=high.low_threshold_date,
		reversal_price=reversal_price,
		reversal_date=reversal_date,
		number_of_low_thresholds=high.number_of_low_thresholds,
	)
