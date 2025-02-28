from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict, constr
from datetime import datetime
from models.user import UserRole

class UserBase(BaseModel):
    email: EmailStr
    username: constr(min_length=3, max_length=50)
    full_name: Optional[str] = None
    role: Optional[UserRole] = UserRole.USER
    is_active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    password: constr(min_length=8)

class UserUpdate(UserBase):
    password: Optional[constr(min_length=8)] = None

class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_superuser: bool

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    hashed_password: str

# Removed UserWithPosts to avoid circular imports

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: int
    exp: datetime
    type: Optional[str] = None