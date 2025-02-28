from fastapi import APIRouter
from api.v1.endpoints import auth, posts, cache

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])
api_router.include_router(cache.router, prefix="/cache", tags=["system"])

# Add other routers here as we create them
# Example:
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(items.router, prefix="/items", tags=["items"])