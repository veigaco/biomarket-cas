"""
Stock price dynamics engine with metabolic health system.
"""

import math
import random
from typing import List, Optional

from ..models.stock import Stock
from ..models.market_state import MarketState
from ..models.regime import Regime
from ..config import REGIMES, HISTORY_LENGTH


class StockPriceEngine:
    """Handles stock price updates and metabolic health calculations"""

    def update_all(
        self,
        stocks: List[Stock],
        market_state: MarketState,
        regime: Regime
    ) -> List[Optional[str]]:
        """
        Update all stocks' prices and metabolic health.

        Args:
            stocks: List of stocks to update (modified in-place)
            market_state: Current market state (VIX, interest rate)
            regime: Current market regime

        Returns:
            List of log messages (extinctions)
        """
        logs = []
        regime_config = REGIMES[regime.value]

        for stock in stocks:
            if stock.status == 'bankrupt':
                continue

            # --- METABOLIC HEALTH SYSTEM ---

            # 1. Base metabolic cost
            base_cost = (
                (market_state.interest_rate / 5.0) * 0.0008 +
                (market_state.vix / 90.0) * 0.001
            )

            # 2. Performance-based regeneration
            recent_return = 0.0
            if len(stock.history) >= 5:
                recent_price = stock.history[-5]
                if recent_price > 0:
                    recent_return = (stock.price - recent_price) / recent_price

            performance_regen = recent_return * 0.02

            # 3. Regime-based adjustment
            regime_regen = regime_config['health_regen']

            # 4. Net health change
            health_change = -base_cost + performance_regen + regime_regen
            health = min(1.2, max(0.0, stock.metabolic_health + health_change))

            # --- PRICE DYNAMICS ---

            # 1. Base drift with regime multiplier
            regime_multiplier = regime_config['drift_multiplier']
            base_drift = (stock.value_score * 0.00002) * regime_multiplier

            # 2. No crisis shocks
            shock = 0

            # 3. Health bonus
            health_bonus = (health - 0.5) * 0.001

            # 4. Final drift
            drift = base_drift + health_bonus + shock

            # 5. Volatility
            vol = (stock.volatility / 35) * (market_state.vix / 14)
            change = math.exp(drift + vol * (random.random() - 0.5))

            new_price = max(0.1, stock.price * change)

            # --- EXTINCTION LOGIC ---
            if new_price < 0.5 or health <= 0:
                stock.status = 'bankrupt'
                stock.price = 0
                stock.current_market_cap = 0
                logs.append(f"Extinction: {stock.ticker}")
                continue

            # --- UPDATE STOCK ---
            stock.price = new_price
            stock.current_market_cap = new_price * stock.shares_outstanding
            stock.metabolic_health = health
            stock.history.append(new_price)

        return logs
