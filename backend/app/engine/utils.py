"""
Utility functions for the market simulation engine.
Ported from src/App.jsx to maintain exact mathematical equivalence.
"""

import math
import random


def log_normal_random(mean: float, std_dev: float) -> float:
    """
    Generate a lognormal random variable using Box-Muller transform.
    Exact port of JavaScript logNormalRandom function.

    Args:
        mean: Mean of the underlying normal distribution
        std_dev: Standard deviation of the underlying normal distribution

    Returns:
        A lognormally distributed random number
    """
    u1 = random.random()
    u2 = random.random()
    z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return math.exp(mean + std_dev * z0)


def format_currency(val: float) -> str:
    """
    Format a currency value with T/B/M suffixes.

    Args:
        val: Currency value to format

    Returns:
        Formatted string (e.g., "$1.25T", "$500.00B")
    """
    if val >= 1e12:
        return f"${val / 1e12:.2f}T"
    if val >= 1e9:
        return f"${val / 1e9:.2f}B"
    return f"${val:.2f}"


def generate_sector_ticker(sector: str) -> str:
    """
    Generate a random ticker symbol starting with the sector's first letter.

    Args:
        sector: Sector name (e.g., "Technology", "Healthcare")

    Returns:
        3-4 character ticker (e.g., "TGXZ", "HMD")
    """
    first_letter = sector[0].upper()
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    length = 3 if random.random() > 0.5 else 4
    ticker = first_letter
    for _ in range(1, length):
        ticker += random.choice(letters)
    return ticker
