from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import jwt
from pydantic import ValidationError


from core.config import settings
from core.security import create_access_token, create_refresh_token, verify_password, decode_token
from api.deps import get_current_user
from db.session import get_db
from db.repositories.user import UserRepository
from models.user import User
from schemas.user import User as UserSchema, Token, UserCreate

router = APIRouter()

@router.post(
    "/register",
    response_model=UserSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Utilisateur créé avec succès",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "user@example.com",
                        "username": "johndoe",
                        "full_name": "John Doe",
                        "role": "user",
                        "is_active": True,
                        "created_at": "2024-02-24T12:00:00",
                        "updated_at": "2024-02-24T12:00:00"
                    }
                }
            }
        },
        400: {
            "description": "Email ou username déjà utilisé",
            "content": {
                "application/json": {
                    "example": {"detail": "Email already registered"}
                }
            }
        }
    }
)
def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Register new user.
    """
    user_repo = UserRepository(db)
    
    # Check if user with this email exists
    if user_repo.get_by_email(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    
    # Check if user with this username exists
    if user_repo.get_by_username(user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists",
        )
    
    user = user_repo.create(user_in)
    return user

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user_repo = UserRepository(db)
    user = user_repo.get_by_username(form_data.username)
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    # Store refresh token in database
    user_repo.update_refresh_token(user.id, refresh_token)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
def refresh_token(
    db: Session = Depends(get_db),
    refresh_token: str = Body(...),
) -> Any:
    """
    Refresh access token.
    """
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid refresh token",
            )
        user_id = int(payload.get("sub"))
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    user_repo = UserRepository(db)
    user = user_repo.get(user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    if user.refresh_token != refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token has been revoked",
        )

    access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)
    
    # Update refresh token in database
    user_repo.update_refresh_token(user_id, new_refresh_token)
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Logout user by revoking refresh token.
    """
    user_repo = UserRepository(db)
    user_repo.update_refresh_token(current_user.id, None)
    return {"message": "Successfully logged out"}