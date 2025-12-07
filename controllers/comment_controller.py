# controllers/comment_controller.py
"""댓글 관련 비즈니스 로직."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import comment_model, post_model, user_model
from models.comment_model import Comment
from models.post_model import Post
from schemas.comment_schema import CommentCreate, CommentResponse, CommentUpdate
from utils.comment_validators import validate_comment_owner
    
#특정 게시글의 댓글 목록 
def get_comments_by_post(post: Post, db: Session, skip: int = 0, limit: int = 10):
    comments = comment_model.get_comments_by_post_id(db, post.id, skip, limit, excluded_deleted = True)
    return [CommentResponse.model_validate(c) for c in comments]

# 댓글 작성
def create_comment(data: CommentCreate, post: Post, db: Session, user_id: int):    
    # 내용 검증
    comment_data = data.model_dump() # dict로 변환
    new_cmt = comment_model.add_comment(db, comment_data, post.id, user_id)

    db.commit()
    db.refresh(new_cmt)
    return CommentResponse.model_validate(new_cmt)


# 댓글 수정
def update_comment(post: Post, comment: Comment, data: CommentUpdate, db: Session, user_id: int):    
    # 권한 확인
    validate_comment_owner(comment, user_id)
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 내용이 없습니다"
        )
    
    updated_comment = comment_model.update_comment(db, update_data, comment.id)
    if not updated_comment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="댓글 수정에 실패했습니다"
        )
    try:
        db.commit()
        db.refresh(updated_comment)
        return {"message": "댓글이 성공적으로 수정되었습니다"}
    except HTTPException:
        db.rollback()
        # 6. HTTPException은 그대로 전달
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"update_failed: {str(e)}"
        )
    


# 댓글 삭제
def delete_comment(post: Post, comment: Comment, db:Session, user_id: int):
    """댓글 삭제"""
    validate_comment_owner(comment, user_id)
    
    try:
        del_comment = comment_model.delete_comment(db, comment.id)
        db.commit()
        return {"message": "댓글이 성공적으로 삭제되었습니다"}
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터베이스 오류: {str(e)}"
        )
    