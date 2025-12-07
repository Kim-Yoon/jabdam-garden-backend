from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, description="게시글 본문")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('본문은 공백일 수 없습니다')
        return v.strip()

# 게시글 생성 요청
class CommentCreate(CommentBase):
    pass  

class CommentUpdate(BaseModel):
    """댓글 수정 요청"""
    content: Optional[str] = Field(None, min_length=1, max_length=1000)
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError('댓글 내용은 공백일 수 없습니다')
            return v.strip()
        return v

class CommentResponse(BaseModel):
    """댓글 응답"""
    id: int
    post_id: int
    user_id: int
    content: str
    user_name: Optional[str] = None  # 댓글 작성자 이름
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def model_validate(cls, comment):
        return cls(
            id=comment.id,
            post_id=comment.post_id,
            user_id=comment.user_id,
            content=comment.content,
            user_name=comment.user.name if comment.user else None,
            created_at=comment.created_at,
            updated_at=comment.updated_at
        )