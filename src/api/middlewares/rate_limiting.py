from typing import Callable, Optional, List
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from core.rate_limiter import RateLimiter

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, 
        app,
        rate_limiter: RateLimiter,
        exclude_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Get user ID if authenticated
        user_id = None
        if hasattr(request.state, "user"):
            user_id = request.state.user.id

        # Check rate limit
        is_limited, headers = self.rate_limiter.is_rate_limited(request, user_id)

        if is_limited:
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests",
                    "type": "rate_limit_exceeded"
                },
                headers=headers
            )

        # Add rate limit headers to response
        response = await call_next(request)
        for key, value in headers.items():
            response.headers[key] = value

        return response