import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.config import settings
from db.repositories.user import UserRepository
from schemas.user import UserCreate, UserRole

def test_register_user(client: TestClient, db: Session) -> None:
    data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "username": "testuser",
        "full_name": "Test User",
        "role": UserRole.USER
    }
    response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["email"] == data["email"]
    assert content["username"] == data["username"]
    assert "id" in content

def test_register_existing_email(client: TestClient, db: Session) -> None:
    # Create a user first
    user_repo = UserRepository(db)
    user_in = UserCreate(
        email="existing@example.com",
        password="testpass123",
        username="existinguser",
        full_name="Existing User"
    )
    user_repo.create(user_in)

    # Try to register with same email
    data = {
        "email": "existing@example.com",
        "password": "anotherpass123",
        "username": "newuser",
        "full_name": "New User"
    }
    response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json=data,
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_login_success(client: TestClient, db: Session) -> None:
    # Create a user first
    user_repo = UserRepository(db)
    user_in = UserCreate(
        email="login@example.com",
        password="testpass123",
        username="loginuser",
        full_name="Login User"
    )
    user_repo.create(user_in)

    # Try to login
    data = {
        "username": "loginuser",
        "password": "testpass123"
    }
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=data,  # Note: using data instead of json for OAuth2 form
    )
    assert response.status_code == 200
    content = response.json()
    assert "access_token" in content
    assert "refresh_token" in content
    assert content["token_type"] == "bearer"

def test_login_wrong_password(client: TestClient, db: Session) -> None:
    # Create a user first
    user_repo = UserRepository(db)
    user_in = UserCreate(
        email="wrong@example.com",
        password="testpass123",
        username="wronguser",
        full_name="Wrong User"
    )
    user_repo.create(user_in)

    # Try to login with wrong password
    data = {
        "username": "wronguser",
        "password": "wrongpass123"
    }
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=data,
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_refresh_token_success(client: TestClient, db: Session, normal_user_token_headers) -> None:
    user = UserRepository(db).get_by_username("testuser")
    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": user.refresh_token},
    )
    assert response.status_code == 200
    content = response.json()
    assert "access_token" in content
    assert "refresh_token" in content
    assert content["token_type"] == "bearer"

def test_logout_success(client: TestClient, db: Session, normal_user_token_headers) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/auth/logout",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Successfully logged out"

    # Verify refresh token is revoked
    user = UserRepository(db).get_by_username("testuser")
    assert user.refresh_token is None