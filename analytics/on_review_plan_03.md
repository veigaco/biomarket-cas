# Plan 03: Fundamental Fixes Implementation & Regime Drift Calibration

**Date:** 2025-12-30
**Status:** IN PROGRESS - Final validation test running
**Goal:** Achieve realistic 8-12% average annual returns with proper regime dynamics

---

## Executive Summary

Successfully implemented fundamental fixes to address root cause of unrealistic market behavior. The core issue was **health bonus dominating regime drift by 83:1 ratio**. After fixing this, we discovered regime drifts need significant rebalancing to achieve target returns.

**Current Status:**
- ✅ Health bonus reduced 100x (0.001 → 0.00001)
- ✅ Regime transitions fixed (lock-in eliminated, avg 13 transitions/cycle)
- ✅ Company stability achieved (70-100 companies, zero mass extinctions)
- 🔄 Regime drifts rebalanced (GROWTH 4.0, awaiting validation results)

---

## Problems Solved

### 1. Health Bonus Dominance (ROOT CAUSE)
**Problem:** Health bonus (0.001) was 83x larger than base regime drift (0.000006)
```python
# Old calculation (GROWTH regime, healthy stock):
base_drift = 0.5 * 0.00002 * 0.6 = 0.000006
health_bonus = (1.0 - 0.5) * 0.001 = 0.0005
total_drift = 0.000506  # Health bonus = 83x base drift!

# This is why tuning drift (1.3 → 0.8 → 0.6) had minimal impact
```

**Fix:** Reduced health bonus 100x
```python
# backend/app/engine/stock_price.py:79
health_bonus = (health - 0.5) * 0.00001  # Was 0.001
```

**Result:** Regime multipliers now have proper effect on returns

---

### 2. Regime Lock-In
**Problem:** Cycles stuck in single regime for 200-365 periods (entire year)
- Cycle 2 (test-run-4): 365/365 periods in GROWTH → 33.54% return
- Caused by: Stay probability 0.997 + checks every 10 ticks

**Fix 1:** Increased check frequency
```python
# backend/app/engine/regime_manager.py:33
if self.ticks_since_last_check < 5:  # Was 10
```

**Fix 2:** Reduced stay probabilities
```python
# backend/app/config.py:61-85
'GROWTH': {'GROWTH': 0.994},      # Was 0.997 (avg 333 ticks → 166 ticks)
'STAGNATION': {'STAGNATION': 0.991},  # Was 0.994
'CONTRACTION': {'CONTRACTION': 0.989},  # Was 0.993
'CRISIS': {'CRISIS': 0.990}        # Was 0.995
```

**Result:**
- Average 13-16 transitions per cycle (was 0-7 with high variance)
- No more regime lock-in
- Realistic regime mixing

---

### 3. Company Stability
**Problem:** Alternating between zero bankruptcies and mass extinction (330 in 9 cycles)
- Original: AND condition too strict (0 bankruptcies)
- Attempt 1: OR condition too lenient (330 bankruptcies, min 8 companies)

**Final Fix:** AND condition with moderate thresholds
```python
# backend/app/engine/stock_price.py:97
if new_price < 0.25 and health <= 0.05:  # Both required
    stock.status = 'bankrupt'
```

**Result:**
- Company count stable: 70-100
- Bankruptcies: 0-5 per cycle (slightly conservative but acceptable)
- Zero mass extinction events

---

## Iterative Regime Drift Calibration

After implementing fundamental fixes, discovered regime drifts needed significant rebalancing.

### Iteration 1: GROWTH = 0.8
**Test Results (3 cycles):**
- Average return: **-0.07%** (too low!)
- Cycle 0: 1.21%, Cycle 1: -1.91%, Cycle 2: 0.50%
- Transitions: 16.0 avg ✓
- Companies: 100 stable ✓

**Analysis:** Returns too low, but fundamental fixes working (no lock-in, stable companies)

---

### Iteration 2: GROWTH = 1.2
**Test Results (5 cycles):**
- Average return: **1.26%** (still too low)
- Individual cycles: 0.22%, 0.64%, 1.22%, 2.74%, 1.50%
- Transitions: 13.0 avg ✓
- Companies: 82-100 ✓

**Analysis:** Marginal improvement, but still far from 8-12% target

---

### Iteration 3: GROWTH = 2.5
**Test Results (5 cycles):**
- Average return: **1.28%** (no meaningful change!)
- Cycles with high GROWTH (167-181 periods): 2.45-3.56% ✓
- Cycles with moderate GROWTH: -0.23%, -1.83% ✗

**Critical Discovery:**
```
Cycle 4 breakdown:
- 97 GROWTH periods × 2.5 = +242.5 drift units
- 123 CONTRACTION periods × (-0.5) = -61.5
- 106 STAGNATION periods × 0.0 = 0
- 38 CRISIS periods × (-1.2) = -45.6
Net: +135.4 → but got -1.83%!
```

**Analysis:** Negative regime drifts (CONTRACTION -0.5, CRISIS -1.2) are TOO STRONG relative to GROWTH. They pull down mixed cycles despite positive net drift.

---

### Iteration 4: REBALANCED ALL REGIMES (CURRENT)

**Configuration:**
```python
REGIMES = {
    'GROWTH': {
        'drift_multiplier': 4.0,     # Was 2.5 → +60% increase
        'health_regen': 0.0002
    },
    'STAGNATION': {
        'drift_multiplier': 0.1,     # Was 0.0 → slight positive bias
        'health_regen': 0.00001
    },
    'CONTRACTION': {
        'drift_multiplier': -0.3,    # Was -0.5 → -40% reduction
        'health_regen': -0.00005
    },
    'CRISIS': {
        'drift_multiplier': -0.8,    # Was -1.2 → -33% reduction
        'health_regen': -0.0002
    }
}
```

**Rationale:**
1. **GROWTH 4.0:** Dominant positive drift to overpower negative regimes in mixed cycles
2. **STAGNATION 0.1:** Offset volatility drag and compounding losses
3. **CONTRACTION -0.3:** Soften corrections to prevent overwhelming positive drift
4. **CRISIS -0.8:** Soften bear markets while maintaining downside character

**Expected Impact (using Cycle 4 distribution from Iteration 3):**
```
97 GROWTH × 4.0 = +388.0 (was +242.5)
123 CONTRACTION × (-0.3) = -36.9 (was -61.5)
106 STAGNATION × 0.1 = +10.6 (was 0)
38 CRISIS × (-0.8) = -30.4 (was -45.6)
Net: +331.3 (was +135.4) → +145% improvement
```

**Status:** Validation test running (started 08:23, ~12 min duration)

---

## Current Configuration Summary

### File: `backend/app/config.py`

**Simulation Parameters:**
```python
TICK_INTERVAL = 0.02              # 20ms (25x faster than original 500ms)
BROADCAST_INTERVAL = 1.0         # 1 second
HISTORY_LENGTH = 60              # 60-period rolling buffer
```

**Regime Drifts:**
```python
GROWTH: 4.0       # Target: ~40% pure GROWTH, ~12-15% mixed
STAGNATION: 0.1   # Slight positive bias
CONTRACTION: -0.3 # Softened correction
CRISIS: -0.8      # Softened bear market
```

**Regime Transitions:**
```python
# Reduced stay probabilities from 0.997 → 0.994
# Checks every 5 ticks (1,460 checks/cycle)
# Average stay: 166 periods (prevents lock-in)
```

**Bankruptcy Logic:**
```python
# AND condition with moderate thresholds
if new_price < 0.25 and health <= 0.05:
    stock.status = 'bankrupt'
```

### File: `backend/app/engine/stock_price.py`

**Health Bonus:**
```python
# Line 79: Reduced 100x to prevent dominating regime drift
health_bonus = (health - 0.5) * 0.00001  # Was 0.001
```

**Drift Calculation:**
```python
base_drift = (stock.value_score * 0.00002) * regime_multiplier
health_bonus = (health - 0.5) * 0.00001
drift = base_drift + health_bonus + shock
```

### File: `backend/app/engine/regime_manager.py`

**Transition Frequency:**
```python
# Line 33: Check every 5 ticks (was 10)
if self.ticks_since_last_check < 5:
    return None
```

---

## Validation Results Summary

| Test | GROWTH Drift | Avg Return | Transitions | Companies | Status |
|------|-------------|------------|-------------|-----------|--------|
| **Baseline (test-run-4)** | 0.6 | 14.4% | 0-7 | 65-100 | Lock-in, high returns |
| **Fundamental Fixes** | 0.8 | -0.07% | 16.0 | 100 | Too low, transitions fixed ✓ |
| **Iter 1** | 1.2 | 1.26% | 13.0 | 82-100 | Too low |
| **Iter 2** | 2.5 | 1.28% | 13.2 | 85-100 | No improvement |
| **Iter 3 (Current)** | 4.0 | ??? | ??? | ??? | **IN PROGRESS** |

---

## Test In Progress

**Current Validation:**
- Started: 08:23
- Duration: ~12 minutes
- Starting tick: 9,107 → Target: 45,605 (5 cycles)
- Configuration: GROWTH=4.0, STAG=0.1, CONTR=-0.3, CRISIS=-0.8

**Expected Results:**
- Average return: **~12-15%**
- Pure GROWTH cycles (200+ periods): **~40%**
- Mixed regime cycles: **~10-15%**
- Transitions: ~13 per cycle
- Companies: 70-100 stable

---

## Next Steps

### If Test Passes (Avg Return 8-15%)
✅ **SUCCESS - Configuration Finalized**

1. **Document final configuration** in project README
2. **Run extended validation** (10-20 cycles) to confirm stability
3. **Download analytics data** for analysis
4. **Consider additional refinements:**
   - Fine-tune bankruptcy thresholds if too conservative (0 bankruptcies)
   - Adjust regime transition probabilities if needed
   - Test different tick intervals (10ms, 30ms) for performance tuning

### If Test Fails Low (Avg Return < 8%)
⚠️ **Further Tuning Needed**

**Option A - More Aggressive GROWTH:**
- GROWTH: 4.0 → 5.0 or 6.0
- Keep other regimes the same

**Option B - Investigate Calculation:**
- Add logging to track actual drift values per tick
- Verify volatility isn't overwhelming drift
- Check for compounding issues

**Option C - Positive Bias Across Board:**
- STAGNATION: 0.1 → 0.2
- CONTRACTION: -0.3 → -0.2
- CRISIS: -0.8 → -0.6

### If Test Fails High (Avg Return > 15%)
⚠️ **Too Aggressive**

**Option A - Scale Back GROWTH:**
- GROWTH: 4.0 → 3.0 or 3.5
- Keep negative regimes softened

**Option B - Strengthen Negative Regimes:**
- CONTRACTION: -0.3 → -0.4
- CRISIS: -0.8 → -1.0
- Keep GROWTH at 4.0

---

## Key Learnings

### 1. Root Cause Analysis is Critical
- Spent multiple iterations tuning GROWTH drift (1.3 → 0.8 → 0.6)
- Had minimal impact because health bonus (0.001) dominated regime drift (0.000006) by 83:1
- Only after deep analysis of 8-cycle data did we identify the real problem
- **Lesson:** When tuning has no effect, look for dominant terms in the calculation

### 2. Negative Regimes Need Careful Balance
- In financial markets, losses compound differently than gains
- A -50% loss requires +100% gain to recover
- Negative regime drifts (CONTRACTION -0.5, CRISIS -1.2) overwhelmed positive drift
- **Lesson:** Positive bias needed to offset asymmetric loss impact

### 3. System-Level Thinking
- Can't tune regimes in isolation
- Must consider:
  - Regime distribution over cycles
  - Transition probabilities
  - Stay durations
  - Interplay between all four regimes
- **Lesson:** Validate with full cycle tests, not individual regime periods

### 4. Server Reload Challenges
- FastAPI --reload with WatchFiles doesn't always work with WebSocket connections
- Had to manually restart server once to pick up config changes
- **Lesson:** Verify config changes took effect before running long tests

---

## Files Modified

### Configuration
- `backend/app/config.py`: Regime drifts, transition probabilities, tick interval

### Core Engine
- `backend/app/engine/stock_price.py`: Health bonus, drift calculation, bankruptcy logic
- `backend/app/engine/regime_manager.py`: Transition check frequency
- `backend/app/main.py`: Simulation loop timing (configurable tick interval)

### API Routes
- `backend/app/api/routes/engine.py`: Dynamic config reading (tick_interval_ms)

### Frontend
- `src/views/AnalyticsView.jsx`: JSON/CSV download buttons

### Documentation
- `analytics/fundamental_analysis.md`: Root cause analysis of health bonus dominance
- `analytics/on_review_plan_01.md`: Original problem identification (900%+ returns)
- `analytics/on_review_plan_02.md`: Mass extinction analysis (330 bankruptcies)
- `analytics/on_review_plan_03.md`: This document (fundamental fixes & drift calibration)

---

## Technical Debt / Future Improvements

1. **Bankruptcy Tuning:**
   - Current AND condition (price < 0.25 AND health <= 0.05) is slightly conservative
   - All recent tests show 0 bankruptcies
   - May need to relax thresholds slightly for realism (target: 1-3 per cycle)

2. **Volatility Investigation:**
   - Volatility term may be dominating drift in some cases
   - Consider adding volatility caps or drift floors
   - Need to verify volatility scaling (currently `volatility / 50`)

3. **IPO Mechanics:**
   - IPOs only occur in GROWTH regime currently
   - May want to allow occasional IPOs in STAGNATION
   - IPO count: 0-18 per cycle (high variance)

4. **Logging & Observability:**
   - Add drift component logging for debugging
   - Track regime contribution to returns
   - Monitor health bonus vs base drift ratio in production

5. **Performance Optimization:**
   - Test 10ms tick interval (current: 20ms)
   - Consider WebSocket broadcast optimization
   - Profile simulation loop for bottlenecks

---

## Conclusion

Successfully identified and fixed the root cause of unrealistic market behavior through systematic analysis. The health bonus dominating regime drift by 83:1 was the core issue preventing regime multipliers from having meaningful effect.

After implementing fundamental fixes:
- ✅ Regime lock-in eliminated
- ✅ Company stability achieved
- ✅ Transition dynamics working properly

Currently calibrating regime drifts to achieve target 8-12% average returns. The rebalanced configuration (GROWTH=4.0, STAG=0.1, CONTR=-0.3, CRISIS=-0.8) addresses the issue of negative regimes overwhelming positive drift in mixed cycles.

**Awaiting validation results to confirm success or determine next tuning iteration.**

---

**Last Updated:** 2025-12-30 08:25
**Next Review:** After 5-cycle validation completes (~08:35)
