# BioMarket CAS - Backend

FastAPI microservice running the market simulation engine.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Run

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload
```

The backend will run at `http://localhost:8000`

WebSocket endpoint: `ws://localhost:8000/ws/market`

## API Endpoints

### WebSocket (for Frontend)
- `WS /ws/market` - Real-time market data (broadcast every 1s)

### REST API v1 (for Agents)
- `GET /api/v1/stocks` - List all stocks (paginated, filterable)
- `GET /api/v1/stocks/{ticker}` - Get specific stock details
- `GET /api/v1/stocks/{ticker}/history` - Get 60-period price history
- `GET /api/v1/market/regime` - Get current market regime
- `GET /api/v1/market/stats` - Get aggregate market statistics
- `GET /api/v1/market/snapshot` - Get full market snapshot
- `GET /api/v1/simulation/info` - Get simulation timing and metadata

### Other Endpoints
- `GET /` - Root endpoint (API info)
- `GET /api/health` - Health check
- `GET /api/market/state` - Current market state (legacy)
- `GET /docs` - Interactive API documentation (Swagger UI)

## For Agent Developers

### Quick Start

```bash
# 1. Get your API key (configured in .env)
# 2. Make a test request
curl -H "X-API-Key: test-key-12345" \
  http://localhost:8000/api/v1/market/stats
```

### Documentation & Examples

- **📖 Complete API Documentation**: See [`AGENT_API.md`](./AGENT_API.md)
- **🤖 Example Agent**: See [`examples/example_agent.py`](./examples/example_agent.py)
- **🌐 Interactive Docs**: Visit http://localhost:8000/docs

### Example Agent Usage

```python
from examples.example_agent import MarketObserver

# Create observer
observer = MarketObserver(
    api_key="test-key-12345",
    base_url="http://localhost:8000"
)

# Start observing (runs forever)
observer.observe_market()
```

See [`examples/README.md`](./examples/README.md) for more details.

## Architecture

- **Engine**: Runs simulation at 500ms tick interval
- **Broadcast**: Sends updates to frontend every 1 second (every 2 ticks)
- **REST API**: Authenticated endpoints for autonomous agents
- **Authentication**: Simple API key system (X-API-Key header)
- **Rate Limiting**: 10-20 requests/minute per agent, 10,000/min global
- **Data**: In-memory state (no persistence)
