"""
FastAPI main application with market simulation WebSocket streaming.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .engine.simulation import SimulationEngine
from .api.websocket import manager
from .api.middleware.rate_limiter import limiter
from .api.middleware.request_logger import RequestLoggingMiddleware
from .api.routes import stocks, market, engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global simulation instance
simulation: SimulationEngine = None
simulation_task = None


async def simulation_loop():
    """
    Main simulation loop: runs at 500ms intervals, broadcasts every 1s (every 2 ticks).
    """
    global simulation

    tick_counter = 0
    next_tick_time = time.time()

    logger.info("Simulation loop started")

    while True:
        try:
            # Execute tick
            await simulation.tick()
            tick_counter += 1

            # Broadcast every 2 ticks (1 second)
            if tick_counter % 2 == 0:
                snapshot = simulation.get_frontend_snapshot()
                await manager.broadcast({
                    'type': 'update',
                    'data': snapshot
                })

            # Drift-corrected sleep (compensates for tick processing time)
            next_tick_time += 0.5  # 500ms
            sleep_duration = max(0, next_tick_time - time.time())
            await asyncio.sleep(sleep_duration)

        except Exception as e:
            logger.error(f"Simulation loop error: {e}", exc_info=True)
            await asyncio.sleep(0.5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: startup and shutdown.
    """
    global simulation, simulation_task

    # Startup
    logger.info("Starting market simulation engine...")
    simulation = SimulationEngine()
    simulation_task = asyncio.create_task(simulation_loop())
    logger.info("Market simulation engine started")

    yield

    # Shutdown
    logger.info("Shutting down market simulation engine...")
    if simulation_task:
        simulation_task.cancel()
        try:
            await simulation_task
        except asyncio.CancelledError:
            pass
    logger.info("Market simulation engine stopped")


# Create FastAPI app
app = FastAPI(
    title="BioMarket CAS - Market Simulation Engine",
    description="""
    Real-time market simulation with WebSocket streaming and REST API.

    ## Overview
    This simulation models a complex adaptive system (CAS) market with:
    - **Ticks**: 500ms intervals (2 ticks = 1 second)
    - **Phases**: TRADING (12 ticks / 6s) and CLOSED (8 ticks / 4s)
    - **Regimes**: GROWTH, STAGNATION, CONTRACTION, CRISIS
    - **Events**: IPOs, bankruptcies, regime transitions

    ## Data Access
    - **WebSocket**: Real-time updates at `/ws/market` (broadcast every 1s)
    - **REST API**: Poll endpoints for current state

    ## Authentication
    All API v1 endpoints require an `X-API-Key` header.

    ## Rate Limits
    - Stock/market queries: 60 requests/minute per agent
    - History queries: 30 requests/minute per agent
    - Snapshot (heavy): 20 requests/minute per agent
    - Global limit: 10,000 requests/minute per agent

    ## Philosophy
    This market is a pure data source. It exposes observable market data
    (prices, regimes, stats) but not internal mechanics (formulas, weights,
    transition probabilities). External systems observe and learn patterns.
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include API v1 routers
app.include_router(stocks.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")
app.include_router(engine.router, prefix="/api/v1")


@app.websocket("/ws/market")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time market data streaming.
    """
    await manager.connect(websocket)

    try:
        # Send initial state
        initial_snapshot = simulation.get_frontend_snapshot()
        await websocket.send_json({
            'type': 'initial',
            'data': initial_snapshot
        })

        # Keep connection alive and listen for client messages
        while True:
            # Wait for client messages (for future control commands)
            data = await websocket.receive_text()
            # TODO: Handle control commands (pause/resume, etc.)
            logger.info(f"Received message: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'tick': simulation.tick_count if simulation else 0,
        'active_connections': len(manager.active_connections)
    }


@app.get("/api/market/state")
async def get_market_state():
    """Get current market state (for reconnection or direct API access)"""
    if not simulation:
        return {'error': 'Simulation not initialized'}

    return simulation.get_frontend_snapshot()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        'message': 'BioMarket CAS - Market Simulation Engine',
        'websocket': '/ws/market',
        'health': '/api/health',
        'state': '/api/market/state'
    }
