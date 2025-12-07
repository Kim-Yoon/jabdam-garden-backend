# models/post_like.py
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Session, relationship
from database import Base


class PostLike(Base):
    __tablename__ = "PostLike"
    
    # 1. 고유 ID (PK) - 관리와 확장성을 위해 필요
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("Posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # 5. 중복 방지: 한 사용자가 같은 게시물에 중복으로 좋아요 불가
    __table_args__ = (
        UniqueConstraint('post_id', 'user_id', name='unique_post_user_like'),
    )
    
    post = relationship("Post", back_populates="likes")
    user = relationship("User", back_populates="likes")


# CRUD 함수들
def get_like(db: Session, post_id: int, user_id: int) -> Optional[PostLike]:
    """특정 게시글에 대한 사용자의 좋아요 조회"""
    return db.query(PostLike).filter(
        PostLike.post_id == post_id,
        PostLike.user_id == user_id
    ).first()

def create_like(db: Session, post_id: int, user_id: int) -> PostLike:
    """좋아요 생성"""
    new_like = PostLike(post_id=post_id, user_id=user_id)
    db.add(new_like)
    db.flush()
    return new_like

def delete_like(db: Session, post_id: int, user_id: int) -> bool:
    """좋아요 삭제"""
    like = get_like(db, post_id, user_id)
    if like:
        db.delete(like)
        return True
    return False

def get_post_likes(db: Session, post_id: int):
    """게시글의 모든 좋아요 조회"""
    return db.query(PostLike).filter(PostLike.post_id == post_id).all()