from sqlalchemy import String, Text, ForeignKey, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List

from .base import Base

class Tag(Base):
    """Tag model"""
    
    __tablename__ = "tags"
    
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    
    # Relationships
    posts: Mapped[List["Post"]] = relationship(
        "Post", 
        secondary="post_tags",
        back_populates="tags",
        lazy="select"
    )

class PostTag(Base):
    """Association table between posts and tags"""
    
    __tablename__ = "post_tags"
    
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), nullable=False
    )

class Post(Base):
    """Post model"""
    
    __tablename__ = "posts"
    
    title: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    summary: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    published: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    
    # Relationships
    author: Mapped["User"] = relationship(
        "User", back_populates="posts", lazy="select"
    )
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[List[Tag]] = relationship(
        Tag,
        secondary="post_tags",
        back_populates="posts",
        lazy="select"
    )