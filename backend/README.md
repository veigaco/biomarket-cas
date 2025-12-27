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

- `GET /` - Root endpoint (API info)
- `GET /api/health` - Health check
- `GET /api/market/state` - Current market state
- `WS /ws/market` - WebSocket for real-time market data

## Architecture

- **Engine**: Runs simulation at 500ms tick interval
- **Broadcast**: Sends updates to frontend every 1 second (every 2 ticks)
- **Data**: In-memory state (no persistence)
