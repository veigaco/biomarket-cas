"""
Engine metadata endpoints.
"""
from fastapi import APIRouter, Depends, Request

from ..schemas.engine import EngineInfoResponse
from ..dependencies.auth import verify_api_key
from ..middleware.rate_limiter import limiter


router = APIRouter(
    prefix="/engine",
    tags=["engine"],
    dependencies=[Depends(verify_api_key)]
)


def get_simulation():
    """Get global simulation instance from main module"""
    from ...main import simulation
    return simulation


@router.get(
    "/info",
    response_model=EngineInfoResponse,
    summary="Get engine timing and metadata",
    description="""
    Get engine timing information including:
    - Current tick count
    - Current market status (open/closed)
    - Time in current phase
    - Tick interval (500ms)
    - Broadcast interval (1000ms)

    **Market Hours:**
    - **Open**: 12 ticks - real-time price updates
    - **Closed**: 8 ticks - prices reflect last known values

    Market hours alternate to simulate trading sessions and overnight periods.
    """
)
@limiter.limit("10/minute")
async def get_engine_info(request: Request):
    """Get engine timing and metadata"""
    simulation = get_simulation()

    # Convert phase to market status
    market_status = 'open' if simulation.market_state.phase == 'TRADING' else 'closed'

    return EngineInfoResponse(
        tick_count=simulation.tick_count,
        phase=market_status,
        time_in_phase=simulation.time_in_phase,
        tick_interval_ms=500,
        broadcast_interval_ms=1000,
        trading_window_ticks=12,
        closed_window_ticks=8
    )
