"""
Regime management with weighted state transitions.
"""

import random
from typing import Optional

from ..models.regime import Regime
from ..config import REGIME_TRANSITIONS, REGIMES


class RegimeManager:
    """Manages market regime state machine with weighted transitions"""

    def __init__(self, initial_regime: Regime = Regime.GROWTH):
        self.current_regime = initial_regime
        self.ticks_in_regime = 0
        self.ticks_since_last_check = 0

    def update(self) -> Optional[str]:
        """
        Update regime based on weighted transition probabilities.
        Only checks transitions every 10 ticks to prevent regime lock-in.

        Returns:
            Log message if regime changed, None otherwise
        """
        self.ticks_since_last_check += 1
        self.ticks_in_regime += 1

        # Only check transitions every 5 ticks (0.1 period)
        # More frequent checks prevent regime lock-in while maintaining realistic transition rates
        if self.ticks_since_last_check < 5:
            return None

        self.ticks_since_last_check = 0

        transitions = REGIME_TRANSITIONS[self.current_regime.value]
        rand = random.random()
        cumulative = 0.0

        for next_regime_str, prob in transitions.items():
            cumulative += prob
            if rand < cumulative:
                if next_regime_str != self.current_regime.value:
                    old_regime = self.current_regime
                    self.current_regime = Regime(next_regime_str)
                    self.ticks_in_regime = 0  # Reset counter on regime change
                    new_label = REGIMES[next_regime_str]['label']
                    return f"Regime Shift: {new_label}"
                break

        return None

    def get_config(self) -> dict:
        """Get current regime configuration"""
        return REGIMES[self.current_regime.value]
