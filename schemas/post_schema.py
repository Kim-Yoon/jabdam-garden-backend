from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class PostBase(BaseModel):
    title: str = Field(..., max_length=26, description="게시글 제목 (최대 26자)")
    content: str = Field(..., min_length=1, description="게시글 본문")
    img: Optional[str] = Field(None, max_length=500, description="이미지 경로/URL")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('제목은 공백일 수 없습니다')
        if len(v) > 26:
            raise ValueError('제목은 26자를 초과할 수 없습니다')
        return v.strip()
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('본문은 공백일 수 없습니다')
        return v.strip()

# 게시글 생성 요청
class PostCreate(PostBase):
    pass  # user_id는 JWT 토큰에서 가져오므로 요청 본문에 포함 안 함

# 게시글 수정 요청
class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=26)
    content: Optional[str] = Field(None, min_length=1)
    img: Optional[str] = Field(None, max_length=500)
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError('제목은 공백일 수 없습니다')
            if len(v) > 26:
                raise ValueError('제목은 26자를 초과할 수 없습니다')
            return v.strip()
        return v
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError('본문은 공백일 수 없습니다')
            return v.strip()
        return v

# 게시글 응답
class PostResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    img: Optional[str] = None
    view_count: int = 0
    comment_count: int = 0
    user_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def model_validate(cls, post):
        # 삭제되지 않은 댓글만 카운트
        comment_count = 0
        if hasattr(post, 'comments') and post.comments:
            comment_count = sum(1 for c in post.comments if not c.is_deleted)
        
        return cls(
            id=post.id,
            user_id=post.user_id,
            title=post.title,
            content=post.content,
            img=post.img,
            view_count=post.view_count,
            comment_count=comment_count,
            user_name=post.user.name if post.user else None,
            created_at=post.created_at,
            updated_at=post.updated_at
        )