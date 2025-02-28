import json
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, Union

from fastapi import Request, Response
from redis import Redis
from pydantic import BaseModel

from core.config import settings

logger = logging.getLogger(__name__)

redis_client = Redis.from_url(
    settings.REDIS_URL,
    socket_connect_timeout=1,
    socket_timeout=1,
    retry_on_timeout=True
)

def is_redis_available() -> bool:
    """Check if Redis is available."""
    try:
        return redis_client.ping()
    except Exception as e:
        logger.warning(f"Redis is not available: {str(e)}")
        return False

def serialize_response(response_data: Any) -> str:
    """Serialize response data to JSON string."""
    return json.dumps(response_data)

def deserialize_response(response_data: str) -> Any:
    """Deserialize JSON string to response data."""
    return json.loads(response_data)

class ResponseCache:
    """Cache for API responses using Redis."""

    @staticmethod
    def generate_cache_key(request: Request, prefix: str = "api_cache") -> str:
        """Generate a cache key from the request."""
        # Use path and query parameters to create a unique key
        path = request.url.path
        query_string = str(request.query_params)
        
        # Include user ID if authenticated to ensure proper isolation
        user_id = "anon"
        if hasattr(request.state, "user") and request.state.user:
            user_id = str(request.state.user.id)
            
        return f"{prefix}:{user_id}:{path}:{query_string}"

    @classmethod
    def cache_response(
        cls,
        *,
        expire: int = 60,  # Cache expiration in seconds
        prefix: str = "api_cache",
        exclude_from_cache: Optional[list[str]] = None
    ) -> Callable:
        """
        Decorator to cache API responses in Redis.
        
        Args:
            expire: Time in seconds for cache to expire
            prefix: Prefix for the cache key
            exclude_from_cache: List of path patterns to exclude from caching
        """
        exclude_from_cache = exclude_from_cache or []
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Response:
                # Skip caching for excluded paths
                path = request.url.path
                if any(path.startswith(pattern) for pattern in exclude_from_cache):
                    return await func(request, *args, **kwargs)
                
                # Skip caching if Redis is not available
                if not is_redis_available():
                    return await func(request, *args, **kwargs)
                
                # Generate cache key
                cache_key = cls.generate_cache_key(request, prefix)
                
                # Try to get cached response
                cached_response = redis_client.get(cache_key)
                if cached_response:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return deserialize_response(cached_response)
                
                # Get fresh response
                response = await func(request, *args, **kwargs)
                
                # Cache the response
                try:
                    serialized_response = serialize_response(response)
                    redis_client.setex(
                        cache_key,
                        expire,
                        serialized_response
                    )
                    logger.debug(f"Cached response for key: {cache_key}")
                except Exception as e:
                    logger.error(f"Failed to cache response: {str(e)}")
                
                return response
                
            return wrapper
        return decorator

    @classmethod
    def invalidate_cache(cls, pattern: str = "*") -> None:
        """
        Invalidate cache entries matching a pattern.
        
        Args:
            pattern: Redis key pattern to match, e.g., "api_cache:user:123:*"
        """
        if not is_redis_available():
            return
            
        try:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries matching pattern: {pattern}")
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {str(e)}")