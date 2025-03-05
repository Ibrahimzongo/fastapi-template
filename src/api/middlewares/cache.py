from typing import Callable, List, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

# Importer de core.cache et core.cache_base
from core.cache import ResponseCache
from core.cache_base import redis_client, is_redis_available

logger = logging.getLogger(__name__)

class CacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to cache API responses.
    
    This middleware will cache GET requests if they match the configured
    cache patterns. POST, PUT, DELETE, etc. will invalidate the cache
    for affected resources.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        cache_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        cache_expire: int = 60,
    ):
        super().__init__(app)
        self.cache_patterns = cache_patterns or ["/api/v1/posts", "/api/v1/tags"]
        self.exclude_patterns = exclude_patterns or [
            "/docs", 
            "/openapi.json", 
            "/metrics", 
            "/health",
            "/api/v1/auth"
        ]
        self.cache_expire = cache_expire
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip caching if Redis is not available
        if not is_redis_available():
            return await call_next(request)
        
        # Skip caching for excluded patterns
        path = request.url.path
        if any(path.startswith(pattern) for pattern in self.exclude_patterns):
            return await call_next(request)
        
        try:
            # Only cache GET requests
            if request.method == "GET":
                # Only cache if path matches a cache pattern
                if any(path.startswith(pattern) for pattern in self.cache_patterns):
                    # Generate cache key
                    cache_key = ResponseCache.generate_cache_key(request)
                    
                    # Check if response is cached
                    cached_response = redis_client.get(cache_key)
                    if cached_response:
                        # Return cached response
                        return Response(
                            content=cached_response,
                            media_type="application/json",
                            headers={"X-Cache": "HIT"},
                        )
                    
                    # Get fresh response
                    response = await call_next(request)
                    
                    # Cache the response if it's successful
                    if 200 <= response.status_code < 300:
                        try:
                            # Read and cache response body
                            body = b""
                            async for chunk in response.body_iterator:
                                body += chunk
                            
                            # Cache response
                            redis_client.setex(
                                cache_key,
                                self.cache_expire,
                                body
                            )
                            
                            # Return response with updated headers
                            return Response(
                                content=body,
                                status_code=response.status_code,
                                headers={**dict(response.headers), "X-Cache": "MISS"},
                                media_type=response.media_type
                            )
                        except Exception as e:
                            logger.error(f"Failed to cache response: {str(e)}")
                            return response
                    
                    return response
            
            # For non-GET methods, invalidate cache
            elif request.method in ["POST", "PUT", "DELETE", "PATCH"]:
                try:
                    # Extract resource type from path
                    parts = path.strip("/").split("/")
                    if len(parts) >= 2:
                        resource = parts[-2] if parts[-1].isdigit() else parts[-1]
                        pattern = f"api_cache:*:{resource}:*"
                        
                        # Invalidate cache for this resource type
                        keys = redis_client.keys(pattern)
                        if keys:
                            redis_client.delete(*keys)
                except Exception as e:
                    logger.error(f"Failed to invalidate cache: {str(e)}")
            
            # Call next middleware
            return await call_next(request)
        except Exception as e:
            # En cas d'erreur, log et passe à la suite du middleware
            logger.error(f"Cache middleware error: {str(e)}")
            return await call_next(request)