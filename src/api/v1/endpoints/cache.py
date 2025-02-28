from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import get_current_active_superuser
from core.cache import redis_client, is_redis_available
from models.user import User

router = APIRouter()

@router.get("/stats", response_model=Dict[str, Any])
async def get_cache_stats(
    current_user: User = Depends(get_current_active_superuser),
) -> Dict[str, Any]:
    """
    Get cache statistics.
    Only accessible to superusers.
    """
    if not is_redis_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache service is not available"
        )
    
    # Get cache info
    info = redis_client.info()
    
    # Get cache keys
    keys = redis_client.keys("*")
    key_count = len(keys)
    
    # Group keys by pattern
    key_patterns = {}
    for key in keys:
        # Extract pattern from key
        parts = key.split(":")
        if len(parts) > 1:
            pattern = parts[0]
            key_patterns[pattern] = key_patterns.get(pattern, 0) + 1
    
    return {
        "total_keys": key_count,
        "patterns": key_patterns,
        "used_memory": info.get("used_memory_human", "N/A"),
        "uptime": info.get("uptime_in_seconds", 0),
        "connected_clients": info.get("connected_clients", 0),
    }

@router.delete("/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cache(
    pattern: str = "*",
    current_user: User = Depends(get_current_active_superuser),
) -> None:
    """
    Clear cache entries matching a pattern.
    Only accessible to superusers.
    
    Examples:
    - Clear all cache: pattern="*"
    - Clear post cache: pattern="posts:*"
    - Clear specific post: pattern="posts:detail:123"
    """
    if not is_redis_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache service is not available"
        )
    
    # Get keys matching pattern
    keys = redis_client.keys(pattern)
    if not keys:
        return
    
    # Delete keys
    redis_client.delete(*keys)