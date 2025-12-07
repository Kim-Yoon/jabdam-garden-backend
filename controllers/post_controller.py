"""게시글 관련 비즈니스 로직."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import post_model, post_like
from models.post_model import Post
from schemas.post_schema import PostCreate, PostResponse, PostUpdate
from utils.post_validators import validate_post_owner, get_like
from models.user_model import User

# 게시글 목록 조회
def get_posts(db: Session):
    posts = post_model.get_posts(db)
    return [PostResponse.model_validate(p) for p in posts]

def get_post(post: Post, db: Session, increment_view: bool = True):
    if increment_view:
        post.view_count += 1
        db.commit()
        db.refresh(post)
    return PostResponse.model_validate(post)

# 게시물 작성
def create_post(data : PostCreate, db: Session, user_id: int):
    post_data = data.model_dump() # dict로 변환
    new_post = post_model.create_post(db, post_data, user_id)
    
    db.commit()
    db.refresh(new_post)
    return new_post

# 게시물 수정
def update_post( post: Post, data: PostUpdate, db: Session, user_id: int):
    validate_post_owner(post, user_id)
    update_data = data.model_dump(exclude_unset=True)
        
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 내용이 없습니다"
        )

    updated_post = post_model.update_post(db, update_data, post.id)
    if not updated_post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="게시물 수정에 실패했습니다"
        )

    try:
        db.commit()
        db.refresh(updated_post)
        return PostResponse.model_validate(updated_post)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"update_failed: {str(e)}"
        )
    

def delete_post(post: Post, db: Session, user_id: int):
    validate_post_owner(post, user_id)

    try:
        del_post = post_model.delete_post(db, post.id)
        db.commit()
        return {"message": "게시물이 성공적으로 삭제되었습니다"}
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터베이스 오류: {str(e)}"
        )
    
## 좋아요 관련
def like_post(post: Post, user_id: int, db: Session):
    like = get_like(db, post.id, user_id)
    if like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 좋아요를 눌렀습니다"
        )
        
    new_like = post_like.create_like(db, post.id, user_id)
    db.commit()
    db.refresh(new_like)
    return new_like

def unlike_post(post: Post, user_id: int, db: Session):
    like = get_like(db, post.id, user_id)
    if not like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이 게시물에 좋아요를 누르지 않았습니다"
        )
        
    deleted_like = post_like.delete_like(db, post.id, user_id)
    if not deleted_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="좋아요 취소에 실패했습니다"
        )
        
    db.commit()
    return {"message": "좋아요가 성공적으로 취소되었습니다"}

def get_post_likes(post: Post, db: Session):
    likes = post_like.get_post_likes(db, post.id)
    return likes




    