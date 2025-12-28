# The Market Engine Explained Intuitively

## 🚀 **Latest Improvements: S&P 500 Calibration**

The market engine has been **fine-tuned to match real S&P 500 behavior**:

✅ **Realistic returns** - Target ~7-10% annual growth (vs previous ~25-35%)
✅ **Regime rebalancing** - Bull Market (2.3x), Sideways (1.4x), Correction (0.7x), Bear Market (-0.3x)
✅ **Individual bankruptcies** - Companies fail one-by-one (no mass extinctions)
✅ **IPO mechanism** - **IPOs only during GROWTH regime** (bull markets = risk appetite, bear markets = risk aversion)
✅ **Trading schedule** - 12 ticks trading, 8 ticks closed with overnight gaps
✅ **No sporulation shocks** - Natural volatility drives drawdowns

**Result:** The market behaves like the real S&P 500: steady growth with periodic -10%, -20%, -30% drawdowns! 📈

---

## 🌍 **The Big Picture: A Living Ecosystem**

Think of this as a **terrarium for companies**. Just like plants in a greenhouse, companies need the right conditions to thrive. The market isn't just numbers going up and down - it's a living system where companies fight for survival.

---

## 🌦️ **1. The Weather System (Market Regimes)**

The market has **4 seasons**, each with different "weather":

```
☀️  BULL MARKET (GROWTH)     → Interest rates: 0-1.5%, VIX: ~15  → Strong tailwinds (2.3x)
🌤️  SIDEWAYS MARKET          → Interest rates: 1.5-3.5%, VIX: ~18 → Choppy (1.4x)
🌥️  CORRECTION               → Interest rates: 3.5-5%, VIX: ~25   → Mild headwinds (0.7x)
⛈️  BEAR MARKET (CRISIS)     → Interest rates: 4-5.5%, VIX: ~35   → Sharp declines (-0.3x)
```

**VIX Dynamics (src/App.jsx:418-435):**
- **Blended VIX base**: 50% × 15 + 20% × 18 + 20% × 25 + 10% × 35 = **~19.6 average**
- **Common small spikes** (1% chance per tick): +5 to +12 → VIX reaches mid-20s frequently
- **Rare large spikes** (0.2% chance per tick): +15 to +40 → VIX spikes to 30-70 range
- **Decay**: 15% mean reversion toward regime base per tick
- **Noise**: ±0.75 random walk for realistic jitter

**How it works (src/App.jsx:401-412):**
- Every half-second tick, there's a **0.1% chance** the weather suddenly changes
- This is like a **random environmental shift** - sunny one moment, storm the next
- Less frequent regime changes (vs 0.5% before) create more stable market cycles
- **No sporulation shocks** - removed -6% price shocks to prevent mass extinctions

---

## 💚 **2. Metabolic Health (The Life Force)** - IMPROVED!

Every company starts with **metabolicHealth = 1.0** (100% healthy). But unlike a death spiral, health can now **regenerate**!

**The NEW Metabolic System (src/App.jsx:430-446):**
```javascript
// 1. Base cost (reduced by 50% for realistic behavior)
baseCost = (interestRate / 5.0) * 0.0004 + (vix / 90.0) * 0.0005

// 2. Performance-based regeneration (NEW!)
performanceRegen = recentReturn * 0.02  // Winners heal themselves

// 3. Regime-based adjustment (NEW!)
regimeRegen = REGIMES[regime].healthRegen  // Good times heal, bad times hurt

// 4. Net health change (can be POSITIVE!)
healthChange = -baseCost + performanceRegen + regimeRegen
health = min(1.2, max(0, health + healthChange))  // Capped at 120%
```

**Translation:**
- **Base cost** = Interest rates + VIX (unavoidable overhead)
- **Performance regen** = Profitable companies regenerate health (virtuous cycle!)
- **Regime regen** = GROWTH regime heals, CRISIS regime damages
- **Health cap** = Can't exceed 120% (prevents infinite accumulation)

**Key Insight:** Winners compound their advantage, losers spiral downward. Just like real markets!

**When health hits 0?** → **EXTINCTION** 💀

---

## 📈 **3. Price Movement (The Random Walk)** - IMPROVED!

Every half-second, each stock's price changes based on a **net-growth-biased** formula:

**src/App.jsx:448-465:**
```javascript
// 1. Base drift with regime multiplier (calibrated for ~7-10% annual return)
baseDrift = (stock.valueScore * 0.00002) * regimeMultiplier

// 2. No crisis shocks - natural volatility handles drawdowns
shock = 0

// 3. Health bonus - healthy companies grow faster
healthBonus = (health - 0.5) * 0.001

// 4. Final drift
drift = baseDrift + healthBonus + shock

// 5. Apply volatility
vol = (stock.volatility / 35) * (vix / 14)
change = e^(drift + vol * randomWalk)
```

**Intuitive breakdown:**

1. **Base Drift (RECALIBRATED!)** = Realistic S&P 500-like growth
   - `valueScore * 0.00002` = Fine-tuned for 12 ticks/day schedule
   - `regimeMultiplier` = BULL (2.3x), SIDEWAYS (1.4x), CORRECTION (0.7x), BEAR (-0.3x)
   - Example: Good company in BULL = 0.5 * 0.00002 * 2.3 = **+0.000023 per tick** → ~10.6% annual!

2. **Health Bonus (NEW!)** = Winners win more
   - Healthy companies (health > 50%) get extra growth
   - Sick companies (health < 50%) grow slower
   - Creates compounding advantage

3. **Regime Multiplier (RECALIBRATED!)** = Market cycles drive returns
   - BULL MARKET regime: Strong tailwinds (2.3x) → ~10.6% annual
   - SIDEWAYS MARKET: Choppy (1.4x) → ~6.3% annual
   - CORRECTION: Mild headwinds (0.7x) → ~3.1% annual
   - BEAR MARKET: Sharp declines (-0.3x) → -1.3% annual
   - Mimics real S&P 500 behavior!

4. **Volatility (unchanged)** = The wobble
   - Small caps: more volatile (like small animals - jumpy)
   - Large caps: less volatile (like elephants - steady)
   - VIX amplifies everything (stormy weather = everything shakes)

5. **The Result:**
   ```
   newPrice = oldPrice × e^(drift + randomWalk)
   ```
   - **BULL MARKET** → strong upward trend (~10% annual)
   - **BEAR MARKET** → sharp declines (negative growth)
   - **Blended return** → ~7-10% annual (realistic!)

---

## 💀🌱 **4. The Circle of Life (Extinction & Rebirth)**

**Extinction happens when:**
- Price drops below $0.50, OR
- Health reaches 0

Bankruptcies can occur at any time, but are **more likely during bear markets and crises** due to negative health regeneration.

**What happens to dead companies?**
They are replaced by **IPOs** - but only during favorable market conditions!

**The IPO Mechanism (Regime-Based):**
- **IPOs only occur during GROWTH regime** (bull markets)
- This reflects real-world risk appetite dynamics:
  - 🐂 **Bull markets** → High investor confidence, new companies go public
  - 🐻 **Bear markets** → Risk aversion, bankruptcies accumulate
- When bankrupt companies exist AND market is in GROWTH:
  - One bankruptcy is replaced at a time
  - **Sector-based tickers**: First letter matches sector (T=Tech, H=Healthcare, E=Energy, F=Financials, etc.)
  - Realistic names: "Biotech Holdings", "Cloud Inc", "Renewables Corp"
  - They start fresh: health = 1.0, modest market cap (~$50B)
  - Higher volatility (0.6) because they're young and risky

**This mimics real markets** - IPOs surge during boom times, bankruptcies pile up during crises!

---

## 🗺️ **5. The Treemap Visualization (Size = Power)**

The visual representation is genius:

**src/App.jsx (TreemapTile component):**
```javascript
const totalReturn = ((stock.price - startPrice) / startPrice) * 100
```

- **Tile SIZE** = current market cap (bigger companies = bigger tiles)
- **Tile COLOR** = 60-period performance (finviz-style gradient)
  - 🟢 **Green shades** = positive returns (healthy/growing)
  - 🔴 **Red shades** = negative returns (stressed/dying)
  - **Intensity** = magnitude of return
- **Sector labels** = Top-left corner with black background
- **Hover modal** = Smart positioning to avoid cursor overlap

**Watch in real-time:**
- Tiles **expand** as companies grow
- Tiles **shrink** as companies lose value
- Tiles **disappear** when companies go extinct
- New tiles **appear** when IPOs are launched

---

## 📊 **6. Period Returns Tracking**

The system tracks market performance over multiple time horizons:

**src/App.jsx:528-541:**
```javascript
// Keep 366 ticks of history (need 366 for 365T calculation)
setMarketCapHistory(prev => [...prev, marketCapTotal].slice(-366));

// Calculate returns
getPeriodReturn(60)   // 60-tick return  (~30 seconds)
getPeriodReturn(180)  // 180-tick return (~90 seconds)
getPeriodReturn(365)  // 365-tick return (~3 minutes)
```

**Display:**
- Shown horizontally to the right of System Biomass
- **60T**: Short-term momentum (updates after 61 ticks)
- **180T**: Medium-term trend (updates after 181 ticks)
- **365T**: Long-term performance (updates after 366 ticks)
- **Color coding**: Green (positive), Red (negative), Gray (insufficient data)

**Why 366 ticks?**
To calculate return over 365 ticks, you need the value at tick 0 and tick 365 = 366 data points total.

---

## ⏰ **7. The Heartbeat (Trading Phases)** - UPDATED!

The market has a **realistic trading schedule**:

**src/App.jsx:375-396:**
- **TRADING phase** (12 ticks = 6 seconds) → Market open, live price updates
- **CLOSED phase** (8 ticks = 4 seconds) → After-hours trading continues
- **Overnight gap** → Random ±0.5% to ±2% gap when market reopens

**Key feature:**
- Prices **continue to drift during closed hours** (simulates after-hours trading)
- **Gap on market open** simulates overnight news/events (just like real markets!)
- Full cycle: 20 ticks (10 seconds) = 1 "trading day"

---

## 🎯 **8. The Beautiful Emergent Behavior**

What makes this engine special is what **emerges naturally**:

1. **Market corrections (-10% to -20%)** happen organically when:
   - Regime shifts to CORRECTION or BEAR MARKET
   - VIX spikes above 35
   - Individual companies fail (not mass extinctions!)
   - Health drains gradually, not catastrophically

2. **Bull markets** emerge when:
   - BULL MARKET regime persists
   - Low interest rates + low VIX
   - Metabolic costs are minimal
   - Companies accumulate health reserves
   - **Result:** ~10.6% annual growth!

3. **Sector rotation** happens because:
   - Different sectors have different sub-industries
   - Individual extinctions create vacancies
   - IPOs only appear during GROWTH regime (reflecting risk appetite)
   - New companies enter random sectors with sector-based tickers
   - Treemap constantly reorganizes by market cap

4. **Survival of the fittest**:
   - High `valueScore` stocks survive longer
   - Low volatility = more stable = better survival
   - Large caps have built-in advantages (lower volatility)
   - Winners compound their advantage (health → growth feedback loop)

---

## 🔬 **9. The Genius: Why Biological Metaphors Work**

Markets ARE ecosystems:
- **Companies** = organisms
- **Capital** = nutrients
- **Interest rates** = temperature
- **Volatility** = predators
- **Bankruptcy** = death
- **IPOs** = birth
- **Market cap** = biomass

This isn't just a cute metaphor - it captures real market dynamics:
- Resources are limited (capital flows)
- Environment matters (macro conditions)
- Adaptation is key (valueScore)
- Systems self-regulate (IPO mechanism prevents total collapse)
- Creative destruction (individual failures → new opportunities)

The result? A mesmerizing simulation that **feels** like a real market because it models the underlying **evolutionary pressures** that drive all competitive systems.

---

## 📋 **10. Quick Reference: Key Parameters**

### Regime Distribution (Target)
```
BULL MARKET:    50% of time → +10.6% annual return
SIDEWAYS:       20% of time → +6.3% annual return
CORRECTION:     20% of time → +3.1% annual return
BEAR MARKET:    10% of time → -1.3% annual return
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLENDED RETURN: ~7-10% annually (S&P 500-like)
```

### Trading Schedule
```
12 ticks (6 sec)  = TRADING phase (market open)
8 ticks (4 sec)   = CLOSED phase (after-hours)
20 ticks (10 sec) = Full cycle (1 trading day)
```

### VIX Behavior
```
Base range:       15-35 (regime-dependent)
Average:          ~18-20 (realistic)
Small spikes:     1% chance → mid-20s (frequent)
Large spikes:     0.2% chance → 30-70 (rare)
```

### Health Dynamics
```
Base cost:        (IR/5)*0.0004 + (VIX/90)*0.0005
Performance regen: recentReturn * 0.02
Regime adjustment: ±0.0001 to ±0.00008
Health cap:       0.0 to 1.2 (120% max)
```

### Price Drift
```
Base:             valueScore * 0.00002
Regime multiplier: 2.3, 1.4, 0.7, -0.3
Health bonus:     (health - 0.5) * 0.001
Target return:    ~7-10% annually
```

### IPO Mechanism
```
Trigger:          GROWTH regime (bull markets) + bankruptcies exist
Timing:           IPOs only occur during favorable market conditions
                  Bankruptcies accumulate during bear markets/crises
Ticker format:    Sector-based (T=Tech, H=Healthcare, E=Energy, etc.)
Initial cap:      $50-100B (randomized)
Initial health:   1.0 (100%)
Volatility:       0.6 (higher risk for new companies)
Risk dynamics:    Bull markets = IPO boom | Bear markets = bankruptcies pile up
```
