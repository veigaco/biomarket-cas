"""
IPO (Initial Public Offering) management for replacing bankrupt companies.

IPOs only occur during market growth periods (GROWTH regime), reflecting real-world
risk appetite dynamics where new companies enter the market during boom times.
Bankruptcies naturally accumulate during contractions and crises, waiting to be
replaced when market conditions improve.
"""

import random
from collections import deque
from typing import List, Optional

from ..models.stock import Stock
from ..models.regime import Regime
from ..config import SECTORS, HISTORY_LENGTH
from .utils import generate_sector_ticker


class IPOManager:
    """
    Manages bankruptcy replacement with IPOs.

    IPOs only occur during GROWTH regime to simulate realistic market dynamics
    where investor risk appetite drives new market entries during boom periods.
    """

    def __init__(self):
        self.stock_id_counter = 0

    def process(self, stocks: List[Stock], regime: Regime) -> Optional[dict]:
        """
        Replace bankrupt companies with IPOs during market growth.

        IPOs only trigger during GROWTH regime, reflecting real-world patterns where:
        - Bull markets = high risk appetite, new companies go public
        - Bear markets = risk aversion, bankruptcies accumulate

        **Failsafe**: If <10% of companies are active, emergency IPOs trigger
        regardless of regime to prevent market collapse.

        Args:
            stocks: List of stocks (modified in-place)
            regime: Current market regime

        Returns:
            IPO event dict if an IPO occurred, None otherwise
        """
        active_count = sum(1 for s in stocks if s.status == 'active')
        bankrupt_count = sum(1 for s in stocks if s.status == 'bankrupt')
        total_count = len(stocks)

        # Failsafe: Emergency IPOs if market is collapsing (<10% active)
        emergency_mode = active_count < (total_count * 0.1)

        # Only process IPOs during GROWTH regime (or emergency)
        if regime != Regime.GROWTH and not emergency_mode:
            return None

        # Only trigger IPOs if there are bankruptcies to replace
        # During growth periods, replace one bankruptcy at a time
        # During emergency, replace multiple to recover market
        if bankrupt_count > 0:
            # Find first bankrupt stock
            for i, stock in enumerate(stocks):
                if stock.status == 'bankrupt':
                    # Generate new IPO
                    sector = random.choice(list(SECTORS.keys()))
                    sub_industries = SECTORS[sector]
                    sub = random.choice(sub_industries)
                    new_price = 80 + random.random() * 40  # $80-$120 range

                    # Replace bankrupt company with IPO
                    stocks[i] = Stock(
                        id=f"stock-{self.stock_id_counter}",
                        ticker=generate_sector_ticker(sector),
                        name=f"{sub} {random.choice(['Inc', 'Corp', 'Group', 'Holdings'])}",
                        sector=sector,
                        sub_industry=sub,
                        price=new_price,
                        shares_outstanding=(50e9 + random.random() * 50e9) / new_price,
                        current_market_cap=50e9,
                        volatility=0.6,
                        value_score=0.4,
                        metabolic_health=1.0,
                        history=deque([new_price] * HISTORY_LENGTH, maxlen=HISTORY_LENGTH),
                        status='active'
                    )

                    self.stock_id_counter += 1

                    ipo_type = "Emergency IPO" if emergency_mode else "IPO"
                    return {
                        'ticker': stocks[i].ticker,
                        'sector': stocks[i].sector,
                        'sub_industry': stocks[i].sub_industry,
                        'emergency': emergency_mode
                    }

        return None
