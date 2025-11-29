# Proposed Field Additions for Low High Pattern Models

This document outlines additional fields to enhance the Low High pattern tracking for real-time trading, historical analysis, and machine learning applications.

---

## Derived Immediately

These fields can be calculated on-demand from existing model data without additional processing or historical data.

### Percentage Gain/Loss Metrics

```python
pct_gain_ls_to_h: Decimal | None        # % gain from low_start to highest
                                         # Formula: ((highest_price - low_start_price) / low_start_price) * 100

pct_decline_h_to_lt: Decimal | None     # % decline from highest to low_threshold
                                         # Formula: ((highest_price - low_threshold_price) / highest_price) * 100

pct_recovery_lt_to_r: Decimal | None    # % recovery from low_threshold to reversal
                                         # Formula: ((reversal_price - low_threshold_price) / low_threshold_price) * 100

total_pct_change: Decimal | None        # Net % change from low_start to reversal
                                         # Formula: ((reversal_price - low_start_price) / low_start_price) * 100
```

### Duration Metrics

```python
total_pattern_days: int | None          # Total days from low_start to reversal/current
                                         # Formula: (reversal_date - low_start_date).days

days_to_peak: int | None                # Days from low_start to highest (uptrend speed)
                                         # Formula: (highest_date - low_start_date).days

days_peak_to_bottom: int | None         # Days from highest to low_threshold (decline speed)
                                         # Formula: (low_threshold_date - highest_date).days

days_to_recovery: int | None            # Days from low_threshold to reversal (recovery speed)
                                         # Formula: (reversal_date - low_threshold_date).days

avg_daily_movement_pct: Decimal | None  # Average % movement per day
                                         # Formula: total_pct_change / total_pattern_days
```

### Pattern Ratios

```python
highest_to_ls_ratio: Decimal | None     # highest_price / low_start_price
                                         # Indicates total upside capture

lt_to_ls_ratio: Decimal | None          # low_threshold_price / low_start_price
                                         # Indicates how far pattern recovered before decline
```

### Pattern State (for Active Patterns - High model only)

```python
distance_from_reversal_pct: Decimal | None  # % away from completion (reversal at low_start)
                                             # Formula: ((current_price - low_start_price) / current_price) * 100

days_since_last_update: int | None      # Days since last price update
                                         # Formula: (today - last_updated).days
```

### Quality Indicators (Derivable from Stored Data)

```python
threshold_exceeded_pct_ht: Decimal | None   # How far past high_threshold at peak
                                             # Formula: (highest_price / high_threshold_price) - 1

threshold_exceeded_pct_lt: Decimal | None   # How far past low_threshold at bottom
                                             # Formula: (low_threshold_price / highest_price) - threshold
```

---

## Derived with Script

These fields require tracking during pattern processing, accumulation over time, or access to full price history. They should be updated in the processor logic or calculated via separate scripts with historical data.

### Lifecycle Tracking (Set During Processing)

```python
created_at: datetime                    # Timestamp when pattern first detected
                                         # Set: When pattern object first created

updated_at: datetime                    # Last modification timestamp
                                         # Set: On every price update in processor

price_updates_count: int                # Number of price points processed
                                         # Set: Increment on each price update in processor
```

### Pattern Quality (Tracked During Processing)

```python
number_of_resets: int                   # Times pattern reset (went above highest after hitting LT)
                                         # Set: Increment in processor when price >= highest after low_threshold set

max_threshold_overshoot_ht: Decimal | None  # Maximum overshoot of high_threshold observed
                                             # Set: Track max(price / high_threshold_price) during pattern

max_threshold_overshoot_lt: Decimal | None  # Maximum overshoot of low_threshold observed
                                             # Set: Track min(price / lowest_price) during pattern
```

### Cached Calculations (Updated During Processing for Query Performance)

```python
# These CAN be derived immediately, but storing them improves database query performance

cached_total_pattern_days: int | None       # Pre-calculated for fast filtering
cached_pct_gain_ls_to_h: Decimal | None     # Pre-calculated for fast filtering
cached_pct_decline_h_to_lt: Decimal | None  # Pre-calculated for fast filtering
```

### Advanced Analytics (Requires Full Price History)

These require a complete price history array and should be calculated via a separate analytics script, not in real-time processing.

```python
price_volatility: Decimal               # Standard deviation of prices during pattern
                                         # Requires: Full array of prices between low_start_date and reversal_date

max_single_day_gain_pct: Decimal        # Largest 1-day % gain during pattern
                                         # Requires: Day-over-day price comparisons for all dates

max_single_day_loss_pct: Decimal        # Largest 1-day % loss during pattern
                                         # Requires: Day-over-day price comparisons for all dates

directional_consistency: Decimal        # Measure of trend smoothness (0-1)
                                         # Requires: Analysis of price direction changes

consolidation_days: int                 # Days spent near thresholds (±2%)
                                         # Requires: Full price history to count consolidation periods

whipsaw_count: int                      # Number of false breakouts/trend reversals
                                         # Requires: Full price history to detect reversals

price_range_pct: Decimal                # (highest - lowest) / low_start * 100
                                         # Derivable immediately, but listed here for completeness

time_above_ht_pct: Decimal             # % of pattern time spent above high_threshold
                                         # Requires: Full price history to calculate time percentages

time_below_lt_pct: Decimal             # % of pattern time spent below low_threshold
                                         # Requires: Full price history to calculate time percentages
```

---

## Implementation Notes

### Derived Immediately Fields
- Can be added to `LowHighDerivedData` TypedDict
- Calculated in `get_derived_data()` method
- No database storage needed
- Fast to compute from existing fields

### Derived with Script Fields

**Lifecycle & Quality Tracking:**
- Add to model dataclasses as stored fields
- Update in `processor.py` during pattern processing
- Requires database migration
- Enables real-time quality filtering

**Cached Calculations:**
- Optional: Store in DB to improve query performance
- Trade-off: Storage space vs. query speed
- Update whenever pattern state changes

**Advanced Analytics:**
- Create separate `get_advanced_analytics(price_history: list[DatePrice])` method
- Call only when needed for ML/deep analysis
- Not suitable for real-time processing (expensive computation)
- Consider batch processing for historical patterns

---

## Recommended Priority

**Phase 1 - Essential (Derived Immediately):**
- All percentage metrics
- All duration metrics
- Pattern ratios

**Phase 2 - Production Tracking (Derived with Script - Processing):**
- Lifecycle tracking (created_at, updated_at, price_updates_count)
- Pattern quality (number_of_resets, max overshoots)

**Phase 3 - Performance Optimization (Derived with Script - Cached):**
- Cached calculations for frequently queried fields

**Phase 4 - Advanced Analytics (Derived with Script - Historical):**
- Volatility and statistical measures
- Only if needed for ML model features
