# schemas/genai_schema.py
"""AI 관련 요청/응답 스키마."""
from pydantic import BaseModel
from typing import Optional, List


class GardenerCommentRequest(BaseModel):
    """AI 정원사 의견 생성 요청"""
    post_id: int  # 게시물 ID (횟수 제한 체크용)
    post_title: str
    post_content: str
    existing_comments: Optional[List[str]] = None


class SummarizeRequest(BaseModel):
    """잡담 정리 요청"""
    post_title: str
    post_content: str
    comments: Optional[List[str]] = None
