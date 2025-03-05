from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# Tag schemas
class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)

class TagCreate(TagBase):
    pass

class TagUpdate(TagBase):
    name: Optional[str] = Field(None, min_length=1, max_length=50)

class Tag(TagBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Post schemas
class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    summary: Optional[str] = Field(None, max_length=500)
    published: Optional[bool] = False
    
class PostCreate(PostBase):
    tags: Optional[List[str]] = []  # List of tag names

class PostUpdate(PostBase):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None

class PostInDBBase(PostBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime
    tags: List["Tag"] = []

    model_config = ConfigDict(from_attributes=True)


class Post(PostInDBBase):
    pass

# Author info for post responses
class AuthorInfo(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PostWithAuthor(Post):
    author: AuthorInfo
    
    model_config = ConfigDict(from_attributes=True)

# Response schemas
class PostPage(BaseModel):
    items: List[Post]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)

class PostResponse(PostBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime
    author: "AuthorInfo"
    tags: List["Tag"] = []

    model_config = ConfigDict(from_attributes=True)
    
PostInDBBase.model_rebuild()
Post.model_rebuild()
PostWithAuthor.model_rebuild()