# Additional Derived Data Fields for High Low Patterns

This document outlines suggested additional fields for the HighLowDerivedData TypedDict to enhance analytical capabilities and trading signal quality.

---

## Derived Immediately

Fields that can be calculated at the time of pattern computation using only the existing pattern data (dates, prices, thresholds).

### Price Change Percentages

**1. pct_hs_to_lt: float | None**
- Percentage drop from high_start to low_threshold
- Formula: `((lt_price - hs_price) / hs_price) * 100`
- Use: Validates threshold crossing and measures initial decline severity
- Example: -15.5 (dropped 15.5% to hit low threshold)

**2. pct_hs_to_l: float | None**
- Percentage drop from high_start to lowest point
- Formula: `((l_price - hs_price) / hs_price) * 100`
- Use: Measures maximum drawdown of the pattern
- Example: -22.3 (max drop was 22.3%)

**3. pct_l_to_r: float | None**
- Percentage rebound from lowest to rebound
- Formula: `((r_price - l_price) / l_price) * 100`
- Use: Measures recovery strength from the bottom
- Example: 12.8 (recovered 12.8% from lowest)
- Note: Only available for rebound patterns

**4. pct_lt_to_r: float | None**
- Percentage gain from low_threshold to rebound
- Formula: `((r_price - lt_price) / lt_price) * 100`
- Use: Measures trading strategy performance (if entering at low threshold)
- Example: 8.5 (8.5% gain from threshold entry)
- Note: Only available for rebound patterns

**5. pct_ht_to_r: float | None**
- Percentage from high_threshold to rebound
- Formula: `((r_price - ht_price) / ht_price) * 100`
- Use: Measures rebound momentum relative to exit threshold
- Example: 2.1 (rebound is 2.1% above high threshold)
- Note: Only available for rebound patterns

### Duration Metrics

**6. total_pattern_days: int**
- Total days from high_start to rebound (or to current date if incomplete)
- Formula:
  - For rebound: `days_between(high_start_date, rebound_date)`
  - For low: `days_between(high_start_date, today)`
- Use: Overall pattern duration for performance analysis

**7. days_in_low_zone: int | None**
- Days spent below low_threshold before rebound
- Formula: `days_between(low_threshold_date, rebound_date)`
- Use: Measures how long the stock remained "on sale"
- Note: For lows, this would be `days_since_lt`

**8. days_recovering: int | None**
- Days from lowest point to rebound
- Formula: `days_between(lowest_date, rebound_date)`
- Use: Measures recovery speed
- Note: Only available for rebound patterns

### Pattern Quality Indicators

**9. low_depth_ratio: float | None**
- How deep the low went relative to the threshold crossing
- Formula: `(hs_price - l_price) / (hs_price - lt_price)`
- Use: Values >1.0 indicate overshooting the threshold, closer to 1.0 is cleaner
- Example: 1.45 means the drop was 45% deeper than the threshold

**10. rebound_strength_ratio: float | None**
- Rebound recovery relative to initial drop
- Formula: `pct_l_to_r / abs(pct_hs_to_l)`
- Use: Measures how much of the drop was recovered
- Example: 0.57 means recovered 57% of the total drop
- Note: Only available for rebound patterns

**11. pattern_symmetry: float | None**
- Ratio of time spent dropping vs recovering
- Formula: `days_between(hs_date, l_date) / days_between(l_date, r_date)`
- Use: Indicates pattern shape (symmetric, V-bottom, gradual recovery)
- Example: 2.0 means drop took twice as long as recovery
- Note: Only available for rebound patterns

### Risk/Confidence Metrics

**12. days_remaining_to_expiration: int | None**
- Days left before pattern expires (for active lows only)
- Formula: `EXPIRED_DAYS_OUT - days_since_lt`
- Use: Urgency indicator for active low patterns
- Note: Only relevant for incomplete patterns

**13. expiration_risk_pct: float | None**
- Percentage of expiration window already used
- Formula: `(days_since_lt / EXPIRED_DAYS_OUT) * 100`
- Use: Risk that pattern will expire without rebounding
- Example: 75.0 means 75% of time window used
- Note: Only relevant for incomplete patterns

**14. price_stability_at_low: bool | None**
- Whether lowest and low_threshold prices are close (stable bottom)
- Formula: `abs(pct_hs_to_l - pct_hs_to_lt) < 2.0` (within 2%)
- Use: Indicates clean low threshold crossing vs volatile bottom
- Example: True means the low was stable near threshold

### Practical Trading Metrics

**15. roi_at_lowest: float | None**
- Return on investment if bought at lowest vs rebound price
- Formula: `((r_price - l_price) / l_price) * 100`
- Use: Best-case scenario profitability
- Example: 12.8 (same as pct_l_to_r)
- Note: Only available for rebound patterns

**16. roi_at_lt: float | None**
- Return on investment if bought at low_threshold vs rebound price
- Formula: `((r_price - lt_price) / lt_price) * 100`
- Use: Realistic entry strategy profitability
- Example: 8.5 (same as pct_lt_to_r)
- Note: Only available for rebound patterns

**17. max_favorable_excursion: float | None**
- Best price movement from entry (low_threshold) to lowest
- Formula: `((lt_price - l_price) / lt_price) * 100`
- Use: How much better you could have done timing the bottom
- Example: -5.2 (price went 5.2% lower after threshold)

**18. max_adverse_excursion: float | None**
- Worst drawdown from entry point before rebound
- Formula: Same as max_favorable_excursion for lows
- Use: Risk management - maximum unrealized loss
- Note: For rebound patterns, this would be 0 or the drawdown before recovery

---

## Derived with Script

Fields that require historical data analysis, batch processing, or comparison against other patterns. These should be computed in a separate pipeline/script.

### Comparative Metrics (Require Historical Database Queries)

**19. percentile_drop: float | None**
- Where this drop ranks among historical drops for this ticker
- Requires: Query all historical high_low patterns for same ticker
- Formula: Percentile rank of `pct_hs_to_l` among all patterns
- Use: Context for how significant this drop is
- Example: 85.0 means this drop was larger than 85% of historical drops

**20. percentile_recovery: float | None**
- Where this recovery ranks among historical recoveries for this ticker
- Requires: Query all historical rebound patterns for same ticker
- Formula: Percentile rank of `pct_l_to_r` among all rebounds
- Use: Context for recovery strength
- Example: 65.0 means this recovery was stronger than 65% of historical rebounds
- Note: Only available for rebound patterns

**21. avg_days_to_rebound_for_ticker: float | None**
- Historical average days from low_threshold to rebound for this ticker
- Requires: Aggregate query across all completed patterns for ticker
- Use: Set expectations for current incomplete patterns
- Example: 18.5 (historically takes ~18.5 days to rebound)

**22. ticker_pattern_success_rate: float | None**
- Percentage of low patterns that successfully rebounded vs expired
- Requires: Count completed vs expired patterns for ticker
- Formula: `(rebound_count / (rebound_count + expired_count)) * 100`
- Use: Confidence in pattern completion
- Example: 72.5 (72.5% of lows historically rebounded)

### Trading Signal Fields (Require ML or Statistical Analysis)

**23. buy_signal_strength: float | None**
- Composite score for entry signal quality (0-100)
- Requires: Machine learning model or weighted scoring algorithm
- Factors: depth, time in low zone, ticker success rate, market conditions
- Use: Automated trading signal ranking
- Example: 78.5 (strong buy signal)

**24. false_low_risk: float | None**
- Probability that pattern will expire without rebounding (0-100)
- Requires: ML model trained on completed/expired patterns
- Factors: expiration_risk_pct, ticker success rate, pattern quality
- Use: Risk assessment for entries
- Example: 35.0 (35% chance of failure)

**25. profit_potential: float | None**
- Expected return based on historical similar patterns
- Requires: Query historical patterns with similar characteristics
- Formula: Average `pct_lt_to_r` for similar patterns
- Use: Expected value calculation
- Example: 9.2 (expect ~9.2% return based on history)

### Volatility Metrics (Require Time-Series Price Data)

**26. pattern_volatility: float | None**
- Standard deviation of daily returns during the pattern period
- Requires: Query all daily prices between high_start and rebound/now
- Use: Indicates pattern stability vs choppiness
- Example: 0.025 (2.5% average daily volatility)

**27. intrapattern_trend: str | None**
- Trend characterization during the low phase
- Requires: Regression analysis of prices during low zone
- Values: "steady_decline", "choppy", "gradual_recovery", "v_bottom"
- Use: Pattern type classification
- Example: "v_bottom" (sharp drop and quick recovery)

---

## Implementation Priority

### Phase 1 (Immediate Value)
Start with **Price Change Percentages** (1-5) and **Practical Trading Metrics** (15-18):
- Easy to calculate
- Directly useful for evaluating profitability
- Required for most other metrics

### Phase 2 (Pattern Analysis)
Add **Duration Metrics** (6-8) and **Pattern Quality Indicators** (9-11):
- Enhance pattern understanding
- Support strategy optimization

### Phase 3 (Risk Management)
Implement **Risk/Confidence Metrics** (12-14):
- Help prioritize active lows
- Support position sizing

### Phase 4 (Historical Context)
Create batch processing for **Comparative Metrics** (19-22) and **Volatility Metrics** (26-27):
- Requires separate pipeline
- Updates periodically, not real-time

### Phase 5 (Advanced Signals)
Develop **Trading Signal Fields** (23-25):
- Requires ML infrastructure
- Most complex but highest potential value
