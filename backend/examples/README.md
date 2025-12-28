# Example Agents

This directory contains example autonomous agents that demonstrate best practices for interacting with the BioMarket CAS Market Simulation API.

## Available Examples

### `example_agent.py` - Market Observer

A comprehensive example agent that demonstrates:
- API authentication
- Efficient polling (every 1-2 seconds)
- Rate limit compliance
- Error handling with exponential backoff
- Null price handling (CLOSED phase)
- Stock sector analysis
- Statistics tracking

## Running the Example Agent

### Prerequisites

```bash
# Install required dependency
pip install requests
```

### Run the Agent

```bash
# Make sure the backend is running first
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# In a new terminal, run the example agent
cd backend/examples
python example_agent.py
```

### Expected Output

```
2025-12-27 11:30:00 - __main__ - INFO - ============================================================
2025-12-27 11:30:00 - __main__ - INFO - Market Observer Agent Starting
2025-12-27 11:30:00 - __main__ - INFO - ============================================================
2025-12-27 11:30:00 - __main__ - INFO - API Key: test-key-12345
2025-12-27 11:30:00 - __main__ - INFO - Base URL: http://localhost:8000
2025-12-27 11:30:00 - __main__ - INFO - Duration: Infinite
2025-12-27 11:30:00 - __main__ - INFO - ============================================================
2025-12-27 11:30:00 - __main__ - INFO - Press Ctrl+C to stop
2025-12-27 11:30:00 - __main__ - INFO - ============================================================
2025-12-27 11:30:00 - __main__ - INFO - Starting market observation...
2025-12-27 11:30:00 - __main__ - INFO - Engine at tick 150, phase: TRADING
2025-12-27 11:30:15 - __main__ - INFO - 📊 Market Stats | Total Cap: $48,620,359,170,036 | Active Stocks: 85 | VIX: 15.68 | Interest Rate: 0.76
2025-12-27 11:30:45 - __main__ - INFO - 💻 Tech Sector | Count: 10 | Highest Value Score: TWH (Score: 0.168, Price: $60.39)
```

## Customization

### Change API Key

Edit the `API_KEY` variable in `example_agent.py`:

```python
API_KEY = "your-agent-key-here"
```

### Change Polling Interval

Modify the `time.sleep()` call in the `observe_market()` method:

```python
# Poll every 2 seconds instead of 1.5
time.sleep(2)
```

### Add Custom Analysis

Extend the `MarketObserver` class with your own analysis methods:

```python
def _my_custom_analysis(self):
    """Custom market analysis logic"""
    # Fetch data
    stats = self.get_market_stats()
    engine_info = self.get_engine_info()

    # Analyze
    if stats['vix'] > 30:
        logger.warning("High volatility detected!")

    # Check market phase
    if engine_info['phase'] == 'CLOSED':
        logger.info("Market is CLOSED - waiting for next TRADING phase")

    # Add your logic here
```

Then call it from the observation loop:

```python
if iteration % 20 == 0:
    self._my_custom_analysis()
```

## Best Practices Demonstrated

1. **Rate Limit Compliance**
   - Client-side rate limiting using deque
   - Automatic backoff when approaching limits

2. **Error Handling**
   - Exponential backoff on failures
   - Graceful handling of 401, 404, 429 errors
   - Network timeout handling

3. **Efficient Polling**
   - Aligned with 1-second broadcast interval
   - Avoids unnecessary requests

4. **Logging**
   - Comprehensive logging for debugging
   - Statistics tracking

5. **State Management**
   - Tracks regime changes
   - Monitors request history
   - Calculates aggregate statistics

## Learn More

- **Full API Documentation**: See `../AGENT_API.md`
- **Interactive API Docs**: Visit http://localhost:8000/docs
- **Backend Setup**: See `../README.md`

## Building Your Own Agent

Use `example_agent.py` as a template:

1. Copy the file and rename it
2. Modify the `MarketObserver` class
3. Add your custom logic in `observe_market()`
4. Implement your own analysis methods
5. Test with the backend running

## Troubleshooting

**"Invalid API key" error:**
- Check that your key is in `backend/.env`
- Verify you're using the correct key in the script

**"Connection refused" error:**
- Make sure the backend is running (`uvicorn app.main:app --reload`)
- Check that you're connecting to the correct URL

**Rate limit errors:**
- Increase `time.sleep()` interval
- Reduce frequency of expensive operations (history, snapshot)

## Support

For questions or issues, see:
- `AGENT_API.md` - Full API documentation
- http://localhost:8000/docs - Interactive Swagger docs
- Contact your system administrator
