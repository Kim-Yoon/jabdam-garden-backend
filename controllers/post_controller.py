"""게시글 관련 비즈니스 로직."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import post_model, post_like
from models.post_model import Post
from models.post_like import get_like
from schemas.post_schema import PostCreate, PostResponse, PostUpdate
from utils.post_validators import validate_post_owner


# 게시글 목록 조회
async def get_posts(db: AsyncSession):
    posts = await post_model.get_posts(db)
    return [PostResponse.model_validate(p) for p in posts]


async def get_post(post: Post, db: AsyncSession, increment_view: bool = True):
    if increment_view:
        post.view_count += 1
        await db.commit()
        # refresh 후 relationship이 lazy 상태로 돌아가므로 다시 eager load
        result = await db.execute(
            select(Post)
            .where(Post.id == post.id)
            .options(selectinload(Post.comments), selectinload(Post.user))
        )
        post = result.scalar_one()
    return PostResponse.model_validate(post)


# 게시물 작성
async def create_post(data: PostCreate, db: AsyncSession, user_id: int):
    post_data = data.model_dump()
    new_post = await post_model.create_post(db, post_data, user_id)
    
    await db.commit()
    # refresh 후 relationship이 lazy 상태로 돌아가므로 다시 eager load
    result = await db.execute(
        select(Post)
        .where(Post.id == new_post.id)
        .options(selectinload(Post.comments), selectinload(Post.user))
    )
    new_post = result.scalar_one()
    return PostResponse.model_validate(new_post)


# 게시물 수정
async def update_post(post: Post, data: PostUpdate, db: AsyncSession, user_id: int):
    validate_post_owner(post, user_id)
    update_data = data.model_dump(exclude_unset=True)
        
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 내용이 없습니다"
        )

    updated_post = await post_model.update_post(db, update_data, post.id)
    if not updated_post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="게시물 수정에 실패했습니다"
        )

    try:
        await db.commit()
        # refresh 후 relationship이 lazy 상태로 돌아가므로 다시 eager load
        result = await db.execute(
            select(Post)
            .where(Post.id == updated_post.id)
            .options(selectinload(Post.comments), selectinload(Post.user))
        )
        updated_post = result.scalar_one()
        return PostResponse.model_validate(updated_post)
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"게시물 수정 중 오류가 발생했습니다: {str(e)}"
        )


async def delete_post(post: Post, db: AsyncSession, user_id: int):
    validate_post_owner(post, user_id)

    try:
        await post_model.delete_post(db, post.id)
        await db.commit()
        return {"message": "게시물이 성공적으로 삭제되었습니다"}
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"게시물 삭제 중 오류가 발생했습니다: {str(e)}"
        )


## 좋아요 관련
async def like_post(post: Post, user_id: int, db: AsyncSession):
    like = await get_like(db, post.id, user_id)
    if like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 좋아요를 눌렀습니다"
        )
        
    new_like = await post_like.create_like(db, post.id, user_id)
    await db.commit()
    await db.refresh(new_like)
    return new_like


async def unlike_post(post: Post, user_id: int, db: AsyncSession):
    like = await get_like(db, post.id, user_id)
    if not like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이 게시물에 좋아요를 누르지 않았습니다"
        )
        
    deleted_like = await post_like.delete_like(db, post.id, user_id)
    if not deleted_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="좋아요 취소에 실패했습니다"
        )
        
    await db.commit()
    return {"message": "좋아요가 성공적으로 취소되었습니다"}


async def get_post_likes(post: Post, db: AsyncSession):
    likes = await post_like.get_post_likes(db, post.id)
    return likes