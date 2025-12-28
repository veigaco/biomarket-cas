"""
Simulation metadata endpoints.
"""
from fastapi import APIRouter, Depends, Request

from ..schemas.simulation import SimulationInfoResponse
from ..dependencies.auth import verify_api_key
from ..middleware.rate_limiter import limiter


router = APIRouter(
    prefix="/simulation",
    tags=["simulation"],
    dependencies=[Depends(verify_api_key)]
)


def get_simulation():
    """Get global simulation instance from main module"""
    from ...main import simulation
    return simulation


@router.get(
    "/info",
    response_model=SimulationInfoResponse,
    summary="Get simulation timing and metadata",
    description="""
    Get simulation timing information including:
    - Current tick count
    - Current phase (TRADING/CLOSED)
    - Time in current phase
    - Tick interval (500ms)
    - Broadcast interval (1000ms)

    **Market Phases:**
    - **TRADING**: 12 ticks (6 seconds) - normal price updates
    - **CLOSED**: 8 ticks (4 seconds) - gap pricing on reopening

    Phases alternate to simulate trading hours and overnight gaps.
    Understanding the phase is useful for agents that want to avoid
    making decisions during phase transitions.
    """
)
@limiter.limit("10/minute")
async def get_simulation_info(request: Request):
    """Get simulation timing and metadata"""
    simulation = get_simulation()

    return SimulationInfoResponse(
        tick_count=simulation.tick_count,
        phase=simulation.market_state.phase,
        time_in_phase=simulation.time_in_phase,
        tick_interval_ms=500,
        broadcast_interval_ms=1000,
        trading_window_ticks=12,
        closed_window_ticks=8
    )
