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
        self.ipo_probability_per_period = 0.3  # 30% chance of IPO per period during GROWTH
        self.ticks_since_last_check = 0

    def process(self, stocks: List[Stock], regime: Regime) -> Optional[dict]:
        """
        Independent IPO generation during market growth.

        IPOs are decoupled from bankruptcies - they occur randomly during GROWTH
        based on probability, not as immediate 1:1 replacements. This creates
        realistic lag and correlation <1.0 between bankruptcies and IPOs.

        IPO Logic:
        - Check once per period (20 ticks) to reduce coupling frequency
        - During GROWTH: 30% chance of IPO per period
        - IPO prioritizes replacing bankruptcies, but can also grow market (<100 stocks)
        - Emergency mode: Guaranteed IPO if <10% active to prevent collapse

        Args:
            stocks: List of stocks (modified in-place)
            regime: Current market regime

        Returns:
            IPO event dict if an IPO occurred, None otherwise
        """
        self.ticks_since_last_check += 1

        # Only process once per period (20 ticks) to decouple from bankruptcies
        if self.ticks_since_last_check < 20:
            return None

        self.ticks_since_last_check = 0

        active_count = sum(1 for s in stocks if s.status == 'active')
        bankrupt_count = sum(1 for s in stocks if s.status == 'bankrupt')
        total_count = len(stocks)

        # Failsafe: Emergency IPOs if market is collapsing (<10% active)
        emergency_mode = active_count < (total_count * 0.1)

        # Independent IPO generation during GROWTH (not tied to bankruptcies)
        if regime == Regime.GROWTH or emergency_mode:
            # Random IPO generation (emergency mode guarantees IPO)
            if random.random() < self.ipo_probability_per_period or emergency_mode:
                # Prioritize replacing bankruptcies, but allow market growth
                if bankrupt_count > 0:
                    # Replace a bankrupt stock with IPO
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
                elif len(stocks) < 100:
                    # Market growth: Add new stock instead of replacing
                    sector = random.choice(list(SECTORS.keys()))
                    sub_industries = SECTORS[sector]
                    sub = random.choice(sub_industries)
                    new_price = 80 + random.random() * 40  # $80-$120 range

                    new_stock = Stock(
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

                    stocks.append(new_stock)
                    self.stock_id_counter += 1

                    return {
                        'ticker': new_stock.ticker,
                        'sector': new_stock.sector,
                        'sub_industry': new_stock.sub_industry,
                        'emergency': False
                    }

        return None
