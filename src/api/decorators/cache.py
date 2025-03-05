import functools
import hashlib
import json
import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

from fastapi import Depends, Request
from pydantic import BaseModel

from core.cache_base import is_redis_available, redis_client

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Callable[..., Any])

def cache(
    *,
    expire: int = 60,
    key_prefix: str = "",
    include_query_params: bool = True,
    include_user: bool = True,
    include_headers: List[str] = None,
) -> Callable[[T], T]:
    """
    Decorator to cache function results in Redis.
    
    Args:
        expire: Time in seconds for cache to expire
        key_prefix: Prefix for the cache key
        include_query_params: Whether to include query parameters in the cache key
        include_user: Whether to include user ID in the cache key
        include_headers: List of headers to include in the cache key
    """
    include_headers = include_headers or []
    
    def decorator(func: T) -> T:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Skip caching if Redis is not available
            if not is_redis_available():
                return await func(*args, **kwargs)
            
            try:
                # Extract request from args or kwargs
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if request is None:
                    # Check if request is in kwargs
                    request = kwargs.get("request")
                    if request is None:
                        # If no request is found, can't generate cache key
                        return await func(*args, **kwargs)
                
                # Generate cache key
                key_parts = [key_prefix or func.__name__]
                
                # Add path
                key_parts.append(request.url.path)
                
                # Add query params if requested
                if include_query_params and request.query_params:
                    # Sort query params to ensure consistent cache keys
                    sorted_params = dict(sorted(request.query_params.items()))
                    key_parts.append(json.dumps(sorted_params))
                
                # Add user ID if requested
                if include_user and hasattr(request.state, "user"):
                    user = request.state.user
                    if user and hasattr(user, "id"):
                        key_parts.append(f"user:{user.id}")
                
                # Add selected headers if requested
                if include_headers:
                    for header in include_headers:
                        if header in request.headers:
                            key_parts.append(f"{header}:{request.headers[header]}")
                
                # Create a hash of all parts for the final cache key
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
                
                # Try to get cached response
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    try:
                        return json.loads(cached_result)
                    except Exception as e:
                        logger.warning(f"Failed to parse cached result: {e}")
                
                # Get fresh result
                result = await func(*args, **kwargs)
                
                # Cache the result
                try:
                    # Serialize result
                    serialized_result = json.dumps(result)
                    redis_client.setex(cache_key, expire, serialized_result)
                except Exception as e:
                    logger.warning(f"Failed to cache result: {e}")
                
                return result
            except Exception as e:
                # En cas d'erreur avec le cache, exécuter simplement la fonction
                logger.error(f"Cache decorator error: {str(e)}")
                return await func(*args, **kwargs)
            
        return cast(T, wrapper)
        
    return decorator

def invalidate_cache(pattern: str) -> None:
    """
    Invalidate cache entries matching a pattern.
    
    Args:
        pattern: Redis key pattern to match
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