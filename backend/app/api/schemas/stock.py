"""
Pydantic response models for stock endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional


class StockResponse(BaseModel):
    """
    Single stock response for external API.
    Price reflects last known value. Check marketStatus to determine if real-time or delayed.
    """
    id: str
    ticker: str
    name: str
    sector: str
    subIndustry: str = Field(alias="sub_industry", description="Stock sub-industry classification")
    price: float = Field(description="Stock price (real-time if market open, last known if closed)")
    marketStatus: str = Field(description="Market status: 'open' or 'closed'")
    sharesOutstanding: float = Field(alias="shares_outstanding", description="Total shares outstanding")
    currentMarketCap: float = Field(alias="current_market_cap", description="Current market capitalization")
    volatility: float = Field(description="Stock volatility metric")
    valueScore: float = Field(alias="value_score", description="Value score metric")

    model_config = {
        "populate_by_name": True
    }


class StockHistoryResponse(BaseModel):
    """
    Price history response for a stock.
    Returns historical prices for the requested number of ticks.
    """
    ticker: str
    history: list[float] = Field(description="Historical prices (most recent last)")
    ticks: int = Field(description="Number of ticks in history")
    marketStatus: str = Field(description="Current market status: 'open' or 'closed'")
