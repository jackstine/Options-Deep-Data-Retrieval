"""High/Low pattern processor - core algorithm logic.

This module contains the state machine logic for processing price patterns.
It is ported from the old_repo implementation.

Pattern States:
1. Searching for low_threshold: Price drops by threshold% from high_start
2. Tracking lowest: Price continues to fall after low_threshold
3. Waiting for high_threshold: Price recovers by threshold% from lowest
4. Waiting for rebound: Price returns to high_start (pattern completes)

Key Behaviors:
- Pattern spawning: When price hits high_threshold, a new pattern can spawn
- Lowest tracking: If price drops below lowest after hitting high_threshold, reset
- Rebound completion: When price >= high_start, pattern moves to rebounds table
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.models.date_price import DatePrice
from src.algorithms.high_lows.models.low import Low
from src.algorithms.high_lows.models.rebound import Rebound

logger = logging.getLogger(__name__)


@dataclass
class ProcessedPatterns:
	"""Result of processing patterns."""

	active_lows: list[Low]
	completed_rebounds: list[Rebound]


def process_high_low_patterns(
	current_patterns: list[Low],
	new_prices: list[DatePrice],
	threshold: Decimal,
) -> ProcessedPatterns:
	"""Process high/low patterns with new price data.

	This is the core algorithm that updates pattern states based on new price data.
	Logic is ported from old_repo/src/appLogic/algorithms/HighLow/logic/process.py

	Key behaviors:
	- Spawned patterns process remaining prices in the same call
	- Patterns that rebound without spawning create new pattern at rebound price
	- Multiple rebounds can occur in a single processing call

	Args:
		current_patterns: List of existing Low patterns to update
		new_prices: List of new DatePrice data to process (should be chronological)
		threshold: Threshold as decimal (e.g., Decimal("0.20") for 20%)

	Returns:
		ProcessedPatterns with updated active lows and any completed rebounds

	Algorithm:
	-----------
	For each price (chronologically), update all active patterns:

	State 1: Searching for low_threshold (low_threshold is None)
		- If price <= high_start * (1 - threshold):
			Set low_threshold = price
			Set lowest = price
		- Elif price > high_start:
			Update high_start = price (still looking for peak)

	State 2: Tracking lowest (low_threshold set, high_threshold is None)
		- If price >= lowest * (1 + threshold):
			Set high_threshold = price
			Spawn new pattern if not already spawned
			If price >= high_start, set rebound (COMPLETE)
		- Elif price <= lowest:
			Update lowest = price

	State 3: Waiting for rebound (high_threshold set, rebound is None)
		- If price >= high_start:
			Set rebound = price (PATTERN COMPLETE)
			Create new pattern at rebound if didn't spawn
		- Elif price <= lowest:
			Update lowest = price
			Clear high_threshold (reset to State 2)
	"""
	completed_rebounds: list[Rebound] = []

	# Ensure prices are sorted chronologically
	sorted_prices = sorted(new_prices, key=lambda p: p.date)

	# Track currently active patterns (starts with input patterns)
	currently_active: list[Low] = list(current_patterns)

	# Process each price with all active patterns
	for price_data in sorted_prices:
		# Track changes during this price
		completed_this_round: list[Low] = []
		new_patterns: list[Low] = []

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

			# STATE 1: Searching for low_threshold
			if pattern.low_threshold_price is None:
				# Check if price dropped by threshold
				if price <= pattern.high_start_price * (Decimal("1") - threshold):
					pattern.low_threshold_price = price
					pattern.low_threshold_date = price_data.date
					pattern.lowest_price = price
					pattern.lowest_date = price_data.date
					logger.debug(
						f"Pattern {pattern.id or 'new'}: Low threshold reached at {price}"
					)

				# Or if price exceeded high_start, update the peak
				elif price > pattern.high_start_price:
					pattern.high_start_price = price
					pattern.high_start_date = price_data.date
					logger.debug(
						f"Pattern {pattern.id or 'new'}: New high start at {price}"
					)

			# STATE 2: Tracking lowest, waiting for high_threshold
			elif pattern.high_threshold_price is None:
				if pattern.lowest_price is None:
					raise ValueError(f"must have lowest_price set for {pattern.id}")
				# Check if price recovered by threshold
				if price >= pattern.lowest_price * (Decimal("1") + threshold):
					pattern.high_threshold_price = price
					pattern.high_threshold_date = price_data.date
					pattern.number_of_high_thresholds += 1
					logger.debug(
						f"Pattern {pattern.id or 'new'}: High threshold reached at {price} "
						f"(count={pattern.number_of_high_thresholds})"
					)

					# Spawn new pattern if not already spawned
					if not pattern.spawned:
						new_pattern = Low(
							ticker_history_id=pattern.ticker_history_id,
							threshold=threshold,
							high_start_price=price,
							high_start_date=price_data.date,
							last_updated=price_data.date,
						)
						new_patterns.append(new_pattern)
						pattern.spawned = True
						logger.debug(
							f"Pattern {pattern.id or 'new'}: Spawned new pattern"
						)

					# Check if this is also a rebound (price >= high_start)
					if price >= pattern.high_start_price:
						# Pattern is complete!
						rebound = _create_rebound_from_low(pattern, price, price_data.date)
						completed_rebounds.append(rebound)
						completed_this_round.append(pattern)
						logger.debug(
							f"Pattern {pattern.id or 'new'}: Completed rebound at {price}"
						)
						# Already spawned above, don't create another pattern
						continue  # Move to next pattern

				# Or if price continued to fall, update lowest
				elif price <= pattern.lowest_price:
					pattern.lowest_price = price
					pattern.lowest_date = price_data.date
					logger.debug(
						f"Pattern {pattern.id or 'new'}: New lowest at {price}"
					)

			# STATE 3: Waiting for rebound
			else:  # high_threshold is set
				if pattern.lowest_price is None:
					raise ValueError(f"must have lowest_price set for {pattern.id}")
				# Check if price returned to high_start (REBOUND!)
				if price >= pattern.high_start_price:
					# Pattern is complete!
					rebound = _create_rebound_from_low(pattern, price, price_data.date)
					completed_rebounds.append(rebound)
					completed_this_round.append(pattern)
					logger.debug(
						f"Pattern {pattern.id or 'new'}: Completed rebound at {price}"
					)

					# Create new pattern at rebound if didn't spawn
					if not pattern.spawned:
						new_pattern = Low(
							ticker_history_id=pattern.ticker_history_id,
							threshold=threshold,
							high_start_price=price,
							high_start_date=price_data.date,
							last_updated=price_data.date,
						)
						new_patterns.append(new_pattern)
						logger.debug(
							f"Pattern {pattern.id or 'new'}: Created new pattern at rebound price {price}"
						)

					continue  # Move to next pattern

				# Or if price fell below lowest, reset high_threshold
				elif price <= pattern.lowest_price:
					pattern.lowest_price = price
					pattern.lowest_date = price_data.date
					pattern.high_threshold_price = None
					pattern.high_threshold_date = None
					logger.debug(
						f"Pattern {pattern.id or 'new'}: Fell below lowest, reset high threshold"
					)

		# Update active patterns list after processing this price
		for pattern in completed_this_round:
			currently_active.remove(pattern)
		currently_active.extend(new_patterns)

	# Remaining patterns are still active
	active_lows = currently_active

	return ProcessedPatterns(
		active_lows=active_lows, completed_rebounds=completed_rebounds
	)


def _create_rebound_from_low(low: Low, rebound_price: Decimal, rebound_date: date) -> Rebound:
	"""Create a Rebound from a completed Low pattern.

	Args:
		low: The completed Low pattern
		rebound_price: Price at which rebound occurred
		rebound_date: Date of rebound

	Returns:
		Rebound instance

	Raises:
		ValueError: If Low pattern is missing required fields
	"""
	if (
		low.low_threshold_price is None
		or low.low_threshold_date is None
		or low.lowest_price is None
		or low.lowest_date is None
		or low.high_threshold_price is None
		or low.high_threshold_date is None
	):
		raise ValueError("Cannot create rebound from incomplete low pattern")

	return Rebound(
		ticker_history_id=low.ticker_history_id,
		threshold=low.threshold,
		high_start_price=low.high_start_price,
		high_start_date=low.high_start_date,
		low_threshold_price=low.low_threshold_price,
		low_threshold_date=low.low_threshold_date,
		lowest_price=low.lowest_price,
		lowest_date=low.lowest_date,
		high_threshold_price=low.high_threshold_price,
		high_threshold_date=low.high_threshold_date,
		rebound_price=rebound_price,
		rebound_date=rebound_date,
		number_of_high_thresholds=low.number_of_high_thresholds,
	)
