from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from models.post import Post, Tag, PostTag
from schemas.post import PostCreate, PostUpdate

class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        return self.db.query(Tag).filter(Tag.name == name).first()

    def create_tag(self, name: str, description: Optional[str] = None) -> Tag:
        db_tag = Tag(name=name, description=description)
        self.db.add(db_tag)
        self.db.commit()
        self.db.refresh(db_tag)
        return db_tag

    def get_or_create_tag(self, name: str) -> Tag:
        tag = self.get_tag_by_name(name)
        if not tag:
            tag = self.create_tag(name)
        return tag

    def get(self, post_id: int) -> Optional[Post]:
        return self.db.query(Post).filter(Post.id == post_id).first()

    def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        author_id: Optional[int] = None,
        tag: Optional[str] = None,
        published: Optional[bool] = None
    ) -> Tuple[List[Post], int]:
        query = self.db.query(Post)

        if author_id is not None:
            query = query.filter(Post.author_id == author_id)
        
        if tag:
            query = query.join(PostTag).join(Tag).filter(Tag.name == tag)
            
        if published is not None:
            query = query.filter(Post.published == published)

        total = query.count()
        posts = query.offset(skip).limit(limit).all()
        
        return posts, total

    def create(self, obj_in: PostCreate, author_id: int) -> Post:
        db_post = Post(
            title=obj_in.title,
            content=obj_in.content,
            summary=obj_in.summary,
            published=obj_in.published,
            author_id=author_id
        )
        self.db.add(db_post)
        self.db.flush()  # Permet d'obtenir l'ID avant d'ajouter des relations
        if obj_in.tags:
            for tag_name in obj_in.tags:
                tag = self.get_or_create_tag(tag_name)
                if tag not in db_post.tags:
                    db_post.tags.append(tag)
        self.db.commit()
        self.db.refresh(db_post)
        return db_post

    def update(
        self, 
        post_id: int, 
        obj_in: PostUpdate, 
        current_user_id: int
    ) -> Optional[Post]:
        db_post = self.get(post_id)
        if not db_post:
            return None
            
        # Check if user is author
        if db_post.author_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Handle tags separately
        if "tags" in update_data:
            tags = update_data.pop("tags")
            db_post.tags = []  # Remove existing tags
            for tag_name in tags:
                tag = self.get_or_create_tag(tag_name)
                db_post.tags.append(tag)

        # Update other fields
        for field, value in update_data.items():
            setattr(db_post, field, value)

        self.db.add(db_post)
        self.db.commit()
        self.db.refresh(db_post)
        return db_post

    def delete(self, post_id: int, current_user_id: int) -> bool:
        db_post = self.get(post_id)
        if not db_post:
            return False
            
        # Check if user is author
        if db_post.author_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        self.db.delete(db_post)
        self.db.commit()
        return True

    def get_post_count_by_author(self, author_id: int) -> int:
        return self.db.query(func.count(Post.id)).filter(
            Post.author_id == author_id
        ).scalar()