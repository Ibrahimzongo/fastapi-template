import json
import logging
from typing import Any
from redis import Redis

from core.config import settings

logger = logging.getLogger(__name__)

def get_redis_client():
    """Fonction pour créer le client Redis avec une gestion d'erreur appropriée"""
    try:
        return Redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=1,
            socket_timeout=1,
            retry_on_timeout=True
        )
    except Exception as e:
        logger.warning(f"Impossible de se connecter à Redis: {str(e)}")
        return None

redis_client = get_redis_client()

def is_redis_available() -> bool:
    """Check if Redis is available."""
    if not redis_client:
        return False
        
    try:
        return redis_client.ping()
    except Exception as e:
        logger.warning(f"Redis is not available: {str(e)}")
        return False

def serialize_response(response_data: Any) -> str:
    """Serialize response data to JSON string."""
    try:
        return json.dumps(response_data)
    except Exception as e:
        logger.error(f"Failed to serialize response: {str(e)}")
        return None

def deserialize_response(response_data: str) -> Any:
    """Deserialize JSON string to response data."""
    try:
        return json.loads(response_data)
    except Exception as e:
        logger.error(f"Failed to deserialize response: {str(e)}")
        return None