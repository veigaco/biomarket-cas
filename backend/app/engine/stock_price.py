"""
Stock price dynamics engine with true bottom-up volatility model.

Phase 1: Pure volatility-driven price movements where market returns
emerge organically from market-cap-weighted aggregation of individual stocks.

Key principles:
- Volatility is the primary driver of short-term moves (not regime drift)
- Each stock has tier-based annualized volatility (MEGA: 15-25%, SMALL: 40-70%)
- Market index volatility (~15-20%) emerges from aggregation
- Small positive drift provides long-term growth bias (~10% annual)
"""

import math
import random
from typing import List, Optional

from ..models.stock import Stock
from ..models.market_state import MarketState
from ..models.regime import Regime
from ..config import REGIMES, HISTORY_LENGTH
from ..config.loader import (
    get_cached_config,
    get_size_multiplier,
    get_bankruptcy_probability,
    get_market_cap_tier
)

# Tier-based annualized volatility ranges (realistic market behavior)
# These match real market data: large caps are stable, small caps are volatile
TIER_VOLATILITY = {
    'MEGA_CAP': (0.15, 0.25),    # 15-25% annual (blue chips like AAPL, MSFT)
    'LARGE_CAP': (0.20, 0.35),   # 20-35% annual (established companies)
    'MID_CAP': (0.30, 0.50),     # 30-50% annual (growth companies)
    'SMALL_CAP': (0.40, 0.70),   # 40-70% annual (speculative stocks)
}

# Conversion factor: annualized vol to per-tick vol
# With 7,300 ticks/cycle (year): tick_vol = annual_vol / sqrt(7300) = annual_vol / 85.4
SQRT_TICKS_PER_YEAR = 85.4

# Base drift for long-term market growth
# Phase 2: Set to 0, let health-based drift provide the bias
# Health drift responds to market conditions (VIX, rates)
BASE_ANNUAL_DRIFT = 0.0
BASE_TICK_DRIFT = BASE_ANNUAL_DRIFT / 7300


class StockPriceEngine:
    """
    Handles stock price updates using true bottom-up volatility model.

    Phase 1 features:
    - Tier-based volatility (MEGA: 15-25%, SMALL: 40-70% annualized)
    - VIX amplifies volatility (VIX 35 = 1.5x normal vol)
    - Small positive drift (~10% annual) provides growth bias
    - Market returns emerge organically from aggregation
    - NO direct regime control of drift (regime only affects VIX)
    """

    def __init__(self):
        self.market_caps_config = get_cached_config('market_caps')
        self.regime_behaviors_config = get_cached_config('regime_behaviors')
        self.vix_distribution_config = get_cached_config('vix_distribution')
        self.winner_threshold = self.market_caps_config['winner_dynamics']['escape_velocity_threshold']
        self.tracking_window = self.market_caps_config['winner_dynamics']['tracking_window_cycles'] * 365  # periods
        self.winner_drift = self.market_caps_config['winner_dynamics']['winner_sustained_drift']

    def calculate_tick_volatility(self, stock: Stock, market_state: MarketState) -> float:
        """
        Calculate per-tick volatility based on tier and market conditions.

        Target annualized volatility by tier:
        - MEGA_CAP: 15-25% (stable blue chips)
        - LARGE_CAP: 20-35% (established companies)
        - MID_CAP: 30-50% (growth companies)
        - SMALL_CAP: 40-70% (speculative)

        VIX amplification:
        - VIX 15 (normal) = 1.0x volatility
        - VIX 35 (crisis) = 1.5x volatility
        - VIX 50+ (extreme) = 1.875x volatility

        Returns:
            Per-tick volatility (standard deviation of log returns)
        """
        tier = stock.market_cap_tier
        min_vol, max_vol = TIER_VOLATILITY.get(tier, (0.30, 0.50))

        # Interpolate within tier range using stock's base volatility (0.0-1.0)
        annual_vol = min_vol + stock.volatility * (max_vol - min_vol)

        # VIX amplification (VIX 15 = normal, VIX 35 = 1.5x, VIX 55 = 2x)
        vix_mult = 1.0 + (market_state.vix - 15) / 40
        annual_vol *= max(0.5, vix_mult)  # Floor at 0.5x to prevent negative

        # Convert annualized to per-tick volatility
        tick_vol = annual_vol / SQRT_TICKS_PER_YEAR

        return tick_vol

    def calculate_health_drift(self, stock: Stock, market_state: MarketState) -> float:
        """
        Phase 2: VIX and rates create organic bias via health.

        Simplified model:
        - VIX > 20: market stress, negative drift
        - VIX < 20: calm conditions, positive drift
        - Rates amplify the effect slightly

        Returns:
            Health-based drift modifier (per tick)
        """
        # VIX-based stress: centered at VIX 20
        vix_factor = (20 - market_state.vix) / 100  # VIX 15 = +0.05, VIX 30 = -0.10

        # Rate adjustment: higher rates = more negative
        rate_factor = -market_state.interest_rate / 200  # Rate 4% = -0.02

        # Combined condition factor
        condition = vix_factor + rate_factor  # Typically -0.15 to +0.05

        # Size advantage in stressed conditions
        size_mult = {
            'MEGA_CAP': 1.2,   # Large caps do better in stress
            'LARGE_CAP': 1.1,
            'MID_CAP': 1.0,
            'SMALL_CAP': 0.8,  # Small caps suffer more
        }.get(stock.market_cap_tier, 1.0)

        # Apply condition to health
        health_change = condition * 0.001  # Small adjustment
        stock.metabolic_health = max(0.2, min(1.2, stock.metabolic_health + health_change))

        # Convert to drift: centered at health 0.6 for positive bias
        # Health 1.0 = +8% annual, health 0.6 = 0%, health 0.2 = -8%
        base_health_drift = (stock.metabolic_health - 0.6) * 0.00002 * size_mult

        return base_health_drift

    def update_all(
        self,
        stocks: List[Stock],
        market_state: MarketState,
        regime: Regime
    ) -> List[Optional[str]]:
        """
        Update all stocks' prices using true bottom-up volatility model.

        Phase 1: Pure volatility-driven price movements
        - NO regime drift multipliers (disabled for Phase 1)
        - Volatility is primary driver of moves
        - Small positive drift for long-term growth
        - Market returns emerge from aggregation

        Args:
            stocks: List of stocks to update (modified in-place)
            market_state: Current market state (VIX, interest rate)
            regime: Current market regime

        Returns:
            List of log messages (bankruptcies)
        """
        logs = []
        regime_config = REGIMES[regime.value]

        for stock in stocks:
            if stock.status == 'bankrupt':
                continue

            # --- PHASE 2: HEALTH-BASED DRIFT ---
            # Health responds to market conditions (VIX, rates) and size
            # This creates organic regime influence without direct multipliers
            health_drift = self.calculate_health_drift(stock, market_state)

            # Total drift = base drift + health-based drift
            # Base drift provides slight positive bias
            # Health drift creates regime-appropriate bias
            drift = BASE_TICK_DRIFT + health_drift

            # Volatility: Tier-based, VIX-amplified
            tick_vol = self.calculate_tick_volatility(stock, market_state)

            # Standard normal random walk (proper Gaussian, not uniform)
            z = random.gauss(0, 1)
            vol_term = tick_vol * z

            # Log-normal price update
            change = math.exp(drift + vol_term)
            new_price = max(0.01, stock.price * change)

            # --- PHASE 3: RARE BANKRUPTCY EVENTS ---
            # Target: 0-3 bankruptcies per cycle (avg ~1)
            # Conditions: health < 0.3, price < $2, random check
            if stock.metabolic_health < 0.3 and new_price < 2.0:
                # Very low probability even when conditions are met
                # ~0.001 per tick when distressed = ~7.3 expected per cycle if always distressed
                # But distress is rare, so actual rate is much lower
                bankruptcy_prob = 0.0005
                if random.random() < bankruptcy_prob:
                    stock.status = 'bankrupt'
                    logs.append(f"Extinction: {stock.ticker} ({stock.sector}) went bankrupt")

            # --- UPDATE STOCK ---
            stock.price = new_price
            stock.current_market_cap = new_price * stock.shares_outstanding
            stock.history.append(new_price)

            # Track performance for winner identification
            stock.performance_tracker.append(new_price)

            # Update market cap tier (companies can move between tiers)
            market_cap_billions = stock.current_market_cap / 1e9
            stock.market_cap_tier = get_market_cap_tier(market_cap_billions, self.market_caps_config)

        return logs

    def update_winner_status(self, stocks: List[Stock], market_avg_return: float):
        """
        Identify winners - stocks that achieve escape velocity through sustained outperformance.
        Top ~2% of performers over tracking window become mega caps (30% of total market cap).

        Args:
            stocks: List of active stocks
            market_avg_return: Average market return over tracking window
        """
        active_stocks = [s for s in stocks if s.status == 'active']

        for stock in active_stocks:
            if len(stock.performance_tracker) >= self.tracking_window:
                # Calculate stock return over tracking window
                start_price = stock.performance_tracker[0]
                current_price = stock.price
                stock_return = (current_price / start_price) if start_price > 0 else 0

                # Check for escape velocity (sustained outperformance)
                if stock_return > market_avg_return * self.winner_threshold:
                    stock.winner_status = 'WINNER'
                elif stock_return < market_avg_return * 0.8:  # Lost winner status
                    stock.winner_status = 'NORMAL'
