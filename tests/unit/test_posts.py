import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.config import settings
from db.repositories.post import PostRepository
from models.post import Post
from schemas.post import PostCreate, PostUpdate

def test_create_post(client: TestClient, normal_user_token_headers: dict) -> None:
    data = {
        "title": "Test Post",
        "content": "This is a test post content",
        "summary": "Test summary",
        "published": True,
        "tags": ["test", "example"]
    }
    response = client.post(
        f"{settings.API_V1_STR}/posts/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == data["title"]
    assert content["content"] == data["content"]
    assert content["published"] == data["published"]
    assert len(content["tags"]) == 2

def test_read_post(
    client: TestClient,
    normal_user_token_headers: dict,
    db: Session
) -> None:
    post_repo = PostRepository(db)
    post = post_repo.create(
        PostCreate(
            title="Test Post",
            content="Content",
            published=True,
            tags=[]  # Add empty tags list
        ),
        author_id=1
    )

    response = client.get(
        f"{settings.API_V1_STR}/posts/{post.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == post.title
    assert content["id"] == post.id
    assert "author" in content  # Verify author is included

def test_read_posts_pagination(
    client: TestClient,
    normal_user_token_headers: dict,
    db: Session
) -> None:
    # Create multiple test posts
    post_repo = PostRepository(db)
    for i in range(15):  # Create 15 posts
        post_repo.create(
            PostCreate(
                title=f"Test Post {i}",
                content=f"Content {i}",
                published=True
            ),
            author_id=1
        )

    # Test first page
    response = client.get(
        f"{settings.API_V1_STR}/posts/?skip=0&limit=10",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["items"]) == 10
    assert content["total"] == 15
    assert content["page"] == 1
    assert content["pages"] == 2

    # Test second page
    response = client.get(
        f"{settings.API_V1_STR}/posts/?skip=10&limit=10",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["items"]) == 5

def test_update_post(
    client: TestClient,
    normal_user_token_headers: dict,
    db: Session
) -> None:
    # Create a test post first
    post_repo = PostRepository(db)
    post = post_repo.create(
        PostCreate(
            title="Original Title",
            content="Original content",
            published=True
        ),
        author_id=1
    )

    data = {
        "title": "Updated Title",
        "content": "Updated content",
        "tags": ["new", "tags"]
    }
    response = client.put(
        f"{settings.API_V1_STR}/posts/{post.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["content"] == data["content"]
    assert len(content["tags"]) == 2

def test_delete_post(
    client: TestClient,
    normal_user_token_headers: dict,
    db: Session
) -> None:
    # Create a test post first
    post_repo = PostRepository(db)
    post = post_repo.create(
        PostCreate(
            title="Test Post",
            content="Content",
            published=True
        ),
        author_id=1
    )

    response = client.delete(
        f"{settings.API_V1_STR}/posts/{post.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 204

    # Verify post is deleted
    post = post_repo.get(post.id)
    assert post is None

def test_filter_posts_by_tag(
    client: TestClient,
    normal_user_token_headers: dict,
    db: Session
) -> None:
    # Create posts with different tags
    post_repo = PostRepository(db)
    post_repo.create(
        PostCreate(
            title="Post with tech tag",
            content="Content",
            published=True,
            tags=["tech"]
        ),
        author_id=1
    )
    post_repo.create(
        PostCreate(
            title="Post with news tag",
            content="Content",
            published=True,
            tags=["news"]
        ),
        author_id=1
    )

    response = client.get(
        f"{settings.API_V1_STR}/posts/?tag=tech",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["items"]) == 1
    assert "tech" in [tag["name"] for tag in content["items"][0]["tags"]]

def test_unauthorized_operations(client: TestClient) -> None:
    # Try to create post without authentication
    response = client.post(
        f"{settings.API_V1_STR}/posts/",
        json={"title": "Test", "content": "Content"}
    )
    assert response.status_code == 401

    # Try to read posts without authentication
    response = client.get(f"{settings.API_V1_STR}/posts/")
    assert response.status_code == 401

def test_update_others_post(
    client: TestClient,
    normal_user_token_headers: dict,
    superuser_token_headers: dict,
    db: Session
) -> None:
    # Create a post as superuser
    response = client.post(
        f"{settings.API_V1_STR}/posts/",
        headers=superuser_token_headers,
        json={
            "title": "Superuser's post",
            "content": "Content",
            "published": True
        }
    )
    post_id = response.json()["id"]

    # Try to update it as normal user
    response = client.put(
        f"{settings.API_V1_STR}/posts/{post_id}",
        headers=normal_user_token_headers,
        json={
            "title": "Trying to update",
            "content": "New content"
        }
    )
    assert response.status_code == 403