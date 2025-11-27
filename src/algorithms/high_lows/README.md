# High/Low and Rebound Algorithm Implementation

## Algorithm Details

### Pattern Lifecycle

1. **High Start (H_S)**: Peak price before a drop
2. **Low Threshold (L_T)**: First price ≤ high_start × (1 - threshold)
   - Triggers when: `price <= high_start * (1 - 0.20)` for 20% threshold
3. **Lowest (L)**: Actual lowest point after low threshold
4. **High Threshold (H_T)**: Recovery point = lowest × (1 + threshold)
   - Triggers when: `price >= lowest * (1 + 0.20)` for 20% threshold
   - **Pattern spawns** at this point (new pattern starts)
5. **Rebound (R)**: Price returns to high_start (PATTERN COMPLETE)
   - Pattern moves from `lows` table to `rebounds` table

### Key Features

- **Multiple Thresholds**: Each ticker has patterns at 15%, 20%, 25%, etc.
- **Pattern Spawning**: When a pattern hits high_threshold, a new pattern begins
- **Expiration**: Patterns expire after 800 days from low_threshold_date
- **Precision**: Prices stored as BIGINT × 1,000,000 (penny = 10,000)

