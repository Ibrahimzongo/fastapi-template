from datetime import datetime, timedelta
import hashlib
from typing import Optional, Tuple

from fastapi import HTTPException, Request, status
from redis import Redis
import json

from core.config import settings

class RateLimiter:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.rate_limit = settings.RATE_LIMIT_PER_MINUTE
        self.window = 60  # 1 minute window

    def _generate_key(self, request: Request, user_id: Optional[int] = None) -> str:
        """Génère une clé unique pour le rate limiting basée sur l'IP et/ou l'ID utilisateur"""
        if user_id:
            key_base = f"{user_id}:{request.client.host}"
        else:
            key_base = request.client.host
            
        # Ajouter le chemin de l'endpoint pour des limites différentes par route
        path_hash = hashlib.md5(request.url.path.encode()).hexdigest()
        return f"rate_limit:{path_hash}:{key_base}"

    def is_rate_limited(self, request: Request, user_id: Optional[int] = None) -> Tuple[bool, dict]:
        """
        Vérifie si une requête dépasse la limite de taux.
        Retourne un tuple (is_limited, headers).
        """
        key = self._generate_key(request, user_id)
        pipe = self.redis.pipeline()

        now = datetime.now()
        window_start = now - timedelta(seconds=self.window)

        # Nettoyer les anciennes requêtes
        pipe.zremrangebyscore(key, 0, window_start.timestamp())
        
        # Ajouter la requête actuelle
        pipe.zadd(key, {json.dumps({'timestamp': now.timestamp()}): now.timestamp()})
        
        # Compter les requêtes dans la fenêtre
        pipe.zcard(key)
        
        # Définir l'expiration de la clé
        pipe.expire(key, self.window)
        
        _, _, request_count, _ = pipe.execute()

        # Préparer les headers pour informer le client
        headers = {
            'X-RateLimit-Limit': str(self.rate_limit),
            'X-RateLimit-Remaining': str(max(0, self.rate_limit - request_count)),
            'X-RateLimit-Reset': str(int(now.timestamp() + self.window))
        }

        if request_count > self.rate_limit:
            return True, headers

        return False, headers

def create_rate_limiter(redis_url: str) -> RateLimiter:
    """Crée une instance de RateLimiter avec une connexion Redis"""
    redis_client = Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_timeout=1,
        socket_connect_timeout=1,
        retry_on_timeout=True
    )
    return RateLimiter(redis_client)