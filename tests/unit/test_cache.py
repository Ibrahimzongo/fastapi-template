import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from core.config import settings
from core.cache import redis_client, is_redis_available
from unittest.mock import patch, MagicMock
import time
from fastapi.exceptions import ResponseValidationError

@pytest.mark.skipif(not is_redis_available(), reason="Redis is not available")
def test_cache_posts_list(client: TestClient, normal_user_token_headers: dict) -> None:
    """Test that posts list is cached."""
    # Clear the cache first
    redis_client.flushall()
    
    # First request should be a cache miss
    with patch("db.repositories.post.PostRepository.get_multi") as mock_get_multi:
        # Mock the repository response with properly structured data
        mock_post = {
            "id": 1,
            "title": "Test Post",
            "content": "Test Content",
            "author_id": 1,
            "created_at": "2025-03-02T09:33:21.786212",
            "updated_at": "2025-03-02T09:33:21.786212",
            "summary": "Test Summary",
            "published": True,
            "author": {
                "id": 1,
                "email": "test@example.com",
                "is_active": True,
                "is_superuser": False,
                "full_name": "Test User"
            }
        }
        mock_get_multi.return_value = ([mock_post], 1)
        
        response = client.get(
            f"{settings.API_V1_STR}/posts/", 
            headers=normal_user_token_headers
        )
        assert response.status_code == 200
        mock_get_multi.assert_called_once()

        # Second request should be a cache hit
        mock_get_multi.reset_mock()
        response = client.get(
            f"{settings.API_V1_STR}/posts/",
            headers=normal_user_token_headers
        )
        assert response.status_code == 200
        mock_get_multi.assert_not_called()  # Should not call repository

    # New Test 1: Clear a specific post detail cache by its pattern.
    @pytest.mark.skipif(not is_redis_available(), reason="Redis is not available")
    def test_clear_specific_post_cache(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict) -> None:
        # Create a post and cache its detail
        post_data = {
            "title": "Cache Clear Specific Test Post",
            "content": "Content for specific cache clear test",
            "summary": "Summary",
            "published": True
        }
        response = client.post(
            f"{settings.API_V1_STR}/posts/",
            headers=normal_user_token_headers,
            json=post_data
        )
        assert response.status_code == 201
        post_id = response.json()["id"]

        # Cache the post detail
        response = client.get(
            f"{settings.API_V1_STR}/posts/{post_id}",
            headers=normal_user_token_headers
        )
        assert response.status_code == 200

        # Verify the detailed cache key exists
        keys = redis_client.keys(f"posts:detail:{post_id}")
        assert len(keys) > 0

        # Clear only the detailed cache for this post via the clear endpoint
        response = client.delete(
            f"{settings.API_V1_STR}/cache/clear?pattern=posts:detail:{post_id}",
            headers=superuser_token_headers
        )
        assert response.status_code == 204

        # Verify the cache key has been cleared
        keys = redis_client.keys(f"posts:detail:{post_id}")
        assert len(keys) == 0

    # New Test 2: Validate the structure of the posts list response.
    @pytest.mark.skipif(not is_redis_available(), reason="Redis is not available")
    def test_posts_list_response_structure(client: TestClient, normal_user_token_headers: dict) -> None:
        # Flush cache to avoid interference
        redis_client.flushall()
        response = client.get(
            f"{settings.API_V1_STR}/posts/",
            headers=normal_user_token_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Expect a dictionary with at least "data" and "total" keys
        assert "data" in data
        assert "total" in data
        if data["data"]:
            post = data["data"][0]
            # Each post must contain required fields
            for key in ("id", "title", "content", "author_id", "created_at", "updated_at", "author"):
                assert key in post

    # New Test 3: Ensure updating a post clears its detailed cache but preserves the posts list cache.
    @pytest.mark.skipif(not is_redis_available(), reason="Redis is not available")
    def test_update_post_preserves_list_cache(client: TestClient, normal_user_token_headers: dict) -> None:
        # Flush cache and get posts list to cache it
        redis_client.flushall()
        response = client.get(
            f"{settings.API_V1_STR}/posts/",
            headers=normal_user_token_headers
        )
        assert response.status_code == 200
        list_keys_before = redis_client.keys("posts:list:*")
        assert len(list_keys_before) > 0

        # Create a post and cache its detail
        post_data = {
            "title": "Post for Update Cache Test",
            "content": "Initial content",
            "summary": "Update test",
            "published": True
        }
        response = client.post(
            f"{settings.API_V1_STR}/posts/",
            headers=normal_user_token_headers,
            json=post_data
        )
        assert response.status_code == 201
        post_id = response.json()["id"]

        response = client.get(
            f"{settings.API_V1_STR}/posts/{post_id}",
            headers=normal_user_token_headers
        )
        assert response.status_code == 200

        # Update the post; this should clear its detailed cache only
        update_data = {"title": "Updated Title"}
        response = client.put(
            f"{settings.API_V1_STR}/posts/{post_id}",
            headers=normal_user_token_headers,
            json=update_data
        )
        assert response.status_code == 200

        # Check that the detail cache for the updated post is cleared
        detail_keys = redis_client.keys(f"posts:detail:{post_id}")
        assert len(detail_keys) == 0

        # The posts list cache should still be intact
        list_keys_after = redis_client.keys("posts:list:*")
        assert len(list_keys_after) > 0

    # New Test 4: Verify that requesting a non-existent post returns 404.
    @pytest.mark.skipif(not is_redis_available(), reason="Redis is not available")
    def test_get_nonexistent_post(client: TestClient, normal_user_token_headers: dict) -> None:
        response = client.get(
            f"{settings.API_V1_STR}/posts/999999999",
            headers=normal_user_token_headers
        )
        assert response.status_code == 404

    # New Test 5: Simulate repository returning an invalid (empty) post structure to trigger response validation error.
    @pytest.mark.skipif(not is_redis_available(), reason="Redis is not available")
    def test_invalid_post_response_triggers_validation_error(client: TestClient, normal_user_token_headers: dict) -> None:
        with patch("db.repositories.post.PostRepository.get") as mock_get:
            # Simulate an empty dictionary for a post, missing required fields.
            mock_get.return_value = {}
            response = client.get(
                f"{settings.API_V1_STR}/posts/9999",  # ID chosen to trigger the patch
                headers=normal_user_token_headers
            )
            # FastAPI error handler should return a 500 error for response validation issues.
            assert response.status_code == 500
            assert "Field required" in response.text
            """Simulate rapid repeated calls to trigger rate limiting."""
            # Assume the rate limit is low (for test purposes, e.g. 5 requests)
            responses = []
            for _ in range(7):
                responses.append(
                    client.get(f"{settings.API_V1_STR}/posts/", headers=normal_user_token_headers)
                )
            # At least one request should be rate-limited (HTTP 429)
            assert any(r.status_code == 429 for r in responses), "Expected one response to be 429 due to rate limiting"

        @pytest.mark.skipif(not is_redis_available(), reason="Redis is not available")
        def test_clear_nonexistent_cache(client: TestClient, superuser_token_headers: dict) -> None:
            """Test that clearing a non-existent cache pattern still returns 204."""
            # Flush all existing cache to simulate no keys matching the pattern
            redis_client.flushall()
            response = client.delete(
                f"{settings.API_V1_STR}/cache/clear?pattern=nonexistent:*",
                headers=superuser_token_headers
            )
            assert response.status_code == 204

        @pytest.mark.skipif(not is_redis_available(), reason="Redis is not available")
        def test_cache_stats_no_entries(client: TestClient, superuser_token_headers: dict) -> None:
            """Test that cache stats endpoint reports zero keys when cache is empty."""
            redis_client.flushall()
            response = client.get(
                f"{settings.API_V1_STR}/cache/stats",
                headers=superuser_token_headers
            )
            assert response.status_code == 200
            stats = response.json()
            assert "total_keys" in stats
            assert stats["total_keys"] == 0

        @pytest.mark.skipif(not is_redis_available(), reason="Redis is not available")
        def test_response_validation_error(client: TestClient, normal_user_token_headers: dict) -> None:
            """
            Test that an invalid post response (missing required fields) causes a ResponseValidationError.
            This simulates a scenario where the repository returns an empty dict.
            """
            with patch("db.repositories.post.PostRepository.get") as mock_get:
                # Simulate an invalid response missing required post fields.
                mock_get.return_value = {}
                response = client.get(
                    f"{settings.API_V1_STR}/posts/9999",  # ID that triggers the patched call
                    headers=normal_user_token_headers
                )
                # FastAPI's error handler catches ResponseValidationError and returns a 500 error
                assert response.status_code == 500
                # Optionally check error message in response for required fields missing
                assert "Field required" in response.text
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
    
    @pytest.mark.skipif(not is_redis_available(), reason="Redis is not available")
    def test_get_post_with_invalid_mock_response(client: TestClient, normal_user_token_headers: dict) -> None:
        """Test handling of invalid repository response structure."""
        with patch("db.repositories.post.PostRepository.get") as mock_get:
            # Mock a Post model instance instead of dict
            mock_post = MagicMock()
            mock_post.id = 1
            mock_post.title = "Test Post"
            mock_post.content = "Test Content"
            mock_post.author_id = 1
            mock_post.created_at = "2025-03-02T09:33:21.786212"
            mock_post.updated_at = "2025-03-02T09:33:21.786212"
            mock_post.summary = "Test Summary"
            mock_post.published = True
            mock_post.author = MagicMock()
            mock_post.author.id = 1
            mock_post.author.email = "test@example.com"
            mock_post.author.is_active = True
            mock_post.author.is_superuser = False
            mock_post.author.full_name = "Test User"
            
            mock_get.return_value = mock_post
            
            response = client.get(
                f"{settings.API_V1_STR}/posts/1",
                headers=normal_user_token_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test Post"
            assert data["author"]["email"] == "test@example.com"

    @pytest.mark.skipif(not is_redis_available(), reason="Redis is not available")
    def test_cache_expiration(client: TestClient, normal_user_token_headers: dict) -> None:
        """Test that cached items expire after the configured time."""
        # Create and cache a post
        post_data = {
            "title": "Cache Expiration Test",
            "content": "Testing cache expiration",
            "published": True
        }
        response = client.post(
            f"{settings.API_V1_STR}/posts/",
            headers=normal_user_token_headers,
            json=post_data
        )
        post_id = response.json()["id"]
        
        # Access the post to cache it
        response = client.get(
            f"{settings.API_V1_STR}/posts/{post_id}",
            headers=normal_user_token_headers
        )
        assert response.status_code == 200
        
        # Verify it's cached
        cache_key = f"posts:detail:{post_id}"
        assert redis_client.exists(cache_key)
        
        # Set TTL to 1 second
        redis_client.expire(cache_key, 1)
        
        # Wait for expiration
        time.sleep(2)
        
        # Verify cache is expired
        assert not redis_client.exists(cache_key)

    @pytest.mark.skipif(not is_redis_available(), reason="Redis is not available")
    def test_cache_with_query_params(client: TestClient, normal_user_token_headers: dict) -> None:
        """Test that different query parameters result in different cache keys."""
        # Make requests with different query params
        response1 = client.get(
            f"{settings.API_V1_STR}/posts/?limit=10",
            headers=normal_user_token_headers
        )
        assert response.status_code == 200
        
        response2 = client.get(
            f"{settings.API_V1_STR}/posts/?limit=20",
            headers=normal_user_token_headers
        )
        assert response.status_code == 200
        
        # Check that we have different cache keys
        cache_keys = redis_client.keys("posts:list:*")
        assert len(cache_keys) == 2

    @pytest.mark.skipif(not is_redis_available(), reason="Redis is not available")
    def test_cache_invalidation_on_post_delete(client: TestClient, normal_user_token_headers: dict) -> None:
        """Test that deleting a post invalidates related cache entries."""
        # Create and cache a post
        post_data = {
            "title": "Delete Cache Test",
            "content": "Testing cache invalidation on delete",
            "published": True
        }
        response = client.post(
            f"{settings.API_V1_STR}/posts/",
            headers=normal_user_token_headers,
            json=post_data
        )
        post_id = response.json()["id"]
        
        # Access the post to cache it
        response = client.get(
            f"{settings.API_V1_STR}/posts/{post_id}",
            headers=normal_user_token_headers
        )
        assert response.status_code == 200
        
        # Verify cache exists
        cache_key = f"posts:detail:{post_id}"
        assert redis_client.exists(cache_key)
        
        # Delete the post
        response = client.delete(
            f"{settings.API_V1_STR}/posts/{post_id}",
            headers=normal_user_token_headers
        )
        assert response.status_code == 204
        
        # Verify cache is invalidated
        assert not redis_client.exists(cache_key)
        
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