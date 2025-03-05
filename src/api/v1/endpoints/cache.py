from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
import logging

from api.deps import get_current_active_superuser
from core.cache_base import redis_client, is_redis_available
from models.user import User
from ...deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Obtenir des statistiques sur le cache"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if not is_redis_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache service is not available"
        )
        
    try:
        post_keys = redis_client.keys("posts:*")
        stats = {"total_keys": len(post_keys)}
        return stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}"
        )

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
    
    try:
        # Get keys matching pattern
        keys = redis_client.keys(pattern)
        if not keys:
            return
        
        # Delete keys
        redis_client.delete(*keys)
        logger.info(f"Cleared {len(keys)} cache entries matching pattern: {pattern}")
    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )