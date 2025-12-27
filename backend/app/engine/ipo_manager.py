"""
IPO (Initial Public Offering) management for replacing bankrupt companies.
"""

import random
from collections import deque
from typing import List, Optional

from ..models.stock import Stock
from ..config import SECTORS, HISTORY_LENGTH
from .utils import generate_sector_ticker


class IPOManager:
    """Manages bankruptcy replacement with IPOs"""

    def __init__(self):
        self.stock_id_counter = 0

    def process(self, stocks: List[Stock]) -> Optional[dict]:
        """
        Replace bankrupt companies with IPOs when >10% are dead.

        Args:
            stocks: List of stocks (modified in-place)

        Returns:
            IPO event dict if an IPO occurred, None otherwise
        """
        active_count = sum(1 for s in stocks if s.status == 'active')

        if active_count < len(stocks) * 0.9:
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

                    return {
                        'ticker': stocks[i].ticker,
                        'sector': sector
                    }

        return None
