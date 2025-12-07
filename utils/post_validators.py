from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from database import get_db
from models.post_model import get_post_by_id
from models.post_like import PostLike

def get_valid_post(
    post_id: int = Path(..., ge=1, description="게시물 ID"),
    db: Session = Depends(get_db)
):
    """게시물 존재 및 삭제 여부 확인 (Dependency)"""
    post = get_post_by_id(db, post_id)
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시물을 찾을 수 없습니다"
        )
    
    if post.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="삭제된 게시물입니다"
        )
    
    return post

def validate_post_owner(post, user_id: int):
    """게시물 작성자 권한 확인"""
    if post.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="게시물을 수정/삭제할 권한이 없습니다"
        )

def get_like(db: Session, post_id: int, user_id: int):
    """좋아요 존재 여부 확인 (에러 없이 반환)"""
    like = db.query(PostLike).filter(
        PostLike.post_id == post_id,
        PostLike.user_id == user_id
    ).first()
    
    return like  # 있으면 Like 객체, 없으면 None