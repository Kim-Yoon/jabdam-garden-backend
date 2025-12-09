# controllers/comment_controller.py
"""댓글 관련 비즈니스 로직."""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import comment_model
from models.comment_model import Comment
from models.post_model import Post
from schemas.comment_schema import CommentCreate, CommentResponse, CommentUpdate
from utils.comment_validators import validate_comment_owner


# 특정 게시글의 댓글 목록 
async def get_comments_by_post(post: Post, db: AsyncSession, skip: int = 0, limit: int = 10):
    comments = await comment_model.get_comments_by_post_id(
        db, post.id, skip, limit, excluded_deleted=True
    )
    return [CommentResponse.model_validate(c) for c in comments]


# 댓글 작성
async def create_comment(data: CommentCreate, post: Post, db: AsyncSession, user_id: int):    
    comment_data = data.model_dump()
    new_cmt = await comment_model.add_comment(db, comment_data, post.id, user_id)

    await db.commit()
    # refresh 후 relationship이 lazy 상태로 돌아가므로 다시 eager load
    result = await db.execute(
        select(Comment)
        .where(Comment.id == new_cmt.id)
        .options(selectinload(Comment.user))
    )
    new_cmt = result.scalar_one()
    return CommentResponse.model_validate(new_cmt)


# 댓글 수정
async def update_comment(comment: Comment, data: CommentUpdate, db: AsyncSession, user_id: int):    
    validate_comment_owner(comment, user_id)
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 내용이 없습니다"
        )
    
    updated_comment = await comment_model.update_comment(db, update_data, comment.id)
    if not updated_comment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="댓글 수정에 실패했습니다"
        )
    try:
        await db.commit()
        # refresh 후 relationship이 lazy 상태로 돌아가므로 다시 eager load
        result = await db.execute(
            select(Comment)
            .where(Comment.id == updated_comment.id)
            .options(selectinload(Comment.user))
        )
        updated_comment = result.scalar_one()
        return CommentResponse.model_validate(updated_comment)
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"댓글 수정 중 오류가 발생했습니다: {str(e)}"
        )


# 댓글 삭제
async def delete_comment(post: Post, comment: Comment, db: AsyncSession, user_id: int):
    """댓글 삭제"""
    validate_comment_owner(comment, user_id)
    
    try:
        await comment_model.delete_comment(db, comment.id)
        await db.commit()
        return {"message": "댓글이 성공적으로 삭제되었습니다"}
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"댓글 삭제 중 오류가 발생했습니다: {str(e)}"
        )