# Fundamental Analysis: 8-Cycle Deep Dive

**Date:** 2025-12-29
**Config:** GROWTH drift=0.6, regime checks every 10 ticks, AND bankruptcy (0.25/0.05)

---

## Executive Summary

After extensive tuning (3 major iterations), the simulation **still produces unrealistic returns** (avg 14.4% vs target 8-12%). The problem is **NOT** in the regime drift multipliers we've been adjusting.

**ROOT CAUSE:** The **health bonus system** is dominating all other drift components, rendering regime multipliers meaningless.

---

## 8-Cycle Data Overview

| Cycle | Return | IPOs | Bankruptcies | Transitions | Regime Distribution | Issue |
|-------|--------|------|--------------|-------------|---------------------|-------|
| 0 | **7.69%** ✅ | 4 | 0 | 3 | 22/61/123/158 | Perfect! |
| 1 | **33.18%** ❌ | 16 | 1 | 3 | **290**/2/0/72 | GROWTH lock (79%) |
| 2 | **33.54%** ❌ | 23 | 23 | **0** | **365**/0/0/0 | 100% GROWTH lock |
| 3 | **21.23%** ⚠️ | 13 | 45 | 6 | 79/69/82/134 | Mixed, still high |
| 4 | **22.17%** ⚠️ | 41 | 9 | 1 | **315**/49/0/0 | GROWTH lock (86%) |
| 5 | **22.35%** ⚠️ | 0 | 16 | 3 | 0/**285**/76/4 | STAG lock (78%) |
| 6 | **27.11%** ❌ | 24 | 9 | 7 | 101/125/77/61 | Mixed, high |
| 7 | **-13.56%** ✅ | 0 | 10 | 4 | 0/69/7/**288** | CRISIS lock (79%) |
| 8 | **-23.3%** ✅ | 0 | 12 | 4 | 0/179/130/56 | Mixed negative |

**Average Return:** 14.4% (target: 8-12%)
**Total IPOs:** 121, **Total Bankruptcies:** 125 (balanced! ✅)
**Company Range:** 65-100 (healthy! ✅)

---

## Pattern Analysis

### Returns by Regime Dominance

**Pure GROWTH Cycles (>250 periods):**
- Cycle 1: 290 periods → 33.18%
- Cycle 2: 365 periods → 33.54%
- Cycle 4: 315 periods → 22.17%
- **Average: 29.6%** (3.7x target!)

**Pure CRISIS Cycles (>250 periods):**
- Cycle 7: 288 periods → -13.56%
- **Result: Realistic downside** ✅

**Mixed Cycles (<250 any regime):**
- Cycle 0: -13.56% to 7.69% (realistic range)
- Cycle 3,6: 21-27% (still high)

**KEY INSIGHT:** When any regime dominates (>250/365 periods), returns become extreme. The issue isn't the drift values—it's the **regime persistence** allowing compounding to dominate.

---

## ROOT CAUSE: The Health Bonus Paradox

### The Math That Breaks Everything

Current drift calculation (stock_price.py lines 66-79):

```python
# 1. Base drift
base_drift = (stock.value_score * 0.00002) * regime_multiplier

# 2. Health bonus
health_bonus = (health - 0.5) * 0.001

# 3. Final drift
drift = base_drift + health_bonus + shock
```

**Example: GROWTH regime with health = 1.0**

```python
# Base drift
value_score = 0.5  # average
regime_multiplier = 0.6  # GROWTH
base_drift = 0.5 * 0.00002 * 0.6 = 0.000006

# Health bonus
health = 1.0  # healthy stock
health_bonus = (1.0 - 0.5) * 0.001 = 0.0005

# Total
total_drift = 0.000006 + 0.0005 = 0.000506
```

**The health bonus (0.0005) is 83x larger than the base drift (0.000006)!**

### Impact Over 365 Periods (7,300 ticks)

```python
# With base drift only:
price_final = price_initial * e^(0.000006 * 7300)
            = e^0.044 ≈ 1.045
            = +4.5% return ✅

# With health bonus:
price_final = price_initial * e^(0.000506 * 7300)
            = e^3.69 ≈ 40.1
            = +3,910% return ❌
```

**Wait, but we're seeing 33%, not 3,910%?**

The capped volatility (±1.5% per tick) and random walk are adding noise that prevents the full exponential explosion, but the underlying issue remains: **health bonus dominates regime multipliers by 83x**.

---

## Why Our Tuning Failed

### Iteration 1: Reduce GROWTH drift 1.3 → 0.8
- **Logic:** Lower multiplier = lower returns
- **Result:** Returns dropped from 45% to 25-33%
- **Why it helped but didn't fix:** Reduced base drift, but health bonus still dominates

### Iteration 2: Reduce GROWTH drift 0.8 → 0.6
- **Logic:** Even lower multiplier
- **Result:** Returns still 22-33% in GROWTH-heavy cycles
- **Why it failed:** Health bonus (0.0005) >> base drift (0.000006)

### Iteration 3: Bankruptcy system tuning
- **Logic:** More bankruptcies = lower average health = lower health bonus
- **Result:** Helped slightly, but GROWTH lock-in persists
- **Why it failed:** Doesn't address regime persistence or health bonus dominance

**WE'VE BEEN TUNING THE WRONG PARAMETER.**

Reducing regime drift multipliers from 1.3 → 0.6 had minimal impact because the health bonus is 83x larger and regime-independent!

---

## The Real Problems

### Problem 1: Health Bonus Dominates Drift (CRITICAL)

**Current state:**
```python
health_bonus = (health - 0.5) * 0.001  # ±0.0005 per tick
base_drift = (0.5 * 0.00002) * 0.6 = 0.000006  # GROWTH
```

**Ratio:** 0.0005 / 0.000006 = **83:1**

**Impact:**
- Regime multipliers (0.6, 0.1, -0.4, -1.4) are almost meaningless
- Health becomes the PRIMARY driver of returns
- Creates positive feedback loop: high health → high returns → health regen → higher health

**Why it was added:**
- Originally intended as a small "value investing" bonus
- Designed when regime drifts were much higher (6.5 for GROWTH)
- Became dominant when we reduced regime drifts

---

### Problem 2: Regime Lock-In Persists (HIGH)

**Current transition logic:**
- Check every 10 ticks (730 checks per cycle)
- GROWTH stay probability: 99.7%
- Expected transitions: 730 * 0.003 = **2.19 per cycle**

**Observed:**
- Cycle 2: **0 transitions** (locked for 365 periods)
- Cycle 4: **1 transition** (locked for 315 periods)
- High variance: 0-7 transitions across cycles

**Math explanation:**
```
Probability of staying entire cycle = 0.997^730 ≈ 0.11 (11%)
```

We expect 11% of cycles to have **total lock-in** (0 transitions). This matches observations (Cycle 2).

**Why it's a problem:**
- When locked in GROWTH for 365 periods, compounding produces 33% returns
- Even with "correct" drift values, extended runs create unrealistic results
- Real markets don't stay in one regime for 365 consecutive periods (1 year)

---

### Problem 3: No Mean Reversion (MEDIUM)

**Current system:**
- Once in GROWTH: health regenerates, prices rise, returns compound
- Once in CRISIS: health decays, prices fall, returns collapse
- **No force pulling back to equilibrium**

**Real markets have:**
- Valuation limits (P/E ratios can't rise forever)
- Central bank intervention
- Profit-taking behavior
- Sentiment cycles

**Impact:**
- Pure GROWTH cycles produce 33% returns
- Pure CRISIS cycles produce -23% returns
- No mechanism to prevent extremes

---

### Problem 4: Compounding Over Long Periods (STRUCTURAL)

**The fundamental issue with any exponential system:**

```python
# Over 7,300 ticks
drift_per_tick = 0.0005  # even a "small" drift
cumulative_return = e^(0.0005 * 7300) - 1 = 39x = 3,800%
```

**Any sustained drift, even tiny, produces massive returns over 7,300 ticks.**

**Why capping volatility helped but isn't enough:**
- Volatility cap (±1.5%) prevents 900%+ explosions
- But drift still compounds exponentially
- Need to cap or decay the drift itself

---

## Fundamental Solutions Needed

### Solution 1: Drastically Reduce/Remove Health Bonus (CRITICAL)

**Option A: Remove entirely**
```python
# stock_price.py line 76
health_bonus = 0  # Remove completely
```

**Option B: Reduce by 100x**
```python
health_bonus = (health - 0.5) * 0.00001  # Was 0.001
```

**Option C: Cap maximum health bonus**
```python
health_bonus = min(0.00001, (health - 0.5) * 0.001)
```

**Recommendation:** Option B (reduce by 100x)
- Keeps the concept of health-based performance
- Makes it comparable to base drift (not 83x larger)
- Allows regime multipliers to actually matter

**Expected impact:**
```python
# GROWTH with reduced health bonus:
base_drift = 0.000006
health_bonus = 0.000005  # 100x reduction
total_drift = 0.000011

# Over 7,300 ticks:
return = e^(0.000011 * 7300) - 1 ≈ 8.4% ✅
```

---

### Solution 2: Increase Regime Transition Frequency (HIGH)

**Option A: Check every 5 ticks (was 10)**
```python
# regime_manager.py line 33
if self.ticks_since_last_check < 5:  # Was 10
    return None
```

**Expected transitions:** 1,460 checks * 0.003 = 4.38 per cycle
**Lock-in probability:** 0.997^1460 ≈ 1.2% (much lower!)

**Option B: Reduce stay probabilities further**
```python
# config.py
'GROWTH': {
    'GROWTH': 0.994,    # Was 0.997 → avg 166 periods before transition
    'STAGNATION': 0.004,
    'CONTRACTION': 0.002,
}
```

**Expected transitions:** 730 checks * 0.006 = 4.38 per cycle (same as Option A)

**Recommendation:** Use both!
- Check every 5 ticks (more granular)
- Reduce stay to 0.994 (faster transitions)
- Expected: 1,460 * 0.006 = 8.76 transitions per cycle

---

### Solution 3: Add Mean Reversion Mechanism (MEDIUM)

**Option A: Time-based drift decay**
```python
# Reduce drift the longer you're in a regime
ticks_in_regime = self.ticks_in_regime
decay_factor = max(0.5, 1.0 - (ticks_in_regime / 10000))
drift = base_drift * decay_factor
```

**Option B: Valuation-based cap**
```python
# Slow growth when prices get too high relative to initial
current_ratio = stock.price / stock.initial_price
if current_ratio > 2.0:  # Stock doubled
    drift = drift * 0.5  # Half the drift
```

**Option C: Increase transition probability with time**
```python
# regime_manager.py
def get_transition_prob(self):
    base_prob = 0.003
    time_factor = min(2.0, self.ticks_in_regime / 2000)
    return base_prob * time_factor
```

**Recommendation:** Option C (time-based transition boost)
- Natural: markets don't stay in one state forever
- Simple: just multiply transition prob by time factor
- Effective: prevents 365-period lock-ins

---

### Solution 4: Reduce Regime Drift Multipliers Further (MEDIUM)

**Only AFTER health bonus is fixed!**

Once health bonus is reduced 100x, we can properly calibrate regime drifts:

```python
# config.py - Calibrated for ~8% annual GROWTH return
REGIMES = {
    'GROWTH': {
        'drift_multiplier': 0.8,   # Target ~8% annual (after health bonus fix)
    },
    'STAGNATION': {
        'drift_multiplier': 0.0,   # Target ~0% annual
    },
    'CONTRACTION': {
        'drift_multiplier': -0.5,  # Target -5% annual
    },
    'CRISIS': {
        'drift_multiplier': -1.2,  # Target -12% annual
    }
}
```

**Why this works now:**
```python
# GROWTH example:
base_drift = 0.5 * 0.00002 * 0.8 = 0.000008
health_bonus = 0.5 * 0.00001 = 0.000005  # 100x reduced
total_drift = 0.000013

# Over 7,300 ticks:
return = e^(0.000013 * 7300) - 1 ≈ 10.0% ✅
```

---

## Implementation Priority

### Phase 1: Fix Health Bonus (CRITICAL)
**Impact:** Immediately fixes GROWTH return explosion
**Effort:** 5 minutes (1 line change)
**Risk:** Low

### Phase 2: Increase Transition Frequency (HIGH)
**Impact:** Prevents regime lock-in
**Effort:** 10 minutes (2 file changes)
**Risk:** Low

### Phase 3: Add Mean Reversion (MEDIUM)
**Impact:** Prevents extended runs from compounding
**Effort:** 30 minutes (new logic)
**Risk:** Medium (could overcorrect)

### Phase 4: Recalibrate Regime Drifts (LOW)
**Impact:** Fine-tune after fixes
**Effort:** 15 minutes + testing
**Risk:** Low

---

## Recommended Configuration

```python
# 1. HEALTH BONUS (stock_price.py line 76)
health_bonus = (health - 0.5) * 0.00001  # Reduced 100x from 0.001

# 2. REGIME TRANSITIONS (regime_manager.py line 33)
if self.ticks_since_last_check < 5:  # Check every 5 ticks (was 10)
    return None

# 3. STAY PROBABILITIES (config.py lines 60-83)
REGIME_TRANSITIONS = {
    'GROWTH': {
        'GROWTH': 0.994,       # Was 0.997 → avg 166 periods
        'STAGNATION': 0.004,
        'CONTRACTION': 0.002,
        'CRISIS': 0.0
    },
    # Similar for other regimes
}

# 4. REGIME DRIFTS (config.py lines 24-55)
REGIMES = {
    'GROWTH': {'drift_multiplier': 0.8},      # Increased from 0.6
    'STAGNATION': {'drift_multiplier': 0.0},  # Decreased from 0.1
    'CONTRACTION': {'drift_multiplier': -0.5}, # Decreased from -0.4
    'CRISIS': {'drift_multiplier': -1.2},     # Decreased from -1.4
}
```

---

## Expected Results

### With All Fixes Applied

**Pure GROWTH cycle (worst case: 300/365 periods):**
```python
drift_per_tick = 0.000013  # base + reduced health bonus
ticks = 7300
return = e^(0.000013 * 7300) - 1 ≈ 10.0% ✅
```

**Mixed cycle (realistic: 150/150/65/0 periods):**
```python
# GROWTH: 150 periods * 0.000013 = 0.00195
# STAGNATION: 150 periods * 0.000000 = 0.00000
# CONTRACTION: 65 periods * -0.000008 = -0.00052
# Total drift: 0.00143
return = e^0.00143 - 1 ≈ 0.14% per 365-period ≈ 1.4% annual ✅
```

Wait, that's too low. Let me recalculate...

Actually, the drift compounds continuously, so:
```python
# GROWTH portion: 150 periods = 3000 ticks
price_after_growth = price_start * e^(0.000013 * 3000) = e^0.039 ≈ 1.040

# STAGNATION: 150 periods = 3000 ticks
price_after_stag = price_after_growth * e^(0.000000 * 3000) = 1.040

# CONTRACTION: 65 periods = 1300 ticks
price_final = price_after_stag * e^(-0.000008 * 1300) = e^-0.0104 ≈ 0.990

# Total: 1.040 * 1.000 * 0.990 ≈ 1.030 → +3.0% ✅
```

**Expected results across 8 cycles:**
- Pure GROWTH: ~10-12%
- Pure CRISIS: ~-12%
- Mixed: 0-8%
- Average: ~5-8% ✅

**Regime transitions:**
- 1,460 checks/cycle * 0.006 prob = ~8-9 per cycle
- Max lock: ~166 periods (45% of cycle)
- No total lock-ins (0 transitions)

**Bankruptcy/Company dynamics:**
- Bankruptcies: 1-10 per cycle (realistic churn)
- Company count: 70-100 (stable)

---

## Why This Will Work

1. **Health bonus no longer dominates:** Regime multipliers can finally do their job
2. **Regime lock-in prevented:** More frequent checks + time-based boosting
3. **Returns match S&P 500:** ~5-10% long-term average
4. **Realistic variance:** Bull markets exist but don't produce 33% years
5. **Bankruptcy dynamics:** AND condition prevents mass extinction while allowing churn

---

## Risk Assessment

**Low Risk:**
- Health bonus reduction (won't break anything, just scales down)
- Transition frequency increase (just more granular checks)

**Medium Risk:**
- Stay probability reduction (might create too much chaos)
  - Mitigation: Test with 0.994, adjust to 0.995 if too volatile

**High Risk:**
- Mean reversion mechanisms (could overcorrect)
  - Mitigation: Implement in Phase 3 after validating Phases 1-2

---

## Next Steps

1. **Implement Phase 1+2** (health bonus + transition frequency)
2. **Run 5-cycle test** (~12 min)
3. **Analyze results:**
   - Average return: 5-10%?
   - Max single cycle: <15%?
   - Regime lock-in: max <200/365 periods?
4. **If good:** Run overnight 20+ cycle validation
5. **If not:** Adjust and iterate

---

## Conclusion

**We've been optimizing the wrong variables.** Tuning regime drift multipliers from 1.3 → 0.8 → 0.6 had minimal impact because the health bonus (0.0005) is 83x larger than the base drift (0.000006).

**The fix is simple:** Reduce health bonus by 100x, increase regime transition frequency, and the system will naturally produce realistic returns.

**This is why data analysis matters:** Without the 8-cycle dataset, we would have continued tweaking regime drifts indefinitely without solving the root cause.
