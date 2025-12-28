# Agent API Documentation

**BioMarket CAS - Market Engine API**

API reference for external systems observing the market engine.

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Market Mechanics](#market-mechanics)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

The BioMarket CAS Market Engine provides a REST API for external systems to observe and analyze market data in real-time.

### Base URL

```
http://localhost:8000
```

### Authentication

All API endpoints require authentication via the `X-API-Key` header:

```
X-API-Key: your-api-key-here
```

**To obtain an API key**, contact your system administrator.

### Rate Limits

| Endpoint Type | Limit | Polling Interval |
|---------------|-------|------------------|
| Stock queries (list, get) | 60 requests/minute | ~1 second |
| Market stats, Engine info | 60 requests/minute | ~1 second |
| Stock history | 30 requests/minute | ~2 seconds |
| Market snapshot (heavy) | 20 requests/minute | ~3 seconds |
| **Global (per agent)** | 10,000 requests/minute | - |

**Rate limit exceeded response:**
```json
HTTP 429 Too Many Requests
{"error": "Rate limit exceeded"}
```

**Note:** Market broadcasts every 2 ticks (1000ms), so polling faster than 1 second for most endpoints won't give you newer data.

---

## Quick Start

### 1. Test Your Connection

```bash
# Health check (no auth required)
curl http://localhost:8000/api/health
```

### 2. Make Your First Request

```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/v1/market/stats
```

**Example Response:**
```json
{
  "total_market_cap": 48620359170035.77,
  "active_stocks": 85,
  "vix": 15.68,
  "interest_rate": 0.76
}
```

### 3. Get Market Status

```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/v1/engine/info
```

**Example Response:**
```json
{
  "tick_count": 150,
  "phase": "open",
  "time_in_phase": 5,
  "tick_interval_ms": 500,
  "broadcast_interval_ms": 1000,
  "trading_window_ticks": 12,
  "closed_window_ticks": 8
}
```

---

## API Endpoints

All endpoints require `X-API-Key` header and are prefixed with `/api/v1`.

### Stocks

#### `GET /api/v1/stocks`

List all active stocks with pagination and filtering.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `page_size` (int, default: 50, max: 100): Items per page
- `sector` (string, optional): Filter by sector
- `status` (string, default: "active"): Filter by status ("active" or "bankrupt")

**To get all tickers across all sectors**, fetch with `page_size=100` and iterate through pages.

**Example Request:**
```bash
curl -H "X-API-Key: your-key" \
  'http://localhost:8000/api/v1/stocks?page_size=100'
```

**Example Response:**
```json
{
  "data": [
    {
      "id": "stock-0",
      "ticker": "TWH",
      "name": "Cloud Systems",
      "sector": "Technology",
      "subIndustry": "Cloud",
      "price": 56.71,
      "marketStatus": "open",
      "sharesOutstanding": 4353772767.08,
      "currentMarketCap": 246908228119.31,
      "volatility": 0.7412
    }
  ],
  "total": 85,
  "page": 1,
  "page_size": 100,
  "total_pages": 1
}
```

**Response Fields:**
- `price`: Real-time price when market is open, last known price when market is closed
- `marketStatus`: Current market status ("open" or "closed")
- `volatility`: Stock volatility metric (higher = more volatile)
- `sharesOutstanding`: Total shares outstanding
- `currentMarketCap`: Current market capitalization

**Rate Limit:** 60 requests/minute

---

#### `GET /api/v1/stocks/{ticker}`

Get details for a specific stock.

**Path Parameters:**
- `ticker` (string): Stock ticker symbol

**Example Request:**
```bash
curl -H "X-API-Key: your-key" \
  http://localhost:8000/api/v1/stocks/TWH
```

**Example Response:**
```json
{
  "id": "stock-0",
  "ticker": "TWH",
  "name": "Cloud Systems",
  "sector": "Technology",
  "subIndustry": "Cloud",
  "price": 60.39,
  "marketStatus": "open",
  "sharesOutstanding": 4353772767.08,
  "currentMarketCap": 262909501228.27,
  "volatility": 0.7412
}
```

**Note:** Check `marketStatus` field to determine if price is real-time ("open") or delayed ("closed").

**Rate Limit:** 60 requests/minute

---

#### `GET /api/v1/stocks/{ticker}/history`

Get historical price data for a stock.

**Path Parameters:**
- `ticker` (string): Stock ticker symbol

**Query Parameters:**
- `ticks` (int, default: 60, max: 60): Number of historical ticks to return

**Example Request:**
```bash
# Get last 30 ticks
curl -H "X-API-Key: your-key" \
  'http://localhost:8000/api/v1/stocks/TWH/history?ticks=30'
```

**Example Response:**
```json
{
  "ticker": "TWH",
  "history": [52.46, 52.86, 53.08, 53.36, ..., 60.39],
  "ticks": 30,
  "marketStatus": "open"
}
```

**Response Fields:**
- `history`: Array of historical prices (most recent last)
- `ticks`: Actual number of ticks returned
- `marketStatus`: Current market status

**Note:** History only includes prices from when market was open. Maximum 60 ticks available.

**Rate Limit:** 30 requests/minute

---

### Market

#### `GET /api/v1/market/stats`

Get aggregate market statistics.

**Example Request:**
```bash
curl -H "X-API-Key: your-key" \
  http://localhost:8000/api/v1/market/stats
```

**Example Response:**
```json
{
  "total_market_cap": 48620359170035.77,
  "active_stocks": 85,
  "vix": 15.68,
  "interest_rate": 0.76
}
```

**Response Fields:**
- `total_market_cap`: Sum of all active stock market caps
- `active_stocks`: Count of active (non-bankrupt) stocks
- `vix`: Current volatility index
- `interest_rate`: Current interest rate

**Rate Limit:** 60 requests/minute

---

#### `GET /api/v1/market/snapshot`

Get complete market snapshot (all stocks + market state).

**Example Request:**
```bash
curl -H "X-API-Key: your-key" \
  http://localhost:8000/api/v1/market/snapshot
```

**Example Response:**
```json
{
  "stocks": [
    {
      "id": "stock-0",
      "ticker": "TWH",
      "price": 60.39,
      "marketStatus": "open",
      ...
    },
    ...
  ],
  "market_state": {
    "vix": 15.68,
    "interest_rate": 0.76,
    "phase": "open"
  },
  "time": 5,
  "logs": ["Market activity logs appear here"]
}
```

**Note:** This is a more expensive operation. Prefer specific endpoints when you only need partial data.

**Rate Limit:** 20 requests/minute

---

### Engine

#### `GET /api/v1/engine/info`

Get engine timing and metadata.

**Example Request:**
```bash
curl -H "X-API-Key: your-key" \
  http://localhost:8000/api/v1/engine/info
```

**Example Response:**
```json
{
  "tick_count": 150,
  "phase": "open",
  "time_in_phase": 5,
  "tick_interval_ms": 500,
  "broadcast_interval_ms": 1000,
  "trading_window_ticks": 12,
  "closed_window_ticks": 8
}
```

**Response Fields:**
- `tick_count`: Total ticks since engine started
- `phase`: Current market status ("open" or "closed")
- `time_in_phase`: Ticks elapsed in current phase
- `tick_interval_ms`: Tick interval (500ms)
- `broadcast_interval_ms`: WebSocket broadcast interval (1000ms)
- `trading_window_ticks`: Ticks per open market period (12)
- `closed_window_ticks`: Ticks per closed market period (8)

**Rate Limit:** 60 requests/minute

---

## Market Mechanics

### Market Hours

The market alternates between two states:

- **Open**: 12 ticks - Real-time price updates available
- **Closed**: 8 ticks - Prices reflect last known values from open hours

**1 Tick = 500ms**

### Price Data

- **When market is open**: All prices are real-time (`marketStatus: "open"`)
- **When market is closed**: All prices reflect last known values (`marketStatus: "closed"`)

### Stock Lifecycle

**Active Stocks:**
- Observable through stock list
- Prices update during open market hours

**Market Dynamics:**
- Companies naturally expand and contract over time
- Some companies may fail and exit the market
- New companies may enter the market at various times
- These events are observable via logs and stock list changes
- Filter by status: `GET /api/v1/stocks?status=active` or `status=bankrupt`

### Observable Data

✅ **Available to external systems:**
- Stock prices (real-time when open, delayed when closed)
- Market capitalization
- VIX (volatility index)
- Interest rate
- Market status (open/closed)
- Stock volatility
- Shares outstanding
- Market entry and exit events

❌ **Hidden from external systems:**
- Internal formulas and calculations
- **Stock health metrics** (metabolicHealth)
- **Stock valuation scores** (valueScore)
- Market regime classifications
- Transition probabilities
- Predictive indicators
- Company status (active/bankrupt - inferred from presence/absence only)

---

## Best Practices

### Efficient Polling

**Poll at 1-3 second intervals** to align with the 2-tick broadcast interval:

```python
import time

while True:
    stats = fetch_market_stats()
    # Process data
    analyze_market(stats)
    time.sleep(2)  # 2 seconds = 30 req/min (well under 60 req/min limit)
```

**Why 2 seconds?**
- Backend broadcasts every 2 ticks (1000ms)
- Polling every 2 seconds gives you fresh data on every other broadcast
- Rate: 30 req/min (well under 60 req/min limit for most endpoints)
- Leaves headroom for occasional bursts or multiple endpoint calls

### Handle Market Status

**Always check marketStatus field:**

```python
def get_stock_price(ticker):
    stock = fetch_stock(ticker)

    if stock['marketStatus'] == 'closed':
        print(f"Market closed - {ticker} price is delayed: ${stock['price']}")
    else:
        print(f"Real-time price for {ticker}: ${stock['price']}")

    return stock['price']
```

### Error Handling

**Handle all error cases with exponential backoff:**

```python
import requests
import time

def fetch_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                wait = 2 ** attempt
                print(f"Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                response.raise_for_status()

        except requests.exceptions.Timeout:
            print(f"Timeout on attempt {attempt + 1}")
            time.sleep(2 ** attempt)

    return None
```

### Client-Side Rate Limiting

**Track your requests to stay under limits:**

```python
from collections import deque
import time

class RateLimiter:
    def __init__(self, max_requests=50, window=60):
        """
        Args:
            max_requests: Stay under endpoint limit (e.g., 50 for 60/min limit)
            window: Time window in seconds (60 for per-minute limits)
        """
        self.max_requests = max_requests
        self.window = window
        self.timestamps = deque(maxlen=max_requests)

    def wait_if_needed(self):
        now = time.time()
        recent = [ts for ts in self.timestamps if now - ts < self.window]

        if len(recent) >= self.max_requests:
            wait = self.window - (now - min(recent)) + 0.1
            print(f"Rate limit approaching. Waiting {wait:.1f}s")
            time.sleep(wait)

        self.timestamps.append(now)

# Usage - set limit below endpoint max to leave headroom
limiter = RateLimiter(max_requests=50, window=60)  # Stay under 60/min

while True:
    limiter.wait_if_needed()
    stats = fetch_market_stats()
    process(stats)
    time.sleep(2)  # ~30 req/min
```

### Map All Tickers

**To build a complete ticker map across all sectors:**

```python
def get_all_tickers():
    """Fetch all tickers and organize by sector"""
    tickers_by_sector = {}

    page = 1
    while True:
        response = fetch_stocks(page=page, page_size=100)

        for stock in response['data']:
            sector = stock['sector']
            if sector not in tickers_by_sector:
                tickers_by_sector[sector] = []
            tickers_by_sector[sector].append(stock['ticker'])

        # Check if more pages
        if page >= response['total_pages']:
            break
        page += 1

    return tickers_by_sector

# Example output:
# {
#   'Technology': ['TWH', 'TGOY', ...],
#   'Healthcare': ['HBK', 'HML', ...],
#   'Finance': ['FSV', 'FBN', ...],
#   ...
# }
```

---

## Troubleshooting

### Authentication Failed

**Error:** `{"detail":"Invalid API key"}`

**Solution:**
- Verify API key is correct
- Check `X-API-Key` header is properly set
- Contact administrator for valid key

---

### Rate Limit Exceeded

**Error:** `HTTP 429 Too Many Requests`

**Solutions:**
1. Increase polling interval (e.g., from 1s to 2-3s)
2. Implement client-side rate limiting (see Best Practices)
3. Use less expensive endpoints (e.g., /market/stats instead of /market/snapshot)
4. Cache data locally and poll less frequently

---

### Connection Refused

**Error:** `Connection refused`

**Solutions:**
- Verify backend is running: `curl http://localhost:8000/api/health`
- Check correct URL: `http://localhost:8000`
- Check firewall settings

---

### Understanding Market Status

**Question:** Why does `marketStatus` say "closed" but I still get prices?

**Answer:** When market is closed, prices reflect the last known value from when the market was open. This is by design - you always get a price, but the `marketStatus` field tells you whether it's real-time or delayed.

---

### Stock Not Found

**Error:** `{"detail":"Stock {ticker} not found"}`

**Solutions:**
- Verify ticker symbol is correct
- Stock may have gone bankrupt: `GET /api/v1/stocks?status=bankrupt`
- Refresh your ticker list to get current active stocks

---

## Example Workflows

### Monitor Market Volatility

```python
import time

def monitor_vix():
    """Alert when VIX exceeds threshold"""
    while True:
        stats = fetch_market_stats()
        vix = stats['vix']

        if vix > 30:
            print(f"⚠️  HIGH VOLATILITY: VIX = {vix:.2f}")
        elif vix > 20:
            print(f"📊 Elevated volatility: VIX = {vix:.2f}")

        time.sleep(2)  # 2 seconds = 30 req/min
```

### Track Sector Performance

```python
def track_sector(sector, duration_ticks=120):
    """Monitor sector price changes over time"""

    # Get initial prices (only when market is open)
    stocks = fetch_stocks(sector=sector)
    initial_prices = {}

    for stock in stocks['data']:
        if stock['marketStatus'] == 'open':
            initial_prices[stock['ticker']] = stock['price']

    # Wait specified ticks
    time.sleep((duration_ticks * 0.5))

    # Get new prices
    stocks = fetch_stocks(sector=sector)
    changes = []

    for stock in stocks['data']:
        ticker = stock['ticker']
        if ticker in initial_prices and stock['marketStatus'] == 'open':
            change = (stock['price'] - initial_prices[ticker]) / initial_prices[ticker]
            changes.append(change)

    avg_change = sum(changes) / len(changes) if changes else 0
    print(f"{sector} average change: {avg_change*100:.2f}%")
    return avg_change
```

### Build Ticker Map

```python
def build_ticker_map():
    """Create complete ticker reference"""

    all_tickers = []
    page = 1

    while True:
        response = fetch_stocks(page=page, page_size=100)

        for stock in response['data']:
            all_tickers.append({
                'ticker': stock['ticker'],
                'name': stock['name'],
                'sector': stock['sector'],
                'subIndustry': stock['subIndustry']
            })

        if page >= response['total_pages']:
            break
        page += 1

    # Save to file for quick reference
    with open('tickers.json', 'w') as f:
        json.dump(all_tickers, f, indent=2)

    print(f"Saved {len(all_tickers)} tickers to tickers.json")
    return all_tickers
```

---

## Support

For questions or issues:

1. Review this documentation
2. Check interactive API docs: http://localhost:8000/docs
3. Contact your system administrator

---

**API Version:** 1.0.0
**Last Updated:** 2025-12-27
