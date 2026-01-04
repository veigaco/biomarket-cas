"""
Stock data model.
"""

from dataclasses import dataclass, field
from collections import deque
from typing import Deque


@dataclass
class Stock:
    """
    Individual stock with price, health, and historical data.

    Bottom-up model: Market cap tier determines volatility, drift sensitivity,
    and crisis resilience. Winners identified through sustained outperformance.
    """
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

    # Bottom-up model fields
    market_cap_tier: str = 'SMALL_CAP'  # MEGA_CAP, LARGE_CAP, MID_CAP, SMALL_CAP
    winner_status: str = 'NORMAL'  # 'NORMAL' or 'WINNER' (escape velocity achieved)
    base_volatility: float = 0.35  # Tier-specific base volatility (before VIX scaling)
    performance_tracker: Deque[float] = field(default_factory=lambda: deque(maxlen=1460))  # 2 cycles

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
            'status': self.status,
            'marketCapTier': self.market_cap_tier,
            'winnerStatus': self.winner_status,
            'baseVolatility': round(self.base_volatility, 4)
        }

    def to_external_dict(self, market_status: str = 'open') -> dict:
        """
        Convert to JSON-serializable dict for external API.
        Hides internal mechanics (metabolic_health, status, history).
        Always includes price (real-time if open, last known if closed).

        Observable metrics only - agents must infer company health from
        price movements, volatility, and market cap changes.

        Args:
            market_status: 'open' or 'closed'
        """
        return {
            'id': self.id,
            'ticker': self.ticker,
            'name': self.name,
            'sector': self.sector,
            'subIndustry': self.sub_industry,
            'price': round(self.price, 2),
            'marketStatus': market_status,
            'sharesOutstanding': self.shares_outstanding,
            'currentMarketCap': self.current_market_cap,
            'volatility': round(self.volatility, 4),
            # valueScore removed - internal valuation metric
        }
