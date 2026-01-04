"""
IPO (Initial Public Offering) management for replacing bankrupt companies.

Bottom-up model: IPOs follow realistic size distribution (mostly small/mid caps).
IPOs only occur during market growth periods (GROWTH regime), reflecting real-world
risk appetite dynamics where new companies enter the market during boom times.
"""

import random
from collections import deque
from typing import List, Optional

from ..models.stock import Stock
from ..models.regime import Regime
from ..config import SECTORS, HISTORY_LENGTH
from ..config.loader import get_cached_config, get_market_cap_tier
from .utils import generate_sector_ticker


class IPOManager:
    """
    Manages bankruptcy replacement with IPOs.

    Bottom-up model: New companies start as small/mid caps with tier-appropriate volatility.
    IPOs only occur during GROWTH regime to simulate realistic market dynamics.
    """

    def __init__(self):
        self.stock_id_counter = 0
        # Phase 3: Target 3-6 IPOs per cycle during GROWTH
        # Check every 50 ticks = 146 checks per cycle
        # But only ~30% of cycle is GROWTH, so ~44 effective checks
        # Probability 0.10 per check = ~4.4 IPOs per cycle in GROWTH
        self.ipo_probability_per_check = 0.10
        self.ticks_since_last_check = 0
        self.check_interval = 50  # Check every 50 ticks
        self.regime_behaviors_config = get_cached_config('regime_behaviors')
        self.market_caps_config = get_cached_config('market_caps')

    def _generate_ipo_stock(self, sector: str, sub_industry: str) -> Stock:
        """
        Generate a new IPO stock with realistic size distribution.

        Bottom-up model: 85% SMALL_CAP, 15% MID_CAP (per regime_behaviors.json).
        Each tier gets tier-specific volatility and market cap range.

        Args:
            sector: Stock sector
            sub_industry: Stock sub-industry

        Returns:
            New Stock object with bottom-up model fields initialized
        """
        # 1. Select tier based on IPO distribution (85% SMALL_CAP, 15% MID_CAP)
        ipo_distribution = self.regime_behaviors_config['ipo_mechanics']['new_company_tier_distribution']
        rand = random.random()
        if rand < ipo_distribution['SMALL_CAP']:
            tier = 'SMALL_CAP'
        else:
            tier = 'MID_CAP'

        # 2. Generate market cap within tier range
        tier_config = self.market_caps_config['tiers'][tier]
        min_cap = tier_config['min_cap_billions'] * 1e9
        max_cap = tier_config['max_cap_billions'] * 1e9
        market_cap = min_cap + random.random() * (max_cap - min_cap)

        # 3. Assign tier-specific base volatility
        vol_min, vol_max = tier_config['base_volatility_range']
        base_volatility = (vol_min + random.random() * (vol_max - vol_min)) / 100

        # 4. Generate initial price and shares
        initial_price = 80 + random.random() * 40  # $80-$120 IPO price range
        shares_outstanding = market_cap / initial_price

        # 5. Create Stock with bottom-up model fields
        new_stock = Stock(
            id=f"stock-{self.stock_id_counter}",
            ticker=generate_sector_ticker(sector),
            name=f"{sub_industry} {random.choice(['Inc', 'Corp', 'Group', 'Holdings'])}",
            sector=sector,
            sub_industry=sub_industry,
            price=initial_price,
            shares_outstanding=shares_outstanding,
            current_market_cap=market_cap,
            volatility=base_volatility,
            value_score=0.4,  # New companies start with neutral value score
            metabolic_health=1.0,  # New companies start healthy
            history=deque([initial_price] * HISTORY_LENGTH, maxlen=HISTORY_LENGTH),
            status='active',
            # Bottom-up model fields
            market_cap_tier=tier,
            winner_status='NORMAL',
            base_volatility=base_volatility,
            performance_tracker=deque([initial_price], maxlen=1460)
        )

        self.stock_id_counter += 1
        return new_stock

    def process(self, stocks: List[Stock], regime: Regime, market_state=None) -> Optional[dict]:
        """
        Phase 3: Independent IPO generation during favorable market conditions.

        IPOs are completely decoupled from bankruptcies. They occur as independent
        events based on market conditions (regime, VIX).

        IPO Logic:
        - Check every 50 ticks
        - During GROWTH with VIX < 25: ~3.5% chance per check
        - Target: 2-8 IPOs per cycle (avg ~5 during typical GROWTH exposure)
        - Max ~110 active stocks (prevent market bloat)

        Args:
            stocks: List of stocks (modified in-place)
            regime: Current market regime
            market_state: Current market state (for VIX check)

        Returns:
            IPO event dict if an IPO occurred, None otherwise
        """
        self.ticks_since_last_check += 1

        if self.ticks_since_last_check < self.check_interval:
            return None

        self.ticks_since_last_check = 0

        active_count = sum(1 for s in stocks if s.status == 'active')

        # Don't add IPOs if market is already large
        if active_count >= 110:
            return None

        # IPOs only during GROWTH regime with low VIX
        vix = market_state.vix if market_state else 20
        if regime != Regime.GROWTH:
            return None
        if vix > 25:
            return None

        # Random IPO generation
        if random.random() < self.ipo_probability_per_check:
            sector = random.choice(list(SECTORS.keys()))
            sub_industries = SECTORS[sector]
            sub = random.choice(sub_industries)

            # Generate new IPO (always adds, never replaces)
            new_stock = self._generate_ipo_stock(sector, sub)
            stocks.append(new_stock)

            return {
                'ticker': new_stock.ticker,
                'sector': new_stock.sector,
                'sub_industry': new_stock.sub_industry,
                'market_cap': new_stock.current_market_cap,
                'emergency': False
            }

        return None
