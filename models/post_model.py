# model/post_model.py
"""게시글 ORM 모델 및 데이터 접근 함수."""
from typing import Optional
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Session, relationship

from database import Base

class Post(Base):
    __tablename__ = "Posts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)  # ForeignKey는 DB 스키마 변경 없이 relationship만 추가
    title = Column(String(26), nullable=False)
    content = Column(Text, nullable=False)  # LONGTEXT는 Text로 매핑
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

def get_posts(db: Session):
    posts = db.query(Post).filter(Post.is_deleted != True).all()
    return posts

def get_post_by_id(db: Session, post_id: int) -> Optional[Post]:
    post = db.query(Post).filter(Post.id == post_id).first()
    return post

def create_post(db: Session, data: dict, user_id: int):
    new_post = Post(
        user_id=user_id,
        **data
    )
    
    db.add(new_post)
    db.flush()
    return new_post

def update_post(db: Session, updates: dict, post_id: int):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return None
        
    for key, value in updates.items():
        setattr(post, key, value)
    return post

def delete_post(db: Session, post_id: int):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return None
        
    post.is_deleted = True    
    post.deleted_at = datetime.now()
    return True 