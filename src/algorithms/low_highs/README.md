# Low/High and Reversal Algorithm Implementation

## Algorithm Details

### Pattern Lifecycle

1. **Low Start (L_S)**: Trough price before a rise
2. **High Threshold (H_T)**: First price ≥ low_start × (1 + threshold)
   - Triggers when: `price >= low_start * (1 + 0.20)` for 20% threshold
3. **Highest (H)**: Actual highest point after high threshold
4. **Low Threshold (L_T)**: Decline point = highest / (1 + threshold)
   - Triggers when: `price <= highest / (1 + 0.20)` for 20% threshold
   - **Pattern spawns** at this point (new pattern starts)
5. **Reversal (R)**: Price returns to low_start (PATTERN COMPLETE)
   - Pattern moves from `highs` table to `reversals` table

### Key Features

- **Multiple Thresholds**: Each ticker has patterns at 15%, 20%, 25%, etc.
- **Pattern Spawning**: When a pattern hits low_threshold, a new pattern begins
- **Expiration**: Patterns expire after 800 days from high_threshold_date
- **Precision**: Prices stored as BIGINT × 1,000,000 (penny = 10,000)
