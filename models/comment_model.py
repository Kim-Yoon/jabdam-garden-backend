# model/comment_model.py
"""댓글 ORM 모델 및 데이터 접근 함수."""
from typing import Optional
from datetime import datetime

from sqlalchemy import Column, Integer, Boolean, DateTime, Text, func
from sqlalchemy.orm import Session, relationship

from database import Base

class Comment(Base):
    __tablename__ = "Comments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False)  # LONGTEXT는 Text로 매핑    
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # User 관계 추가 (user_name 조회용)
    user = relationship("User", foreign_keys=[user_id], primaryjoin="Comment.user_id == User.id")


# 댓글 작성
def add_comment(db: Session, data: dict, post_id: int, user_id: int):
    new_comment = Comment(
        user_id=user_id,
        post_id=post_id,
        **data
    )
    
    db.add(new_comment)
    db.flush()
    return new_comment

# 특정 댓글 조회
def get_comment_by_id(db: Session, comment_id: int) -> Optional[Comment]:
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    return comment

# 댓글 업데이트
def update_comment(db: Session, updates: dict, comment_id:int):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        return None
        
    for key, value in updates.items():
        setattr(comment, key, value)
    return comment
    

# 댓글 삭제
def delete_comment(db: Session, comment_id: int):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        return None
        
    comment.is_deleted = True    
    comment.deleted_at = datetime.now()
    return True 

# 특정 게시글의 댓글 목록 (페이징)
def get_comments_by_post_id(db: Session, post_id: int, skip: int = 0, limit: int = 10, excluded_deleted : bool = True):

    query = db.query(Comment).filter(Comment.post_id == post_id)
    
    # 삭제된 댓글 제외 옵션
    if excluded_deleted:
        query = query.filter(Comment.is_deleted == False)
    
    # 최신순 정렬
    query = query.order_by(Comment.created_at.desc())

    # 페이징 여부 확인
    comments = query.offset(skip).limit(limit).all()
    
    return comments
    
