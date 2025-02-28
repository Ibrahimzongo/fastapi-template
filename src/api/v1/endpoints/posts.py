from typing import Any, Optional
import json
import logging
from fastapi import APIRouter, Depends, Query, HTTPException, status, Response, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from db.repositories.post import PostRepository
from models.user import User
from schemas.post import (
    Post,
    PostCreate,
    PostUpdate,
    PostWithAuthor,
    PostPage,
    Tag,
)
from core.cache import redis_client

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/",
    response_model=PostPage,
    responses={
        200: {
            "description": "Liste des posts avec pagination",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "title": "Premier post",
                                "content": "Contenu du post...",
                                "summary": "Résumé du post",
                                "published": True,
                                "author_id": 1,
                                "tags": [
                                    {"id": 1, "name": "tech", "description": "Tech posts"}
                                ],
                                "created_at": "2024-02-24T12:00:00",
                                "updated_at": "2024-02-24T12:00:00"
                            }
                        ],
                        "total": 50,
                        "page": 1,
                        "size": 10,
                        "pages": 5
                    }
                }
            }
        }
    }
)
async def get_posts(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    author_id: Optional[int] = None,
    tag: Optional[str] = None,
    published: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    request: Request = None,
) -> Any:
    """
    Retrieve posts with pagination.
    """
    # Check if cached response exists
    cache_key = f"posts:list:skip={skip}:limit={limit}:author={author_id}:tag={tag}:published={published}"
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")

    # Get posts from database
    post_repo = PostRepository(db)
    posts, total = post_repo.get_multi(
        skip=skip,
        limit=limit,
        author_id=author_id,
        tag=tag,
        published=published
    )
    
    # Calculate total pages
    pages = (total + limit - 1) // limit
    
    # Prepare response
    response = {
        "items": posts,
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit,
        "pages": pages
    }
    
    # Cache the response
    if redis_client:
        try:
            redis_client.setex(
                cache_key,
                60 * 5,  # Cache for 5 minutes
                json.dumps(jsonable_encoder(response))
            )
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")
    
    return response

@router.post("/", response_model=Post, status_code=status.HTTP_201_CREATED)
async def create_post(
    *,
    db: Session = Depends(get_db),
    post_in: PostCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create new post.
    """
    post_repo = PostRepository(db)
    post = post_repo.create(post_in, current_user.id)
    
    # Invalidate cache
    if redis_client:
        try:
            # Invalider la liste des posts
            keys_to_delete = redis_client.keys("posts:list:*")
            if keys_to_delete:
                redis_client.delete(*keys_to_delete)
                logger.info(f"Invalidated {len(keys_to_delete)} cache entries after post creation")
        except Exception as e:
            logger.warning(f"Redis cache invalidation error: {e}")
    
    return post

@router.get("/{post_id}", response_model=PostWithAuthor)
async def get_post(
    *,
    db: Session = Depends(get_db),
    post_id: int,
    current_user: User = Depends(get_current_user),
    request: Request = None,
) -> Any:
    """
    Get post by ID.
    """
    # Check if cached response exists
    cache_key = f"posts:detail:{post_id}"
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")
    
    # Get post from database
    post_repo = PostRepository(db)
    post = post_repo.get(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Update view count
    if hasattr(post, 'views_count'):
        post.views_count += 1
        db.commit()
    
    # Cache the response
    if redis_client:
        try:
            # Cache for 10 minutes
            redis_client.setex(
                cache_key,
                60 * 10,
                json.dumps(jsonable_encoder(post))
            )
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")
    
    return post

@router.put("/{post_id}", response_model=Post)
async def update_post(
    *,
    db: Session = Depends(get_db),
    post_id: int,
    post_in: PostUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update post.
    """
    post_repo = PostRepository(db)
    post = post_repo.update(post_id, post_in, current_user.id)
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Invalidate cache
    if redis_client:
        try:
            # Invalider les caches spécifiques
            keys_to_delete = redis_client.keys(f"posts:detail:{post_id}")
            keys_to_delete.extend(redis_client.keys("posts:list:*"))
            
            if keys_to_delete:
                redis_client.delete(*keys_to_delete)
                logger.info(f"Invalidated {len(keys_to_delete)} cache entries after post update")
        except Exception as e:
            logger.warning(f"Redis cache invalidation error: {e}")
    
    return post

@router.delete("/{post_id}")
async def delete_post(
    *,
    db: Session = Depends(get_db),
    post_id: int,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete post.
    """
    post_repo = PostRepository(db)
    result = post_repo.delete(post_id, current_user.id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Invalidate cache
    if redis_client:
        try:
            # Invalider les caches spécifiques
            keys_to_delete = redis_client.keys(f"posts:detail:{post_id}")
            keys_to_delete.extend(redis_client.keys("posts:list:*"))
            
            if keys_to_delete:
                redis_client.delete(*keys_to_delete)
                logger.info(f"Invalidated {len(keys_to_delete)} cache entries after post deletion")
        except Exception as e:
            logger.warning(f"Redis cache invalidation error: {e}")
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/tags/", response_model=list[Tag])
def get_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get all tags.
    """
    tags = db.query(Tag).all()
    return tags