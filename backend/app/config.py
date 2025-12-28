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

# Market regimes with their characteristics
REGIMES = {
    'GROWTH': {
        'label': 'Bull Market',
        'color': 'text-green-400',
        'rate_range': [0, 1.5],
        'vix_base': 15,              # Increased from 12 to keep VIX average ~18
        'drift_multiplier': 6.5,     # Target: ~30% annual (bull years)
        'health_regen': 0.0002       # Strong regeneration
    },
    'STAGNATION': {
        'label': 'Sideways Market',
        'color': 'text-yellow-400',
        'rate_range': [1.5, 3.5],
        'vix_base': 18,              # Reduced from 20
        'drift_multiplier': 1.2,     # Target: ~5% annual (normal years)
        'health_regen': 0.00001      # Minimal regeneration
    },
    'CONTRACTION': {
        'label': 'Correction',
        'color': 'text-orange-500',
        'rate_range': [3.5, 5.0],
        'vix_base': 25,              # Reduced from 28
        'drift_multiplier': -1.2,    # Target: ~-5% annual (correction years)
        'health_regen': -0.00005     # Active decay
    },
    'CRISIS': {
        'label': 'Bear Market',      # Changed from 'Sporulation (Crises)'
        'color': 'text-red-500',
        'rate_range': [4.0, 5.5],
        'vix_base': 35,              # Reduced from 45 (NO SPORULATION TRIGGER)
        'drift_multiplier': -5.0,    # Target: ~-20% annual (bear years)
        'health_regen': -0.0002      # Strong decay
    }
}

# Weighted transition probabilities (regimes persist longer for realistic annual variance)
REGIME_TRANSITIONS = {
    'GROWTH': {
        'GROWTH': 0.997,       # 99.7% stay (avg 333 ticks before transition)
        'STAGNATION': 0.002,
        'CONTRACTION': 0.001,
        'CRISIS': 0.0          # Can't go directly to CRISIS from GROWTH
    },
    'STAGNATION': {
        'GROWTH': 0.001,
        'STAGNATION': 0.994,   # 99.4% stay
        'CONTRACTION': 0.003,
        'CRISIS': 0.002
    },
    'CONTRACTION': {
        'GROWTH': 0.002,
        'STAGNATION': 0.002,
        'CONTRACTION': 0.993,  # 99.3% stay
        'CRISIS': 0.003        # Can escalate to CRISIS
    },
    'CRISIS': {
        'GROWTH': 0.001,       # Rare recovery
        'STAGNATION': 0.003,
        'CONTRACTION': 0.001,
        'CRISIS': 0.995        # 99.5% stay (bear markets persist!)
    }
}

# Simulation parameters
HISTORY_LENGTH = 60              # 60-period window for returns
TRADING_WINDOW_TICKS = 12        # 6 seconds at 500ms/tick (1 trading day)
CLOSE_WINDOW_TICKS = 8           # 4 seconds at 500ms/tick (market closed)
TICK_INTERVAL = 0.5              # 500ms
BROADCAST_INTERVAL = 1.0         # 1 second (every 2 ticks)

# API Configuration
API_KEYS = set(os.getenv("API_KEYS", "").split(","))
if not API_KEYS or API_KEYS == {""}:
    print("WARNING: No API keys configured in .env file")
