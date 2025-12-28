"""
Stock-related API endpoints.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from typing import Optional

from ..schemas.stock import StockResponse, StockHistoryResponse
from ..schemas.common import PaginatedResponse
from ..dependencies.auth import verify_api_key
from ..middleware.rate_limiter import limiter


router = APIRouter(
    prefix="/stocks",
    tags=["stocks"],
    dependencies=[Depends(verify_api_key)]
)


def get_simulation():
    """Get global simulation instance from main module"""
    from ...main import simulation
    return simulation


@router.get(
    "",
    response_model=PaginatedResponse[StockResponse],
    summary="List all stocks with pagination and filtering",
    description="""
    List all stocks with optional filtering by sector and status.

    Returns current stock data including prices and market status.
    Price reflects real-time value when market is open, last known value when closed.

    **Filtering:**
    - `sector`: Filter by sector (Technology, Healthcare, Finance, etc.)
    - `status`: Filter by status ('active' or 'bankrupt')

    **Pagination:**
    - `page`: Page number (starts at 1)
    - `page_size`: Items per page (max 100)
    """
)
@limiter.limit("20/minute")
async def list_stocks(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    status: Optional[str] = Query("active", description="Filter by status (active/bankrupt)")
):
    """List all stocks with pagination and filtering"""
    simulation = get_simulation()

    # Filter stocks
    filtered = [
        s for s in simulation.stocks
        if (sector is None or s.sector == sector)
        and (status is None or s.status == status)
    ]

    # Paginate
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = filtered[start:end]

    # Determine market status
    market_status = 'open' if simulation.market_state.phase == 'TRADING' else 'closed'

    return PaginatedResponse(
        data=[StockResponse(**s.to_external_dict(market_status=market_status)) for s in page_data],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get(
    "/{ticker}",
    response_model=StockResponse,
    summary="Get stock details by ticker",
    description="""
    Returns current observable data for a specific stock.

    Price reflects real-time value when market is open, last known value when closed.
    Check marketStatus field to determine if price is real-time or delayed.
    """
)
@limiter.limit("20/minute")
async def get_stock(request: Request, ticker: str):
    """Get detailed information for a stock by ticker"""
    simulation = get_simulation()

    stock = next((s for s in simulation.stocks if s.ticker == ticker), None)

    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    # Determine market status
    market_status = 'open' if simulation.market_state.phase == 'TRADING' else 'closed'

    return StockResponse(**stock.to_external_dict(market_status=market_status))


@router.get(
    "/{ticker}/history",
    response_model=StockHistoryResponse,
    summary="Get price history for a stock",
    description="""
    Get historical price data for a stock.

    Returns price history for the requested number of ticks (max 60).
    History buffer maintains the last 60 prices.

    Query Parameters:
    - ticks: Number of historical ticks to return (default: 60, max: 60)
    """
)
@limiter.limit("10/minute")
async def get_stock_history(
    request: Request,
    ticker: str,
    ticks: int = Query(60, ge=1, le=60, description="Number of ticks to return")
):
    """Get price history for a stock"""
    simulation = get_simulation()

    stock = next((s for s in simulation.stocks if s.ticker == ticker), None)

    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    # Get requested number of ticks from history
    history_list = list(stock.history)
    requested_history = history_list[-ticks:] if len(history_list) >= ticks else history_list

    # Determine market status
    market_status = 'open' if simulation.market_state.phase == 'TRADING' else 'closed'

    return StockHistoryResponse(
        ticker=ticker,
        history=requested_history,
        ticks=len(requested_history),
        marketStatus=market_status
    )
