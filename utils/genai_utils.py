# utils/genai_utils.py
"""AI 관련 유틸리티 함수."""
from sqlalchemy.orm import Session
from models.comment_model import Comment

# AI 정원사 최대 호출 횟수
MAX_AI_GARDENER_COUNT = 3


def count_ai_comments(db: Session, post_id: int) -> int:
    """해당 게시물의 AI 정원사 댓글 개수를 센다 (🤖로 시작하는 댓글)"""
    ai_comments = db.query(Comment).filter(
        Comment.post_id == post_id,
        Comment.is_deleted == False,
        Comment.content.like('🤖%')  # 🤖로 시작하는 댓글
    ).count()
    return ai_comments
