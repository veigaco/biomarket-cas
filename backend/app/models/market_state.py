"""
Market state data model.
"""

from dataclasses import dataclass


@dataclass
class MarketState:
    """Current market macro state"""
    vix: float = 15.5
    interest_rate: float = 1.25
    phase: str = 'TRADING'  # 'TRADING' or 'CLOSED'

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict for frontend (camelCase fields)"""
        return {
            'vix': round(self.vix, 2),
            'interestRate': round(self.interest_rate, 2),
            'phase': self.phase
        }
