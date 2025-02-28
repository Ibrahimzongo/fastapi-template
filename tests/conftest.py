import pytest
from typing import Dict, Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.config import settings
from db.session import get_db
from db.repositories.user import UserRepository
from main import app
from models.base import Base
from schemas.user import UserCreate
from core.security import create_access_token, create_refresh_token

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
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db: TestingSessionLocal) -> Generator:
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def normal_user(db: TestingSessionLocal) -> UserCreate:
    user_in = UserCreate(
        email="test@example.com",
        password="testpass123",
        username="testuser",
        full_name="Test User"
    )
    user_repo = UserRepository(db)
    user = user_repo.create(user_in)
    return user

@pytest.fixture(scope="function")
def normal_user_token_headers(
    client: TestClient, normal_user: UserCreate
) -> Dict[str, str]:
    access_token = create_access_token(
        normal_user.id
    )
    refresh_token = create_refresh_token(
        normal_user.id
    )
    
    # Store refresh token
    db = TestingSessionLocal()
    user_repo = UserRepository(db)
    user_repo.update_refresh_token(normal_user.id, refresh_token)
    db.close()
    
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def superuser(db: TestingSessionLocal) -> UserCreate:
    user_in = UserCreate(
        email="admin@example.com",
        password="adminpass123",
        username="admin",
        full_name="Admin User",
        is_superuser=True
    )
    user_repo = UserRepository(db)
    user = user_repo.create(user_in)
    return user

@pytest.fixture(scope="function")
def superuser_token_headers(
    client: TestClient, superuser: UserCreate
) -> Dict[str, str]:
    access_token = create_access_token(
        superuser.id
    )
    refresh_token = create_refresh_token(
        superuser.id
    )
    
    # Store refresh token
    db = TestingSessionLocal()
    user_repo = UserRepository(db)
    user_repo.update_refresh_token(superuser.id, refresh_token)
    db.close()
    
    return {"Authorization": f"Bearer {access_token}"}