# router/comment_router.py
"""댓글 관련 라우터 정의."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from controllers import comment_controller
from database import get_db
from models.comment_model import Comment
from models.post_model import Post
from schemas.comment_schema import CommentCreate, CommentUpdate
from utils.user_validators import get_active_user
from utils.comment_validators import get_valid_comment
from utils.post_validators import get_valid_post

router = APIRouter(prefix="/posts/{post_id}/comments")


# 특정 게시물의 댓글 조회 (인증 불필요)
@router.get("")
async def get_post_comments(
    post: Post = Depends(get_valid_post),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(10, ge=1, le=100, description="페이지당 개수"),
):
    skip = (page - 1) * limit
    return await comment_controller.get_comments_by_post(post, db, skip, limit)


# 댓글 작성 (인증 필요)
@router.post("", status_code=201)
async def create_comment(
    data: CommentCreate,
    user_id: int = Depends(get_active_user),
    post: Post = Depends(get_valid_post),
    db: AsyncSession = Depends(get_db)
):
    return await comment_controller.create_comment(data, post, db, user_id)


# 댓글 수정 (인증 필요)
@router.patch("/{comment_id}")
async def update_comment(
    data: CommentUpdate,
    user_id: int = Depends(get_active_user),
    comment: Comment = Depends(get_valid_comment),
    post: Post = Depends(get_valid_post),
    db: AsyncSession = Depends(get_db)
):
    return await comment_controller.update_comment(comment, data, db, user_id)


# 댓글 삭제 (인증 필요)
@router.delete("/{comment_id}")
async def delete_comment(
    user_id: int = Depends(get_active_user),
    post: Post = Depends(get_valid_post),
    comment: Comment = Depends(get_valid_comment),
    db: AsyncSession = Depends(get_db)
):
    return await comment_controller.delete_comment(post, comment, db, user_id)
