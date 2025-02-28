from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from models.user import User
from core.security import get_password_hash
from schemas.user import UserCreate, UserUpdate

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def create(self, user_in: UserCreate) -> User:
        db_user = User(
            email=user_in.email,
            username=user_in.username,
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            role=user_in.role,
            is_active=user_in.is_active
        )
        try:
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )

    def update(self, id: int, user_in: UserUpdate) -> Optional[User]:
        db_user = self.get(id)
        if not db_user:
            return None

        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(db_user, field, value)

        try:
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )

    def delete(self, id: int) -> bool:
        db_user = self.get(id)
        if not db_user:
            return False
        
        self.db.delete(db_user)
        self.db.commit()
        return True

    def update_refresh_token(self, user_id: int, refresh_token: Optional[str]) -> None:
        db_user = self.get(user_id)
        if db_user:
            db_user.refresh_token = refresh_token
            self.db.commit()