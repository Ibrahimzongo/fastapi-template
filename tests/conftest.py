import pytest
from typing import Dict, Generator, Optional, Tuple
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from models.user import User
from core.config import settings
from db.session import get_db
from db.repositories.user import UserRepository
from main import app
from models.base import Base
from schemas.user import UserCreate
from core.security import create_access_token, create_refresh_token
from fastapi import Request

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db() -> Generator:
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis pour les tests."""
    # Configuration complète du mock Redis
    mock_redis_client = MagicMock()
    
    # Méthodes standard
    mock_redis_client.ping.return_value = True
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    mock_redis_client.setex.return_value = True
    mock_redis_client.delete.return_value = True
    mock_redis_client.keys.return_value = []
    mock_redis_client.exists.return_value = False
    mock_redis_client.flushall.return_value = True
    mock_redis_client.expire.return_value = True
    
    # Pipeline
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [0, True, 1, True]
    mock_pipeline.zremrangebyscore.return_value = mock_pipeline
    mock_pipeline.zadd.return_value = mock_pipeline
    mock_pipeline.zcard.return_value = mock_pipeline
    mock_pipeline.expire.return_value = mock_pipeline
    mock_redis_client.pipeline.return_value = mock_pipeline
    
    # Appliquer le patch à tous les endroits où Redis est utilisé
    with patch("core.cache_base.redis_client", mock_redis_client), \
         patch("core.cache_base.is_redis_available", return_value=True), \
         patch("core.rate_limiter.redis_client", mock_redis_client), \
         patch("api.v1.endpoints.cache.redis_client", mock_redis_client), \
         patch("api.middlewares.cache.redis_client", mock_redis_client):
        yield mock_redis_client

class MockRateLimiter:
    def __init__(self, *args, **kwargs):
        pass

    def is_rate_limited(self, request: Request, user_id: Optional[int] = None) -> Tuple[bool, dict]:
        headers = {
            'X-RateLimit-Limit': '100',
            'X-RateLimit-Remaining': '99',
            'X-RateLimit-Reset': '0'
        }
        return False, headers

@pytest.fixture(scope="function")
def mock_rate_limiter():
    """Mock le RateLimiter pour éviter les appels à Redis"""
    with patch("core.rate_limiter.RateLimiter", MockRateLimiter), \
         patch("api.middlewares.rate_limiting.RateLimiter", MockRateLimiter):
        yield

@pytest.fixture(scope="function")
def client(db: Session, mock_redis, mock_rate_limiter) -> Generator:
    """Client de test avec bases de données et mocks configurés"""
    def override_get_db():
        try:
            yield db
        finally:
            pass  # Ne pas fermer la connexion ici pour éviter des fermetures doubles

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()
        
@pytest.fixture(scope="function")
def normal_user(db: Session) -> User:
    user_in = UserCreate(
        email="test@example.com",
        password="testpass123",
        username="testuser",
        full_name="Test User"
    )
    user_repo = UserRepository(db)
    user = user_repo.create(user_in)
    # Créer et enregistrer les tokens
    refresh_token = create_refresh_token(user.id)
    user_repo.update_refresh_token(user.id, refresh_token)
    return user

@pytest.fixture(scope="function")
def normal_user_token_headers(client: TestClient, normal_user: User) -> Dict[str, str]:
    access_token = create_access_token(normal_user.id)
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def superuser(db: Session) -> User:
    user_in = UserCreate(
        email="admin@example.com",
        password="adminpass123",
        username="admin",
        full_name="Admin User"
    )
    # Force ce user à être superuser
    user_repo = UserRepository(db)
    user = user_repo.create(user_in)
    user.is_superuser = True
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def superuser_token_headers(
    client: TestClient, superuser: User, db: Session
) -> Dict[str, str]:
    access_token = create_access_token(
        superuser.id
    )
    refresh_token = create_refresh_token(
        superuser.id
    )
    
    user_repo = UserRepository(db)
    user_repo.update_refresh_token(superuser.id, refresh_token)
    db.commit()
        
    return {"Authorization": f"Bearer {access_token}"}

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "redis: mark test as requiring redis"
    )