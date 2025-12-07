from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from controllers import genai_controller
from schemas.genai_schema import GardenerCommentRequest, SummarizeRequest
from utils.genai_utils import count_ai_comments, MAX_AI_GARDENER_COUNT
from utils.auth import get_current_user_id

router = APIRouter(prefix="/ai-posts", tags=["ai-posts"])


# ============================================
# 🌱 AI 정원사 - 의견 생성
# ============================================
@router.post("/gardener-comment")
async def get_gardener_comment(
    request: GardenerCommentRequest,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user_id)
):
    """
    AI 정원사가 게시물에 대한 의견/질문을 생성합니다.
    - 게시물당 최대 3회까지만 호출 가능
    - 아이디어를 발전시키는 질문
    - 새로운 관점 제시
    """
    if not request.post_title or not request.post_content:
        raise HTTPException(400, "제목과 내용이 필요합니다")
    
    # 🔒 AI 정원사 호출 횟수 제한 체크
    current_ai_count = count_ai_comments(db, request.post_id)
    if current_ai_count >= MAX_AI_GARDENER_COUNT:
        raise HTTPException(
            status_code=429,  # Too Many Requests
            detail=f"이 씨앗에는 AI 정원사를 {MAX_AI_GARDENER_COUNT}번까지만 부를 수 있어요! 🌱"
        )
    
    return await genai_controller.generate_gardener_comment(
        post_title=request.post_title,
        post_content=request.post_content,
        existing_comments=request.existing_comments
    )


# ============================================
# 📝 잡담 정리 - 토론 요약
# ============================================
@router.post("/summarize")
async def get_discussion_summary(
    request: SummarizeRequest,
    current_user: int = Depends(get_current_user_id)
):
    """
    게시물과 댓글들을 분석해서 핵심 인사이트를 정리합니다.
    - 핵심 아이디어 추출
    - 공통된 의견 정리
    - 더 논의가 필요한 점 제시
    """
    if not request.post_title or not request.post_content:
        raise HTTPException(400, "제목과 내용이 필요합니다")
    
    return await genai_controller.summarize_discussion(
        post_title=request.post_title,
        post_content=request.post_content,
        comments=request.comments
    )
