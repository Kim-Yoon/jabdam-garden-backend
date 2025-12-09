# model/post_model.py
"""게시글 ORM 모델 및 데이터 접근 함수."""
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, selectinload

from database import Base


class Post(Base):
    __tablename__ = "Posts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String(26), nullable=False)
    content = Column(Text, nullable=False)
    img = Column(String(500), nullable=True)
    view_count = Column(Integer, default=0, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 좋아요 관계 추가
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")
    
    # User 관계 추가 (user_name 조회용)
    user = relationship("User", foreign_keys=[user_id], primaryjoin="Post.user_id == User.id")
    
    # 댓글 관계 추가 (comment_count 조회용)
    comments = relationship("Comment", foreign_keys="Comment.post_id", primaryjoin="Post.id == Comment.post_id")


async def get_posts(db: AsyncSession):
    result = await db.execute(
        select(Post)
        .where(Post.is_deleted != True)
        .options(selectinload(Post.comments), selectinload(Post.user))
    )
    return result.scalars().all()


async def get_post_by_id(db: AsyncSession, post_id: int) -> Optional[Post]:
    result = await db.execute(
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.comments), selectinload(Post.user))
    )
    return result.scalars().first()


async def create_post(db: AsyncSession, data: dict, user_id: int):
    new_post = Post(
        user_id=user_id,
        **data
    )
    db.add(new_post)  # add()는 동기 메서드
    await db.flush()
    return new_post


async def update_post(db: AsyncSession, updates: dict, post_id: int):
    result = await db.execute(
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.comments), selectinload(Post.user))
    )
    post = result.scalars().first()
    if not post:
        return None
        
    for key, value in updates.items():
        setattr(post, key, value)
    return post


async def delete_post(db: AsyncSession, post_id: int):
    result = await db.execute(
        select(Post).where(Post.id == post_id)
    )
    post = result.scalars().first()
    if not post:
        return None
        
    post.is_deleted = True    
    post.deleted_at = func.now()
    return True