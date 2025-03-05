import logging
from functools import wraps
from typing import Any, Callable, Optional, List

from fastapi import Request, Response

# Importer depuis le module de base
from core.cache_base import redis_client, is_redis_available, serialize_response, deserialize_response

logger = logging.getLogger(__name__)

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
        exclude_from_cache: Optional[List[str]] = None
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
                
                try:
                    # Generate cache key
                    cache_key = cls.generate_cache_key(request, prefix)
                    
                    # Try to get cached response
                    cached_response = redis_client.get(cache_key)
                    if cached_response:
                        logger.debug(f"Cache hit for key: {cache_key}")
                        deserialized = deserialize_response(cached_response)
                        if deserialized:
                            return deserialized
                    
                    # Get fresh response
                    response = await func(request, *args, **kwargs)
                    
                    # Cache the response
                    serialized_response = serialize_response(response)
                    if serialized_response:
                        try:
                            redis_client.setex(
                                cache_key,
                                expire,
                                serialized_response
                            )
                            logger.debug(f"Cached response for key: {cache_key}")
                        except Exception as e:
                            logger.error(f"Failed to cache response: {str(e)}")
                    
                    return response
                except Exception as e:
                    # En cas d'erreur, log et retourne la réponse non mise en cache
                    logger.error(f"Cache error: {str(e)}")
                    return await func(request, *args, **kwargs)
                
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