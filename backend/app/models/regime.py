"""
Regime enum and related types for market state.
"""

from enum import Enum


class Regime(str, Enum):
    """Market regime states"""
    GROWTH = "GROWTH"
    STAGNATION = "STAGNATION"
    CONTRACTION = "CONTRACTION"
    CRISIS = "CRISIS"
