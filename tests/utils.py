from unittest.mock import MagicMock

def create_mock_redis():
    """Crée un mock Redis configuré pour les tests"""
    mock_redis = MagicMock()
    
    # Configuration de base
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.setex.return_value = True
    mock_redis.delete.return_value = True
    mock_redis.keys.return_value = []
    
    # Pipeline
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [0, True, 1, True]
    mock_pipeline.incr.return_value = mock_pipeline
    mock_pipeline.expire.return_value = mock_pipeline
    mock_redis.pipeline.return_value = mock_pipeline
    
    return mock_redis

def check_rate_limit_headers(response):
    """Vérifie la présence et le format des headers de rate limiting"""
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    
    assert response.headers["X-RateLimit-Limit"].isdigit()
    assert response.headers["X-RateLimit-Remaining"].isdigit()
    assert response.headers["X-RateLimit-Reset"].isdigit()

def setup_rate_limiter_mock():
    """Configure le mock du rate limiter pour les tests"""
    mock_limiter = MagicMock()
    mock_limiter.is_rate_limited.return_value = (False, {
        'X-RateLimit-Limit': '100',
        'X-RateLimit-Remaining': '99',
        'X-RateLimit-Reset': '0'
    })
    return mock_limiter