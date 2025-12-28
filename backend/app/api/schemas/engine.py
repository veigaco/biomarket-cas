"""
Pydantic response models for engine endpoints.
"""
from pydantic import BaseModel, Field


class EngineInfoResponse(BaseModel):
    """Engine timing and metadata"""
    tick_count: int = Field(description="Total number of ticks since engine started")
    phase: str = Field(description="Current market status: 'open' or 'closed'")
    time_in_phase: int = Field(description="Number of ticks elapsed in current phase")
    tick_interval_ms: int = Field(description="Tick interval in milliseconds (500ms)", default=500)
    broadcast_interval_ms: int = Field(description="WebSocket broadcast interval in milliseconds (1000ms)", default=1000)
    trading_window_ticks: int = Field(description="Number of ticks when market is open (12)", default=12)
    closed_window_ticks: int = Field(description="Number of ticks when market is closed (8)", default=8)
