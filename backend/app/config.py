"""
Configuration constants for the market simulation engine.
Ported from src/App.jsx
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Sectors and sub-industries
SECTORS = {
    'Technology': ['Cloud', 'Semiconductors', 'AI Hardware', 'SaaS', 'Cybersecurity'],
    'Healthcare': ['Biotech', 'Pharmaceuticals', 'Medical Devices', 'Payors'],
    'Energy': ['E&P', 'Renewables', 'Midstream', 'Services'],
    'Financials': ['Banks', 'Fintech', 'Asset Management', 'Insurance'],
    'Consumer': ['Retail', 'Luxury', 'Staples', 'E-commerce'],
    'Industrials': ['Aerospace', 'Logistics', 'Infrastructure', 'Manufacturing'],
    'Communication': ['Telco', 'Social Media', 'Streaming', 'Advertising'],
    'Materials': ['Mining', 'Chemicals', 'Forestry', 'Steel']
}

# Market regimes with their characteristics (rebalanced for realistic 8-12% avg returns)
# Health bonus is 0.00001 (100x reduced), so regime drifts can be more aggressive
# Positive bias overall to offset volatility drag and compounding losses
REGIMES = {
    'GROWTH': {
        'label': 'Bull Market',
        'color': 'text-green-400',
        'rate_range': [0, 1.5],
        'vix_base': 15,              # Increased from 12 to keep VIX average ~18
        'drift_multiplier': 4.0,     # Dominant positive: Target ~40% pure GROWTH, ~12-15% mixed
        'health_regen': 0.0002       # Strong regeneration
    },
    'STAGNATION': {
        'label': 'Sideways Market',
        'color': 'text-yellow-400',
        'rate_range': [1.5, 3.5],
        'vix_base': 18,              # Reduced from 20
        'drift_multiplier': 0.1,     # Slight positive bias to offset volatility drag
        'health_regen': 0.00001      # Minimal regeneration
    },
    'CONTRACTION': {
        'label': 'Correction',
        'color': 'text-orange-500',
        'rate_range': [3.5, 5.0],
        'vix_base': 25,              # Reduced from 28
        'drift_multiplier': -0.3,    # Softened from -0.5: Target -2 to -3% annual
        'health_regen': -0.00005     # Active decay
    },
    'CRISIS': {
        'label': 'Bear Market',      # Changed from 'Sporulation (Crises)'
        'color': 'text-red-500',
        'rate_range': [4.0, 5.5],
        'vix_base': 35,              # Reduced from 45 (NO SPORULATION TRIGGER)
        'drift_multiplier': -0.8,    # Softened from -1.2: Target -5 to -8% annual
        'health_regen': -0.0002      # Strong decay
    }
}

# Weighted transition probabilities (reduced stay prob from 0.997 → 0.994)
# At 5-tick checks: 1,460 checks/cycle * 0.006 = 8.76 expected transitions
# Average stay time: 166 periods (prevents regime lock-in)
REGIME_TRANSITIONS = {
    'GROWTH': {
        'GROWTH': 0.994,       # 99.4% stay (avg 166 ticks before transition)
        'STAGNATION': 0.004,   # Doubled from 0.002
        'CONTRACTION': 0.002,  # Doubled from 0.001
        'CRISIS': 0.0          # Can't go directly to CRISIS from GROWTH
    },
    'STAGNATION': {
        'GROWTH': 0.002,       # Doubled from 0.001
        'STAGNATION': 0.991,   # Reduced from 0.994
        'CONTRACTION': 0.005,  # Increased from 0.003
        'CRISIS': 0.002
    },
    'CONTRACTION': {
        'GROWTH': 0.004,       # Doubled from 0.002
        'STAGNATION': 0.004,   # Doubled from 0.002
        'CONTRACTION': 0.989,  # Reduced from 0.993
        'CRISIS': 0.003        # Can escalate to CRISIS
    },
    'CRISIS': {
        'GROWTH': 0.002,       # Doubled from 0.001
        'STAGNATION': 0.006,   # Doubled from 0.003
        'CONTRACTION': 0.002,  # Doubled from 0.001
        'CRISIS': 0.990        # Reduced from 0.995 (bear markets still persist but can end)
    }
}

# Simulation parameters
HISTORY_LENGTH = 60              # 60-period window for returns
TRADING_WINDOW_TICKS = 12        # 6 seconds at 500ms/tick (1 trading day)
CLOSE_WINDOW_TICKS = 8           # 4 seconds at 500ms/tick (market closed)
TICK_INTERVAL = 0.02              # 20ms
BROADCAST_INTERVAL = 1.0         # 1 second (every 2 ticks)

# API Configuration
API_KEYS = set(os.getenv("API_KEYS", "").split(","))
if not API_KEYS or API_KEYS == {""}:
    print("WARNING: No API keys configured in .env file")
