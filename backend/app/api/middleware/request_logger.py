"""
Request logging middleware for tracking agent API usage.
"""
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

# Configure logger for agent requests
logger = logging.getLogger("agent_requests")
logger.setLevel(logging.INFO)

# Create console handler with formatted output
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all agent API requests.

    Logs:
    - API key/agent identifier
    - Endpoint path
    - Query parameters
    - Response status
    - Response time
    - Rate limit headers (if present)
    """

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip health check and root endpoints
        if request.url.path in ["/", "/api/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Extract agent identifier
        api_key = request.headers.get("X-API-Key", "anonymous")
        agent_id = api_key[:8] + "..." if len(api_key) > 8 else api_key

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Start timing
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate response time
        duration_ms = (time.time() - start_time) * 1000

        # Extract query parameters
        query_params = dict(request.query_params) if request.query_params else {}
        query_str = f"?{request.query_params}" if request.query_params else ""

        # Get rate limit headers if present
        rate_limit_info = ""
        if hasattr(response, "headers"):
            remaining = response.headers.get("X-RateLimit-Remaining")
            limit = response.headers.get("X-RateLimit-Limit")
            if remaining and limit:
                rate_limit_info = f" [Rate: {remaining}/{limit}]"

        # Log the request
        log_level = logging.WARNING if response.status_code >= 400 else logging.INFO

        logger.log(
            log_level,
            f"Agent={agent_id} IP={client_ip} "
            f"Method={request.method} Path={request.url.path}{query_str} "
            f"Status={response.status_code} Duration={duration_ms:.2f}ms{rate_limit_info}"
        )

        # Log query parameters separately if they exist (for debugging)
        if query_params and log_level == logging.INFO:
            logger.debug(f"  Query params: {query_params}")

        return response
