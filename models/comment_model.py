# model/comment_model.py
"""댓글 ORM 모델 및 데이터 접근 함수."""
from typing import Optional

from sqlalchemy import Column, Integer, Boolean, DateTime, Text, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, selectinload

from database import Base


class Comment(Base):
    __tablename__ = "Comments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # User 관계 추가 (user_name 조회용)
    user = relationship("User", foreign_keys=[user_id], primaryjoin="Comment.user_id == User.id")


# 댓글 작성
async def add_comment(db: AsyncSession, data: dict, post_id: int, user_id: int):
    new_comment = Comment(
        user_id=user_id,
        post_id=post_id,
        **data
    )
    db.add(new_comment)
    await db.flush()
    return new_comment


# 특정 댓글 조회
async def get_comment_by_id(db: AsyncSession, comment_id: int) -> Optional[Comment]:
    result = await db.execute(
        select(Comment)
        .where(Comment.id == comment_id)
        .options(selectinload(Comment.user))
    )
    return result.scalars().first()


# 댓글 업데이트
async def update_comment(db: AsyncSession, updates: dict, comment_id: int):
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id)
    )
    comment = result.scalars().first()
    if not comment:
        return None
        
    for key, value in updates.items():
        setattr(comment, key, value)
    return comment


# 댓글 삭제
async def delete_comment(db: AsyncSession, comment_id: int):
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id)
    )
    comment = result.scalars().first()
    if not comment:
        return None
        
    comment.is_deleted = True    
    comment.deleted_at = func.now()
    return True


# 특정 게시글의 댓글 목록 (페이징)
async def get_comments_by_post_id(
    db: AsyncSession, 
    post_id: int, 
    skip: int = 0, 
    limit: int = 10, 
    excluded_deleted: bool = True
):
    query = select(Comment).where(Comment.post_id == post_id)
    
    # 삭제된 댓글 제외 옵션
    if excluded_deleted:
        query = query.where(Comment.is_deleted == False)
    
    # 최신순 정렬
    query = query.order_by(Comment.created_at.desc())
    
    # 페이징
    query = query.offset(skip).limit(limit)
    
    # user relationship eager load
    query = query.options(selectinload(Comment.user))
    
    result = await db.execute(query)
    return result.scalars().all()


# AI 정원사 댓글 개수 조회
async def count_ai_comments(db: AsyncSession, post_id: int) -> int:
    """해당 게시물의 AI 정원사 댓글 개수를 센다 (🤖로 시작하는 댓글)"""
    result = await db.execute(
        select(func.count(Comment.id)).where(
            Comment.post_id == post_id,
            Comment.is_deleted == False,
            Comment.content.like('🤖%')
        )
    )
    return result.scalar() or 0
