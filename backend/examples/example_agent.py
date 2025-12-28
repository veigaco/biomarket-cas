#!/usr/bin/env python3
"""
Example Market Observer Agent

This agent demonstrates best practices for interacting with the
BioMarket CAS Market Engine API.

Features:
- API key authentication
- Efficient polling (every 1-2 seconds)
- Error handling with exponential backoff
- Rate limit compliance
- Null price handling (CLOSED phase)
- Stock monitoring and analysis

Usage:
    python example_agent.py

Requirements:
    pip install requests
"""

import requests
import time
import logging
from typing import Dict, List, Optional
from collections import deque


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarketObserver:
    """
    Autonomous agent that observes the market engine and logs insights.

    This agent polls the market API every 1-2 seconds, respects rate limits,
    handles errors gracefully, and properly handles null prices during CLOSED phases.
    """

    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        """
        Initialize the market observer.

        Args:
            api_key: Your API key for authentication
            base_url: Base URL of the market simulation API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}

        # State tracking
        self.request_timestamps = deque(maxlen=20)  # Track last 20 requests

        # Statistics
        self.total_requests = 0
        self.errors = 0

        logger.info(f"Initialized MarketObserver with base_url={base_url}")

    def _make_request(self, endpoint: str, max_retries: int = 3) -> Optional[Dict]:
        """
        Make an API request with exponential backoff on errors.

        Args:
            endpoint: API endpoint (e.g., "/api/v1/market/stats")
            max_retries: Maximum number of retry attempts

        Returns:
            Response JSON data, or None if all retries failed
        """
        url = f"{self.base_url}{endpoint}"

        for attempt in range(max_retries):
            try:
                # Check rate limit before making request
                self._wait_if_rate_limited()

                # Make request with timeout
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=5
                )

                # Track request timestamp
                self.request_timestamps.append(time.time())
                self.total_requests += 1

                # Handle response
                if response.status_code == 200:
                    return response.json()

                elif response.status_code == 401:
                    logger.error("Authentication failed - invalid API key")
                    raise Exception("Invalid API key")

                elif response.status_code == 404:
                    logger.warning(f"Resource not found: {endpoint}")
                    return None

                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue

                else:
                    logger.error(f"HTTP {response.status_code}: {response.text}")
                    response.raise_for_status()

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)
                self.errors += 1

            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e} (attempt {attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)
                self.errors += 1

        logger.error(f"Failed to fetch {endpoint} after {max_retries} attempts")
        return None

    def _wait_if_rate_limited(self):
        """
        Implement client-side rate limiting.

        Ensures we don't exceed 20 requests per minute.
        """
        now = time.time()
        window = 60  # 1 minute
        max_requests = 18  # Stay under limit (20/min)

        # Count requests in last minute
        recent_requests = [ts for ts in self.request_timestamps if now - ts < window]

        if len(recent_requests) >= max_requests:
            # Calculate wait time
            oldest_request = min(recent_requests)
            wait_time = window - (now - oldest_request) + 0.1
            logger.info(f"Rate limit approaching. Waiting {wait_time:.1f}s...")
            time.sleep(wait_time)

    def get_market_stats(self) -> Optional[Dict]:
        """
        Fetch aggregate market statistics.

        Returns:
            Market stats including total cap, VIX, interest rate
        """
        return self._make_request("/api/v1/market/stats")

    def get_stocks(self, sector: Optional[str] = None, page_size: int = 50) -> Optional[Dict]:
        """
        Fetch active stocks with optional sector filtering.

        Args:
            sector: Filter by sector (e.g., "Technology")
            page_size: Number of stocks per page

        Returns:
            Paginated stock data
        """
        endpoint = f"/api/v1/stocks?page_size={page_size}&status=active"
        if sector:
            endpoint += f"&sector={sector}"

        return self._make_request(endpoint)

    def get_stock_details(self, ticker: str) -> Optional[Dict]:
        """
        Fetch detailed information for a specific stock.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Stock details including price, market cap, health, etc.
        """
        return self._make_request(f"/api/v1/stocks/{ticker}")

    def get_engine_info(self) -> Optional[Dict]:
        """
        Fetch engine timing and metadata.

        Returns:
            Engine info including tick count, phase, etc.
        """
        return self._make_request("/api/v1/engine/info")

    def observe_market(self, duration: Optional[int] = None):
        """
        Main observation loop - polls market and logs insights.

        This is the main method that runs continuously to observe
        the market and detect interesting patterns.

        Args:
            duration: How long to run in seconds (None = run forever)
        """
        logger.info("Starting market observation...")
        start_time = time.time()

        # Get initial state
        engine_info = self.get_engine_info()
        if engine_info:
            logger.info(f"Engine at tick {engine_info['tick_count']}, phase: {engine_info['phase']}")

        try:
            iteration = 0
            while True:
                iteration += 1

                # Check duration
                if duration and (time.time() - start_time) > duration:
                    logger.info(f"Reached duration limit ({duration}s). Stopping.")
                    break

                # Fetch current market state
                stats = self.get_market_stats()

                if not stats:
                    logger.error("Failed to fetch market data. Retrying...")
                    time.sleep(5)
                    continue

                # Log market insights every 10 iterations (~10 seconds)
                if iteration % 10 == 0:
                    logger.info(
                        f"📊 Market Stats | "
                        f"Total Cap: ${stats['total_market_cap']:,.0f} | "
                        f"Active Stocks: {stats['active_stocks']} | "
                        f"VIX: {stats['vix']:.2f} | "
                        f"Interest Rate: {stats['interest_rate']:.2f}"
                    )

                # Monitor high-volatility stocks (example analysis)
                if iteration % 30 == 0:  # Every ~30 seconds
                    self._analyze_technology_sector()

                # Print statistics every 50 iterations
                if iteration % 50 == 0:
                    self._print_statistics()

                # Wait before next poll (aligned with 1s broadcast interval)
                time.sleep(1.5)  # 1.5 seconds = ~40 req/min (under 20 req/min limit for stats)

        except KeyboardInterrupt:
            logger.info("Interrupted by user. Shutting down...")
            self._print_statistics()

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise

    def _analyze_technology_sector(self):
        """
        Example analysis: Monitor Technology sector stocks.

        This demonstrates how to fetch and analyze specific stocks.
        """
        tech_stocks = self.get_stocks(sector="Technology", page_size=10)

        if not tech_stocks:
            return

        stocks = tech_stocks.get('data', [])
        if not stocks:
            logger.info("No Technology stocks found")
            return

        # Find stock with highest value score (only consider stocks with prices)
        stocks_with_prices = [s for s in stocks if s.get('price') is not None]

        if not stocks_with_prices:
            logger.info("💻 Tech Sector | Market is CLOSED - prices not available")
            return

        highest_value = max(stocks_with_prices, key=lambda s: s.get('valueScore', 0))

        logger.info(
            f"💻 Tech Sector | "
            f"Count: {len(stocks)} | "
            f"Highest Value Score: {highest_value['ticker']} "
            f"(Score: {highest_value['valueScore']:.3f}, "
            f"Price: ${highest_value['price']:.2f})"
        )

    def _print_statistics(self):
        """Print observer statistics."""
        logger.info(
            f"📈 Agent Stats | "
            f"Requests: {self.total_requests} | "
            f"Errors: {self.errors}"
        )


def main():
    """
    Main entry point for the example agent.

    Modify API_KEY and BASE_URL as needed for your setup.
    """
    # Configuration
    API_KEY = "test-key-12345"  # Replace with your API key
    BASE_URL = "http://localhost:8000"
    DURATION = None  # Run forever (set to number of seconds to limit)

    # Create and run observer
    observer = MarketObserver(api_key=API_KEY, base_url=BASE_URL)

    logger.info("=" * 60)
    logger.info("Market Observer Agent Starting")
    logger.info("=" * 60)
    logger.info(f"API Key: {API_KEY}")
    logger.info(f"Base URL: {BASE_URL}")
    logger.info(f"Duration: {'Infinite' if DURATION is None else f'{DURATION}s'}")
    logger.info("=" * 60)
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)

    try:
        observer.observe_market(duration=DURATION)
    except Exception as e:
        logger.error(f"Agent failed: {e}")
        return 1

    logger.info("Agent shutdown complete")
    return 0


if __name__ == "__main__":
    exit(main())
