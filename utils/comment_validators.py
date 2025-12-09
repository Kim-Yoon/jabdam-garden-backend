from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.comment_model import get_comment_by_id


async def get_valid_comment(
    comment_id: int = Path(..., ge=1, description="댓글 ID"),
    db: AsyncSession = Depends(get_db)
):
    """댓글 존재 및 삭제 여부 확인 (Dependency)"""
    comment = await get_comment_by_id(db, comment_id)
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="댓글을 찾을 수 없습니다"
        )
    
    if comment.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="삭제된 댓글입니다"
        )
    
    return comment


def validate_comment_owner(comment, user_id: int):
    """댓글 작성자 권한 확인"""
    if comment.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="댓글을 수정/삭제할 권한이 없습니다"
        )
