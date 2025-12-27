"""
Stock data model.
"""

from dataclasses import dataclass, field
from collections import deque
from typing import Deque


@dataclass
class Stock:
    """Individual stock with price, health, and historical data"""
    id: str
    ticker: str
    name: str
    sector: str
    sub_industry: str
    price: float
    shares_outstanding: float
    current_market_cap: float
    volatility: float
    value_score: float
    metabolic_health: float
    history: Deque[float] = field(default_factory=lambda: deque(maxlen=60))
    status: str = 'active'  # 'active' or 'bankrupt'

    def to_dict(self) -> dict:
        """
        Convert to JSON-serializable dict for frontend.
        Uses camelCase for JavaScript compatibility.
        """
        return {
            'id': self.id,
            'ticker': self.ticker,
            'name': self.name,
            'sector': self.sector,
            'subIndustry': self.sub_industry,  # camelCase for JS
            'price': round(self.price, 2),
            'sharesOutstanding': self.shares_outstanding,
            'currentMarketCap': self.current_market_cap,
            'volatility': round(self.volatility, 4),
            'valueScore': round(self.value_score, 4),
            'metabolicHealth': round(self.metabolic_health, 4),
            'history': list(self.history),
            'status': self.status
        }
