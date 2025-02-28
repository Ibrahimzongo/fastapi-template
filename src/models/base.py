from datetime import datetime
from typing import Any
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime
from typing import Optional

class Base(DeclarativeBase):
    """Base class for all models"""
    
    # Auto-generate __tablename__
    @classmethod
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    # Common columns for all models
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )