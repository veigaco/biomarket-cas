"""
Main simulation engine orchestrator.
"""

import random
from collections import deque
from typing import List, Optional

from ..models.stock import Stock
from ..models.market_state import MarketState
from ..models.regime import Regime
from ..config import (
    SECTORS, REGIMES, HISTORY_LENGTH,
    TRADING_WINDOW_TICKS, CLOSE_WINDOW_TICKS
)
from .regime_manager import RegimeManager
from .stock_price import StockPriceEngine
from .ipo_manager import IPOManager
from .cycle_analytics import CycleAnalytics
from .utils import log_normal_random, generate_sector_ticker


class SimulationEngine:
    """Main orchestrator for the market simulation"""

    def __init__(self):
        self.stocks: List[Stock] = []
        self.regime_manager = RegimeManager()
        self.stock_price_engine = StockPriceEngine()
        self.ipo_manager = IPOManager()
        self.cycle_analytics = CycleAnalytics()
        self.market_state = MarketState()

        self.tick_count = 0
        self.time_in_phase = 0
        self.market_cap_history = deque(maxlen=366)  # 366 for 365T calculation
        self.logs: List[dict] = []

        # Initialize stocks
        self._generate_initial_stocks()

    def _generate_initial_stocks(self):
        """Generate initial stock portfolio (ported from generateInitialStocks)"""
        stock_id_counter = 0

        for sector, sub_industries in SECTORS.items():
            for sub in sub_industries:
                count = random.randint(2, 3)  # 2-3 companies per sub-industry

                for i in range(count):
                    is_large_cap = random.random() > 0.85
                    base_cap = (
                        (random.random() * 2e12 + 1e12) if is_large_cap
                        else (random.random() * 400e9 + 50e9)
                    )

                    initial_price = log_normal_random(4.605, 0.5)  # log(100) ≈ 4.605

                    self.stocks.append(Stock(
                        id=f"stock-{stock_id_counter}",
                        ticker=generate_sector_ticker(sector),
                        name=f"{sub} {random.choice(['Corp', 'Systems', 'Global'])}",
                        sector=sector,
                        sub_industry=sub,
                        price=initial_price,
                        shares_outstanding=base_cap / initial_price,
                        current_market_cap=base_cap,
                        volatility=(
                            random.random() * 0.15 + 0.15 if is_large_cap
                            else random.random() * 0.6 + 0.30
                        ),
                        value_score=min(1.0, max(0.1, base_cap / 3e12 + random.random() * 0.2)),
                        metabolic_health=1.0,
                        history=deque([initial_price] * HISTORY_LENGTH, maxlen=HISTORY_LENGTH),
                        status='active'
                    ))

                    stock_id_counter += 1

    async def tick(self):
        """Execute one 500ms simulation tick"""

        # 1. Update phase (TRADING/CLOSED) and handle transitions
        self._update_phase()

        # 2. Update regime (with weighted transitions)
        regime_log = self.regime_manager.update()
        if regime_log:
            self._add_log(regime_log, 'error')

        # 3. Update macro variables (VIX, interest rate)
        self._update_macro_variables()

        # 4. Update all stock prices and metabolic health
        price_logs = self.stock_price_engine.update_all(
            self.stocks,
            self.market_state,
            self.regime_manager.current_regime
        )
        for log in price_logs:
            # Track bankruptcies for cycle analytics
            if "Extinction:" in log:
                self.cycle_analytics.record_bankruptcy()
            self._add_log(log, 'error')

        # 5. Handle bankruptcies and IPOs
        # IPOs only occur during GROWTH regime (risk appetite)
        # Exception: Emergency IPOs trigger if <10% companies active (prevent collapse)
        ipo_event = self.ipo_manager.process(self.stocks, self.regime_manager.current_regime)
        if ipo_event:
            self.cycle_analytics.record_ipo()
            ipo_type = "Emergency IPO" if ipo_event.get('emergency') else "IPO"
            log_type = 'error' if ipo_event.get('emergency') else 'success'
            self._add_log(
                f"{ipo_type}: {ipo_event['ticker']} ({ipo_event['sector']} - {ipo_event['sub_industry']}) enters the market",
                log_type
            )

        # 6. Track market cap history
        total_market_cap = self._calculate_total_market_cap()
        self.market_cap_history.append(total_market_cap)

        # 7. Update cycle analytics
        self.cycle_analytics.tick_update(
            tick=self.tick_count,
            active_company_count=sum(1 for s in self.stocks if s.status == 'active'),
            regime=self.regime_manager.current_regime,
            vix=self.market_state.vix,
            interest_rate=self.market_state.interest_rate,
            total_market_cap=total_market_cap
        )

        self.tick_count += 1

    def _update_phase(self):
        """Update trading phase (TRADING/CLOSED) with gap pricing"""
        self.time_in_phase += 1

        if self.market_state.phase == 'TRADING' and self.time_in_phase >= TRADING_WINDOW_TICKS:
            self.market_state.phase = 'CLOSED'
            self.time_in_phase = 0
            self._add_log("Market closing - after-hours trading begins", 'warning')

        elif self.market_state.phase == 'CLOSED' and self.time_in_phase >= CLOSE_WINDOW_TICKS:
            self.market_state.phase = 'TRADING'
            self.time_in_phase = 0

            # Apply gap pricing (simulate overnight movements)
            self._apply_gap_pricing()
            self._add_log("Market open - gap from overnight drift", 'success')

    def _apply_gap_pricing(self):
        """Apply random gap to all stocks on market open (0.5% to 2%)"""
        for stock in self.stocks:
            if stock.status == 'bankrupt':
                continue

            gap_direction = 1 if random.random() > 0.5 else -1
            gap_magnitude = (random.random() * 0.015 + 0.005) * gap_direction
            gapped_price = stock.price * (1 + gap_magnitude)
            stock.price = max(0.1, gapped_price)

    def _update_macro_variables(self):
        """Update VIX and interest rate based on regime"""
        regime_config = self.regime_manager.get_config()

        # Interest rate mean reversion
        target_rate = sum(regime_config['rate_range']) / 2
        self.market_state.interest_rate += (
            (target_rate - self.market_state.interest_rate) * 0.05 +
            (random.random() - 0.5) * 0.02
        )

        # VIX dynamics with two-tier spike logic
        base_vix = regime_config['vix_base']

        spike = 0
        rand = random.random()
        if rand > 0.998:
            # 0.2% chance: Rare large spike (+15 to +40)
            spike = random.random() * 25 + 15
        elif rand > 0.99:
            # 1% chance: Common small spike (+5 to +12)
            spike = random.random() * 7 + 5

        decay = (self.market_state.vix - base_vix) * 0.15
        noise = (random.random() - 0.5) * 1.5

        self.market_state.vix = max(10.0, self.market_state.vix - decay + spike + noise)

    def _calculate_total_market_cap(self) -> float:
        """Calculate total market capitalization of active stocks"""
        return sum(s.current_market_cap for s in self.stocks if s.status == 'active')

    def _calculate_period_return(self, period: int) -> Optional[float]:
        """Calculate return over specified period (in ticks)"""
        if len(self.market_cap_history) <= period:
            return None

        current_cap = self.market_cap_history[-1]
        past_cap = self.market_cap_history[-(period + 1)]

        if past_cap == 0:
            return None

        return ((current_cap - past_cap) / past_cap) * 100

    def _add_log(self, msg: str, log_type: str = 'info'):
        """Add a log entry"""
        self.logs.append({
            'msg': msg,
            'type': log_type,
            'tick': self.tick_count
        })
        # Keep only last 10 logs
        if len(self.logs) > 10:
            self.logs = self.logs[-10:]

    def get_frontend_snapshot(self) -> dict:
        """
        Get current simulation state for frontend broadcast.
        Called every 2 ticks (1 second).
        """
        return {
            'stocks': [s.to_dict() for s in self.stocks],
            'market_state': self.market_state.to_dict(),
            'regime': self.regime_manager.current_regime.value,
            'time': self.time_in_phase,
            'phase': self.market_state.phase,
            'period_returns': {
                'return60': self._calculate_period_return(60),
                'return180': self._calculate_period_return(180),
                'return365': self._calculate_period_return(365)
            },
            'logs': self.logs[-5:],  # Send last 5 logs
            'analytics': self.cycle_analytics.get_analytics_snapshot(self.tick_count)
        }
