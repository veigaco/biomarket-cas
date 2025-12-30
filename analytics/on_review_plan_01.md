# Plan: Fix Unrealistic Market Behavior

## Overview

Analyze overnight market data showing abnormal behavior and implement fixes to create realistic market dynamics similar to S&P 500 historical patterns.

## Problems Identified from Data Analysis

### 1. Extreme Returns (CRITICAL)
- **Observed**: Cycle 15 shows 899.68% and 911% returns, Cycle 17 shows 814.71% and 908.57%
- **Root Cause**: Exponential volatility formula with unbounded random term creates compound multiplicative swings
- **Formula**: `change = exp(drift + vol * (random() - 0.5))` where `vol = (volatility/35) * (vix/14)`
- **Impact**: With volatility=0.75 and vix=35, single tick can be ±2.7%, compounding to 970%+ over 120 ticks

### 2. Excessive Regime Transitions (HIGH)
- **Observed**: 28-49 transitions per 365-period cycle
- **Root Cause**: Transition probabilities designed for 20-tick period checks, but applied EVERY tick
- **Expected**: ~1-3 regime changes per year (real S&P 500)
- **Actual**: 10-16x more frequent than reality

### 3. Perfect IPO/Bankruptcy Balance (HIGH)
- **Observed**: Cycle 7: 237/237, Cycle 9: 252/252, nearly all cycles show exact matches
- **Root Cause**: 1:1 replacement logic - every bankruptcy immediately replaced with IPO during GROWTH
- **Impact**: Unrealistic perfect correlation between events that should be independent

### 4. Near-Extinction Events (MEDIUM)
- **Observed**: Company counts drop to 5-8 minimum in multiple cycles
- **Root Cause**:
  - Weak metabolic health regeneration (5-tick lookback = 2.5 seconds)
  - $0.50 bankruptcy threshold too aggressive
  - Base health cost drain too strong relative to regeneration

---

## Implementation Plan

### Phase 1: Fix Extreme Volatility (CRITICAL - Priority 1)

**File**: `/Users/vveiga/code/mkteng/backend/app/engine/stock_price.py`

#### Changes Needed:

1. **Cap the volatility exponent** (lines 66-85):
   ```python
   # Current:
   vol = (stock.volatility / 35) * (market_state.vix / 14)
   change = math.exp(drift + vol * (random.random() - 0.5))

   # Fix:
   vol_term = vol * (random.random() - 0.5)
   capped_vol_term = max(-0.015, min(0.015, vol_term))  # Cap at ±1.5% per tick
   change = math.exp(drift + capped_vol_term)
   ```

2. **Reduce volatility scaling factor**:
   - Change divisor from 35 to 50 to reduce overall volatility impact
   - This makes high-volatility stocks (0.75) less extreme

3. **Add realistic daily volatility targeting**:
   - S&P 500 daily volatility: ~1.5% (normal), ~3% (high), ~5% (crisis)
   - Current system: No daily bounds, only per-tick exponentials
   - Add: Daily return tracking with mean reversion

**Expected Impact**: Reduce extreme returns from 900%+ to realistic 10-30% annual ranges

---

### Phase 2: Fix Regime Transitions (Priority 2)

**File**: `/Users/vveiga/code/mkteng/backend/app/engine/regime_manager.py`

#### Option A: Period-Based Transitions (Recommended)

1. **Add tick counter** (lines 12-15):
   ```python
   def __init__(self):
       self.current_regime = Regime.GROWTH
       self.ticks_in_regime = 0
       self.ticks_since_last_check = 0
   ```

2. **Check transitions only every 20 ticks** (lines 18-39):
   ```python
   def update(self) -> Optional[str]:
       self.ticks_since_last_check += 1
       self.ticks_in_regime += 1

       # Only check transitions every 20 ticks (1 period)
       if self.ticks_since_last_check < 20:
           return None

       self.ticks_since_last_check = 0

       # Existing transition logic here...
   ```

#### Option B: Reduce Transition Probabilities

Alternatively, adjust probabilities in `/Users/vveiga/code/mkteng/backend/app/config.py`:
```python
# Reduce all non-diagonal probabilities by 20x
'GROWTH': {
    'GROWTH': 0.9999,      # 99.99% stay (was 99.7%)
    'STAGNATION': 0.0001,  # 0.01% (was 0.2%)
    # ...
}
```

**Expected Impact**: Reduce transitions from 28-49 per cycle to 2-5 per cycle (realistic)

---

### Phase 3: Decouple IPO/Bankruptcy Events (Priority 3)

**File**: `/Users/vveiga/code/mkteng/backend/app/engine/ipo_manager.py`

#### Changes Needed:

1. **Add independent IPO rate** (lines 20-30):
   ```python
   def __init__(self):
       self.stock_id_counter = 0
       self.ipo_probability_per_period = 0.3  # 30% chance of IPO per period during GROWTH
       self.ticks_since_last_check = 0
   ```

2. **Separate IPO generation from bankruptcy replacement** (lines 31-100):
   ```python
   def process(self, stocks: List[Stock], regime: Regime) -> Optional[dict]:
       self.ticks_since_last_check += 1

       # Only process once per period (20 ticks)
       if self.ticks_since_last_check < 20:
           return None

       self.ticks_since_last_check = 0

       active_count = sum(1 for s in stocks if s.status == 'active')
       bankrupt_count = sum(1 for s in stocks if s.status == 'bankrupt')
       total_count = len(stocks)

       # Emergency IPOs if <10% active (keep existing failsafe)
       emergency_mode = active_count < (total_count * 0.1)

       # Independent IPO generation during GROWTH (not tied to bankruptcies)
       if regime == Regime.GROWTH or emergency_mode:
           # Random IPO generation
           if random.random() < self.ipo_probability_per_period:
               if bankrupt_count > 0:
                   # Replace a bankrupt stock
                   # ... existing replacement logic
               elif len(stocks) < 100:  # Cap total market size
                   # Add new stock to market
                   # ... create new stock instead of replacing

       return None
   ```

3. **Allow bankruptcy accumulation**:
   - Don't replace ALL bankruptcies immediately
   - Let some bankrupt stocks remain (realistic delay)
   - Only replace when IPO event triggers

**Expected Impact**: Break perfect 1:1 correlation, create realistic lag between bankruptcies and IPOs

---

### Phase 4: Strengthen Metabolic Health System (Priority 4)

**File**: `/Users/vveiga/code/mkteng/backend/app/engine/stock_price.py`

#### Changes Needed:

1. **Increase health lookback window** (lines 52-55):
   ```python
   # Current: 5 ticks (2.5 seconds)
   if len(stock.history) >= 5:
       recent_return = (stock.price - stock.history[-5]) / stock.history[-5]

   # Fix: 60 ticks (30 seconds) - more realistic recovery timeframe
   if len(stock.history) >= 60:
       recent_return = (stock.price - stock.history[-60]) / stock.history[-60]
   ```

2. **Reduce base health cost** (lines 56-58):
   ```python
   # Current:
   base_cost = (interest_rate / 5.0) * 0.0008 + (vix / 90.0) * 0.001

   # Fix: Reduce drain by 50%
   base_cost = (interest_rate / 5.0) * 0.0004 + (vix / 90.0) * 0.0005
   ```

3. **Lower bankruptcy price threshold** (line 88):
   ```python
   # Current: $0.50 threshold
   if new_price < 0.5 or health <= 0:

   # Fix: Lower to $0.10, require both conditions
   if new_price < 0.10 and health <= 0:
   ```

**Expected Impact**: Companies survive longer during downturns, minimum company count stays above 20-30

---

### Phase 5: Adjust Regime Parameters for Realistic Returns

**File**: `/Users/vveiga/code/mkteng/backend/app/config.py`

#### Recalibrate Drift Multipliers (lines 31-57):

Target annual returns (365 periods = 7,300 ticks):
- GROWTH: +10% per year (not 30%)
- STAGNATION: +2% per year
- CONTRACTION: -5% per year
- CRISIS: -15% per year

**Current drift formula**: `base_drift = (value_score * 0.00002) * regime_multiplier`

**Math for GROWTH**:
- Needed: `(1 + daily_return)^7300 = 1.10` → `daily_return = 0.000013`
- With value_score ≈ 0.5: `0.00002 * 0.5 * multiplier = 0.000013`
- Required multiplier: **1.3** (current: 6.5)

**Adjusted multipliers**:
```python
REGIMES = {
    'GROWTH': {
        'label': 'Bull Market',
        'color': '#22c55e',
        'drift_multiplier': 1.3,    # Was: 6.5
        'vix_base': 15,
        'rate_range': (0.5, 2.0),
        'health_regen': 0.0002,
    },
    'STAGNATION': {
        'drift_multiplier': 0.3,     # Was: 1.2
        'vix_base': 18,
        # ...
    },
    'CONTRACTION': {
        'drift_multiplier': -0.8,    # Was: -1.2
        'vix_base': 25,
        # ...
    },
    'CRISIS': {
        'drift_multiplier': -2.5,    # Was: -5.0
        'vix_base': 35,
        # ...
    }
}
```

**Expected Impact**: Annual returns align with S&P 500 historical averages

---

## Implementation Sequence

### Step 1: Fix Volatility (1-2 hours)
1. Modify `stock_price.py` lines 66-85
2. Add volatility cap to prevent extreme moves
3. Test: Run 1 cycle, verify max single-period return < 20%

### Step 2: Fix Regime Transitions (30 min)
1. Modify `regime_manager.py` to check transitions every 20 ticks
2. Test: Run 1 cycle, verify 2-5 transitions instead of 28-49

### Step 3: Fix IPO/Bankruptcy Balance (1 hour)
1. Modify `ipo_manager.py` to decouple events
2. Test: Run 1 cycle, verify IPO ≠ bankruptcy count

### Step 4: Strengthen Health System (30 min)
1. Modify `stock_price.py` health calculations
2. Test: Run 1 cycle, verify min companies > 20

### Step 5: Recalibrate Regime Parameters (15 min)
1. Modify `config.py` drift multipliers
2. Test: Run full cycle, verify annual returns 5-15%

### Step 6: Long-Term Validation (overnight)
1. Run 20+ cycles overnight
2. Verify statistics match S&P 500 historical patterns:
   - Annual returns: 8-12% average
   - Max drawdown: <30% per year
   - Regime transitions: 2-4 per year
   - IPO/bankruptcy correlation: <0.5

---

## Success Criteria

✅ **Volatility**: No single cycle shows >50% return (vs current 911%)
✅ **Regime transitions**: 2-5 per 365-period cycle (vs current 28-49)
✅ **IPO/bankruptcy**: Correlation <0.7 (vs current 1.0 perfect match)
✅ **Company survival**: Minimum companies >20 (vs current 5-8)
✅ **Annual returns**: Average 8-12% in GROWTH cycles
✅ **VIX spikes**: Max VIX <80 (current: 87)
✅ **Realistic drawdowns**: Max -30% in CRISIS cycles (vs current -92%)

---

## Files to Modify

1. `/Users/vveiga/code/mkteng/backend/app/engine/stock_price.py` - Fix volatility, health system
2. `/Users/vveiga/code/mkteng/backend/app/engine/regime_manager.py` - Fix transition frequency
3. `/Users/vveiga/code/mkteng/backend/app/engine/ipo_manager.py` - Decouple IPO/bankruptcy
4. `/Users/vveiga/code/mkteng/backend/app/config.py` - Recalibrate regime parameters

---

## Risk Mitigation

- **Backup current code**: Create git branch before changes
- **Incremental testing**: Test each fix separately before combining
- **Overnight validation**: Run 20+ cycles to verify improvements
- **Rollback plan**: Keep original parameters in comments for comparison
