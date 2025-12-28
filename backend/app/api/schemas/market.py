"""
Pydantic response models for market endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional


class MarketStatsResponse(BaseModel):
    """Aggregate market statistics"""
    total_market_cap: float = Field(description="Total market capitalization (all active stocks)")
    active_stocks: int = Field(description="Number of active stocks")
    vix: float = Field(description="Current VIX (volatility index)")
    interest_rate: float = Field(description="Current interest rate")


class MarketSnapshotResponse(BaseModel):
    """Full market snapshot for external API"""
    stocks: list = Field(description="All stocks with observable data")
    market_state: dict = Field(description="Market state (VIX, interest rate, phase)")
    time: int = Field(description="Time in current phase", default=0)
    logs: list = Field(description="Recent event logs", default=[])
