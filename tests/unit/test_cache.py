import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from core.config import settings
from core.cache import redis_client, is_redis_available

def test_cache_health_endpoint(client: TestClient) -> None:
    """Test that health endpoint returns Redis status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "redis" in response.json()

@pytest.mark.skipif(not is_redis_available(), reason="Redis is not available")
def test_cache_posts_list(client: TestClient, normal_user_token_headers: dict) -> None:
    """Test that posts list is cached."""
    # Clear the cache first
    redis_client.flushall()
    
    # First request should be a cache miss
    response = client.get(
        f"{settings.API_V1_STR}/posts/", 
        headers=normal_user_token_headers
    )
    assert response.status_code == 200
    
    # Check Redis for the cache key
    cache_keys = redis_client.keys("posts:list:*")
    assert len(cache_keys) > 0
    
    # Make the same request again, should be a cache hit
    with patch("db.repositories.post.PostRepository.get_multi") as mock_get_multi:
        mock_get_multi.return_value = ([], 0)  # Should not be called if cache hit
        response = client.get(
            f"{settings.API_V1_STR}/posts/", 
            headers=normal_user_token_headers
        )
        assert response.status_code == 200
        # Repository should not be called if cache hit
        mock_get_multi.assert_not_called()

@pytest.mark.skipif(not is_redis_available(), reason="Redis is not available")
def test_invalidate_cache_on_post_update(
    client: TestClient, 
    normal_user_token_headers: dict, 
    db: MagicMock
) -> None:
    """Test that cache is invalidated when a post is updated."""
    # Create a post first
    post_data = {
        "title": "Cache Test Post",
        "content": "This is a test post for cache invalidation",
        "summary": "Test summary",
        "published": True
    }
    response = client.post(
        f"{settings.API_V1_STR}/posts/",
        headers=normal_user_token_headers,
        json=post_data
    )
    assert response.status_code == 201
    post_id = response.json()["id"]
    
    # Get the post to cache it
    response = client.get(
        f"{settings.API_V1_STR}/posts/{post_id}",
        headers=normal_user_token_headers
    )
    assert response.status_code == 200
    
    # Check Redis for the cache key
    cache_keys = redis_client.keys(f"posts:detail:{post_id}")
    assert len(cache_keys) > 0
    
    # Update the post
    update_data = {
        "title": "Updated Cache Test Post"
    }
    response = client.put(
        f"{settings.API_V1_STR}/posts/{post_id}",
        headers=normal_user_token_headers,
        json=update_data
    )
    assert response.status_code == 200
    
    # Cache should be invalidated
    cache_keys = redis_client.keys(f"posts:detail:{post_id}")
    assert len(cache_keys) == 0
    
    # Get the post again, should be a cache miss
    with patch("db.repositories.post.PostRepository.get") as mock_get:
        response = client.get(
            f"{settings.API_V1_STR}/posts/{post_id}",
            headers=normal_user_token_headers
        )
        assert response.status_code == 200
        # Repository should be called if cache miss
        mock_get.assert_called_once()

@pytest.mark.skipif(not is_redis_available(), reason="Redis is not available")
def test_cache_control_endpoints(client: TestClient, superuser_token_headers: dict) -> None:
    """Test that cache control endpoints work."""
    # Get cache stats
    response = client.get(
        f"{settings.API_V1_STR}/cache/stats",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    assert "total_keys" in response.json()
    
    # Clear cache
    response = client.delete(
        f"{settings.API_V1_STR}/cache/clear?pattern=posts:*",
        headers=superuser_token_headers
    )
    assert response.status_code == 204
    
    # Check that posts cache is cleared
    cache_keys = redis_client.keys("posts:*")
    assert len(cache_keys) == 0