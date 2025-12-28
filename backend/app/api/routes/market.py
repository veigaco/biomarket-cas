"""
Market state API endpoints.
"""
from fastapi import APIRouter, Depends, Request

from ..schemas.market import MarketStatsResponse, MarketSnapshotResponse
from ..dependencies.auth import verify_api_key
from ..middleware.rate_limiter import limiter


router = APIRouter(
    prefix="/market",
    tags=["market"],
    dependencies=[Depends(verify_api_key)]
)


def get_simulation():
    """Get global simulation instance from main module"""
    from ...main import simulation
    return simulation


@router.get(
    "/stats",
    response_model=MarketStatsResponse,
    summary="Get aggregate market statistics",
    description="""
    Get aggregate market statistics including:
    - Total market capitalization (sum of all active stocks)
    - Active stock count
    - VIX (volatility index)
    - Interest rate
    """
)
@limiter.limit("20/minute")
async def get_market_stats(request: Request):
    """Get aggregate market statistics"""
    simulation = get_simulation()

    total_cap = sum(
        s.current_market_cap
        for s in simulation.stocks
        if s.status == 'active'
    )

    active_count = sum(1 for s in simulation.stocks if s.status == 'active')

    return MarketStatsResponse(
        total_market_cap=total_cap,
        active_stocks=active_count,
        vix=simulation.market_state.vix,
        interest_rate=simulation.market_state.interest_rate
    )


@router.get(
    "/snapshot",
    response_model=MarketSnapshotResponse,
    summary="Get full market snapshot",
    description="""
    Get complete market snapshot including all stocks and market state.

    Use this for:
    - Initial state on connection
    - Reconnection after network loss
    - Polling-based clients (agents that don't use WebSocket)

    **Note:** This is a more expensive operation than specific queries.
    Prefer using specific endpoints (stocks, stats) when you only
    need partial data.

    Prices reflect real-time values when market is open, last known values when closed.
    """
)
@limiter.limit("10/minute")
async def get_market_snapshot(request: Request):
    """Get full market snapshot for external API"""
    simulation = get_simulation()

    # Determine market status
    market_status = 'open' if simulation.market_state.phase == 'TRADING' else 'closed'

    # Build external snapshot (hide internal mechanics)
    snapshot = {
        'stocks': [s.to_external_dict(market_status=market_status) for s in simulation.stocks],
        'market_state': {
            'vix': simulation.market_state.vix,
            'interest_rate': simulation.market_state.interest_rate,
            'phase': market_status
        },
        'time': simulation.time_in_phase,
        'logs': simulation.logs[-5:]  # Send last 5 logs
    }

    return MarketSnapshotResponse(**snapshot)
