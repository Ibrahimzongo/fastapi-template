from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import time
import uuid

from core.config import settings
from core.logging import setup_logging, RequestIdFilter
from core.docs import description, tags_metadata, responses
from core.rate_limiter import create_rate_limiter
from api.middlewares.rate_limiting import RateLimitMiddleware
from api.v1.api import api_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create rate limiter
rate_limiter = create_rate_limiter(settings.REDIS_URL)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=description,
    openapi_tags=tags_metadata,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=None,
    redoc_url=None,
    responses=responses,
    openapi_version="3.0.3"
)

# Custom docs endpoint
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=f"{settings.PROJECT_NAME} - API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_favicon_url="/static/favicon.ico",
        init_oauth=None
    )

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    rate_limiter=rate_limiter,
    exclude_paths=["/health", "/metrics", "/docs", f"{settings.API_V1_STR}/openapi.json"]
)

# Ajout du middleware de cache temporairement désactivé pour debug
# app.add_middleware(
#     CacheMiddleware,
#     cache_patterns=["/api/v1/posts", "/api/v1/tags"],
#     exclude_patterns=["/docs", "/openapi.json", "/metrics", "/health", "/api/v1/auth"],
#     cache_expire=300  # 5 minutes
# )

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Add request ID to logger
    logger.addFilter(RequestIdFilter(request_id))
    
    # Log request
    logger.info(
        f"Request started",
        extra={
            "path": request.url.path,
            "method": request.method,
            "request_id": request_id
        }
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log response
        logger.info(
            f"Request completed",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "process_time": process_time,
                "request_id": request_id
            }
        )
        
        return response
        
    except Exception as exc:
        logger.exception(
            f"Request failed",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error": str(exc),
                "request_id": request_id
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# Add API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    """
    Endpoint de vérification de la santé de l'API.
    """
    try:
        # Vérifier la connexion Redis
        redis_ok = rate_limiter.redis.ping()
        redis_status = "healthy" if redis_ok else "unhealthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "redis": redis_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)