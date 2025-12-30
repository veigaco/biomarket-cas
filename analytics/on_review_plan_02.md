# 5-Cycle Validation Review: Post-Fix Analysis

**Date:** 2025-12-29
**Tick Interval:** 20ms
**Total Runtime:** ~13 minutes (5 complete cycles + 1 partial)

---

## Executive Summary

The fixes from Plan 01 **partially succeeded** but revealed new critical issues:

✅ **FIXED:**
- Extreme volatility reduced (no 900%+ cycles)
- Company survival excellent (81-100, no extinctions)
- VIX under control (max 72.74 vs 87)
- Some cycles show realistic returns (0.94%, -2.73%)

❌ **NEW PROBLEMS:**
- **Regime lock-in:** Cycles 3 & 4 stuck in GROWTH for 98-100% of periods
- **Returns too high:** Average ~20% (target: 8-12%), with Cycle 3 at 45.16%
- **Zero bankruptcies:** 0 across 5 cycles despite 19 IPOs (unrealistic)
- **GROWTH drift still too strong:** 1.3 multiplier produces excessive returns

---

## Detailed Cycle Breakdown

| Cycle | Return 365T | IPOs | Bankruptcies | Transitions | Min/Max Co | VIX (Med) | Regime Distribution |
|-------|-------------|------|--------------|-------------|------------|-----------|---------------------|
| **0** | **29.83%** ⚠️ | 4 | 0 | 3 ✅ | 81-85 | 19.15 | G:16 / S:229 / C:119 / Cr:0 |
| **1** | **0.94%** ✅ | 0 | 0 | 1 ⚠️ | 85-85 | 33.63 | G:0 / S:0 / C:178 / Cr:186 |
| **2** | **-2.73%** ✅ | 15 | 0 | 4 ✅ | 85-100 | 34.42 | G:95 / S:41 / C:0 / Cr:228 |
| **3** | **45.16%** ❌ | 0 | 0 | 0 ❌ | 100-100 | 15.25 | G:365 / S:0 / C:0 / Cr:0 |
| **4** | **25.27%** ⚠️ | 0 | 0 | 2 ✅ | 100-100 | 15.19 | G:358 / S:0 / C:7 / Cr:0 |

**Average Annual Return:** 19.70% (Target: 8-12%)

---

## Problem Analysis

### 1. GROWTH Regime Lock-In (CRITICAL)

**Observation:**
- Cycle 3: **365/365 periods in GROWTH** (100% - entire cycle)
- Cycle 4: **358/365 periods in GROWTH** (98.1%)
- Cycle 3: **0 regime transitions** (stuck for entire year)

**Root Cause:**
```python
# config.py line 61
'GROWTH': 0.997,  # 99.7% stay = avg 333 periods before transition
```

**Math:**
- Transition probability: 0.3% per period
- Average stay: 1 / 0.003 = **333 periods**
- Cycle length: **365 periods**
- **Problem:** Expected stay (333) ≈ cycle length (365)!

**Impact:**
- When stuck in GROWTH for entire cycle → returns compound to 45%+
- Makes market unrealistically stable (no bear markets)
- IPO mechanics only trigger in GROWTH (starves other regimes)

---

### 2. Excessive GROWTH Returns (HIGH)

**Observation:**
- Cycle 3 (pure GROWTH): +45.16%
- Cycle 4 (mostly GROWTH): +25.27%
- Cycle 0 (mixed): +29.83%

**Root Cause:**
```python
# config.py line 29
'drift_multiplier': 1.3,  # Target +10% annual
```

**Math Check:**
- Base drift: `value_score (0.5) * 0.00002 * 1.3 = 0.000013`
- Per tick: `e^0.000013 ≈ 1.000013`
- Over 7,300 ticks: `1.000013^7300 ≈ 1.104` → **+10.4%** ✅

**Why actual returns are higher:**
1. **Health bonus:** `(health - 0.5) * 0.001` adds extra drift when health > 0.5
   - With health at 1.0: bonus = 0.0005 (doubles the drift!)
2. **Volatility:** Even capped at ±1.5%, positive random walks compound
3. **No downward pressure:** Pure GROWTH has no offsetting forces

**Impact:**
- Intended 10% becomes 25-45% in pure GROWTH cycles
- Only cycles with CRISIS periods show realistic returns

---

### 3. Zero Bankruptcies (MEDIUM)

**Observation:**
- 5 complete cycles: **0 bankruptcies**
- 19 IPOs but 0 bankruptcies = perfect survival rate (unrealistic)
- Companies grew from 81 → 100 with no failures

**Root Cause:**
```python
# stock_price.py line 94
if new_price < 0.10 and health <= 0:  # BOTH conditions required
    stock.status = 'bankrupt'
```

**Analysis:**
1. **Price threshold too low:** $0.10 is extremely low
   - Stock would need to fall 99.9% from typical $80-120 IPO price
   - Even in CRISIS, this rarely happens with ±1.5% volatility cap

2. **AND condition too strict:** Requires BOTH low price AND zero health
   - Health regenerates in GROWTH (`health_regen: 0.0002`)
   - With 60-period lookback, even small gains restore health
   - Hard to hit zero health while price is also crashing

3. **Health system too generous:**
   ```python
   # Base cost reduced by 50% in Plan 01 (line 45-48)
   base_cost = (interest_rate / 5.0) * 0.0004 + (vix / 90.0) * 0.0005
   ```
   - In GROWTH (rate=0.75, VIX=15): cost = 0.00006 + 0.00008 = **0.00014**
   - In GROWTH: regen = **0.0002**
   - **Net gain:** +0.00006 per tick → health always regenerates!

**Impact:**
- No natural selection pressure
- Unrealistic correlation: 19 IPOs, 0 failures
- Market grows indefinitely without churn

---

### 4. Regime Transition Frequency (MEDIUM)

**Observation:**
- Cycle 3: 0 transitions (stuck)
- Cycle 1: 1 transition (low)
- Cycles 0,2,4: 2-4 transitions (acceptable)

**Root Cause:**
```python
# regime_manager.py line 33
if self.ticks_since_last_check < 20:  # Only check every 20 ticks
    return None
```

**Math:**
- Checks per cycle: 7,300 / 20 = **365 checks**
- Transition prob per check: 0.3% (GROWTH)
- Expected transitions: 365 * 0.003 = **1.1 transitions/cycle**

**Analysis:**
- Math says we should see ~1 transition per cycle on average
- Observed: 0-4 transitions (consistent with randomness)
- **Issue:** Variance is too high (0 in some cycles, 4 in others)
- Need more frequent checks to smooth out the randomness

---

### 5. Positive Findings ✅

**Company Count:**
- Min: 81 (no near-extinction events)
- Max: 100 (healthy growth)
- **Excellent stability** vs previous 5-8 minimums

**VIX Control:**
- Max: 72.74 (vs target <80)
- Median: 15-34 (reasonable range)
- **No extreme spikes** vs previous 87+

**Mixed Regime Cycles Perform Well:**
- Cycle 1 (CONTRACTION/CRISIS): 0.94% ✅
- Cycle 2 (mixed): -2.73% ✅
- **When regimes transition, returns are realistic**

---

## Root Cause Summary

### Primary Issues

1. **GROWTH drift multiplier (1.3) too strong**
   - Intended for 10% returns in mixed cycles
   - Produces 25-45% in pure GROWTH cycles
   - Health bonus doubles effective drift

2. **Regime stay probabilities too high**
   - 99.7% stay = 333-period average
   - Comparable to cycle length (365 periods)
   - Results in regime lock-in

3. **Bankruptcy conditions too strict**
   - Requires BOTH price < $0.10 AND health <= 0
   - Health regenerates faster than it decays in GROWTH
   - Price rarely drops to $0.10 with capped volatility

### Contributing Factors

4. **Health system too forgiving**
   - Base cost reduced too much (50% cut in Plan 01)
   - Regen > cost in GROWTH regime
   - 60-period lookback allows easy recovery

5. **Transition checks too infrequent**
   - Every 20 ticks = 365 checks per cycle
   - Creates high variance in transition counts (0-4)
   - Should check more frequently for smoother behavior

---

## Recommended Fixes (Plan 02)

### Phase 1: Reduce GROWTH Drift (CRITICAL)

**File:** `/backend/app/config.py`

**Change:**
```python
# Line 29 - Reduce GROWTH drift multiplier
'GROWTH': {
    'drift_multiplier': 0.8,    # Was: 1.3 → Target ~6% annual in pure GROWTH
    # ... rest unchanged
}
```

**Rationale:**
- Health bonus adds ~0.0005 drift (doubles base drift at health=1.0)
- Volatility random walk adds upward bias
- Target: 6% base → becomes ~10-12% with bonuses in pure GROWTH
- In mixed cycles (with STAGNATION/CONTRACTION): avg ~8%

---

### Phase 2: Increase Regime Transitions (HIGH)

**Option A: Check more frequently** (Recommended)

**File:** `/backend/app/engine/regime_manager.py`

**Change:**
```python
# Line 33 - Check every 10 ticks instead of 20
if self.ticks_since_last_check < 10:  # Was: 20
    return None
```

**Impact:**
- Checks per cycle: 7,300 / 10 = **730 checks** (was 365)
- Expected transitions (GROWTH): 730 * 0.003 = **2.2/cycle** (was 1.1)
- Reduces variance, smoother transitions
- Prevents 365-period lock-ins

**Option B: Reduce stay probabilities**

**File:** `/backend/app/config.py`

**Change:**
```python
# Lines 60-83 - Reduce all stay probabilities
REGIME_TRANSITIONS = {
    'GROWTH': {
        'GROWTH': 0.994,       # Was: 0.997 → avg 166 periods (was 333)
        'STAGNATION': 0.004,   # Was: 0.002
        'CONTRACTION': 0.002,  # Was: 0.001
        'CRISIS': 0.0
    },
    # ... similar reductions for other regimes
}
```

**Recommendation:** Use **Option A** (check frequency) first. Easier to tune, more predictable.

---

### Phase 3: Fix Bankruptcy Logic (HIGH)

**File:** `/backend/app/engine/stock_price.py`

**Change 1: Use OR instead of AND**
```python
# Line 94 - Either condition triggers bankruptcy
if new_price < 0.50 or health <= 0.1:  # Was: new_price < 0.10 and health <= 0
    stock.status = 'bankrupt'
```

**Rationale:**
- Raise price threshold: $0.10 → $0.50 (still very low, but more realistic)
- Change AND → OR (either condition can trigger)
- Raise health threshold: 0 → 0.1 (gives small buffer)

**Change 2: Increase health cost in GROWTH**
```python
# Line 45-48 - Increase base cost slightly
base_cost = (
    (market_state.interest_rate / 5.0) * 0.0006 +  # Was: 0.0004
    (market_state.vix / 90.0) * 0.0007              # Was: 0.0005
)
```

**Impact:**
- In GROWTH (rate=0.75, VIX=15): cost = 0.00009 + 0.00012 = **0.00021**
- With regen = 0.0002, net = **-0.00001** (slight decay)
- Creates bankruptcy pressure even in GROWTH
- Weak stocks will gradually fail

---

### Phase 4: Adjust Other Regime Drifts (MEDIUM)

**File:** `/backend/app/config.py`

**Change:**
```python
# Lines 37, 45, 53
'STAGNATION': {
    'drift_multiplier': 0.15,   # Was: 0.3 → Target 0% annual
},
'CONTRACTION': {
    'drift_multiplier': -0.5,   # Was: -0.8 → Target -3% annual
},
'CRISIS': {
    'drift_multiplier': -1.8,   # Was: -2.5 → Target -10% annual
},
```

**Rationale:**
- Maintain balance: if GROWTH reduced, others should scale proportionally
- Cycle 1 (CRISIS-heavy) was 0.94% → good, but could be slightly negative
- Cycle 2 (mixed) was -2.73% → good, keep similar

---

## Implementation Plan

### Step 1: GROWTH Drift Reduction (15 min)
1. Edit `config.py` line 29: `drift_multiplier: 1.3 → 0.8`
2. Edit `config.py` lines 37,45,53: Adjust other regime multipliers
3. Test: Run 3 cycles (~7 min), verify returns 5-15%

### Step 2: Regime Transition Frequency (15 min)
1. Edit `regime_manager.py` line 33: `< 20 → < 10`
2. Test: Run 3 cycles, verify 2-4 transitions per cycle
3. Check: No cycles stuck at 0 transitions

### Step 3: Bankruptcy Logic (30 min)
1. Edit `stock_price.py` line 94: AND → OR, thresholds $0.50 / 0.1
2. Edit `stock_price.py` lines 45-48: Increase base cost
3. Test: Run 5 cycles (~12 min), verify some bankruptcies occur
4. Target: 1-5 bankruptcies per cycle (realistic churn)

### Step 4: Full Validation (overnight)
1. Run 20+ cycles (~50 minutes at 20ms)
2. Analyze:
   - Average return: 8-12%
   - Max return per cycle: <30%
   - Regime transitions: 2-5 per cycle
   - Bankruptcies: >0, correlation with IPOs <0.9
   - No regime lock-ins (max single regime <300 periods)

---

## Success Criteria (Updated)

### Priority 1 (CRITICAL)
- ✅ **Returns:** Average 8-12%, no cycle >30% (was >50%)
- ✅ **Regime transitions:** 2-5 per cycle, no 0-transition cycles
- ✅ **No regime lock-in:** Max single regime <300/365 periods (82%)

### Priority 2 (HIGH)
- ✅ **Bankruptcies:** >0 total, at least 1-5 per 5 cycles
- ✅ **IPO/bankruptcy correlation:** <0.9 (was 1.0 perfect match)
- ✅ **Min companies:** >50 (was >20, now we're at 81-100)

### Priority 3 (MEDIUM)
- ✅ **VIX:** Max <80 (achieved: 72.74)
- ✅ **Company stability:** No extinction events <10 companies
- ✅ **Regime balance:** No regime >90% of any cycle

---

## Risk Assessment

### Low Risk
- GROWTH drift reduction (0.8 is still positive, won't cause crashes)
- Regime check frequency (just more granular, same probabilities)

### Medium Risk
- Bankruptcy OR logic (might cause too many failures initially)
- Health cost increase (need to monitor min company count)

### Mitigation
- Incremental testing: Test each fix separately before combining
- Monitor min company count: If drops below 50, revert health cost increase
- Rollback plan: Keep current parameters commented in code

---

## Files to Modify

1. **`/backend/app/config.py`** (Lines 29, 37, 45, 53)
   - Reduce GROWTH drift: 1.3 → 0.8
   - Adjust other regime drifts proportionally

2. **`/backend/app/engine/regime_manager.py`** (Line 33)
   - Increase transition check frequency: 20 → 10 ticks

3. **`/backend/app/engine/stock_price.py`** (Lines 45-48, 94)
   - Increase health cost: prevent regen in GROWTH
   - Fix bankruptcy logic: AND → OR, adjust thresholds

---

## Next Actions

1. **Implement Phase 1-2** (GROWTH drift + transitions) → Quick test (3 cycles)
2. **Implement Phase 3** (Bankruptcies) → Medium test (5 cycles)
3. **Full validation** → Overnight run (20+ cycles)
4. **Analyze results** → Document in `on_review_plan_03.md`

---

## Appendix: Raw Data

### Cycle 3 Analysis (Pure GROWTH - Worst Case)

```json
{
  "cycle_number": 3,
  "return_365t": 45.16,
  "regime_periods": {"GROWTH": 365, "STAGNATION": 0, "CONTRACTION": 0, "CRISIS": 0},
  "regime_transitions": 0,
  "min_vix": 12.42,
  "median_vix": 15.25,
  "min_interest_rate": 0.69,
  "median_interest_rate": 0.75
}
```

**Analysis:**
- Stuck in GROWTH for all 365 periods
- Low VIX (15.25) + low rates (0.75%) = optimal growth conditions
- No offsetting CRISIS/CONTRACTION periods
- Result: Compounding 10% target → 45% actual

### IPO/Bankruptcy Correlation

```
Total IPOs: 19
Total Bankruptcies: 0
Correlation: N/A (division by zero)
Realistic target: 0.3-0.7 correlation
```

**Observation:** Perfect IPO survival rate is unrealistic for a 5-year simulation.
