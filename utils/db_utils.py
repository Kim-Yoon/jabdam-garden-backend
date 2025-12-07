"""데이터베이스 유틸리티 함수들."""
from contextlib import contextmanager
from typing import Generator

from fastapi import HTTPException, status
from sqlalchemy.orm import Session


@contextmanager
def db_transaction(db: Session) -> Generator[None, None, None]:
    """
    데이터베이스 트랜잭션을 관리하는 컨텍스트 매니저.
    
    사용 예시:
        with db_transaction(db):
            # DB 작업 수행
            db.add(new_item)
            # commit은 자동으로 수행됨
    
    Args:
        db: SQLAlchemy 세션 객체
        
    Raises:
        HTTPException: 트랜잭션 실패 시
    """
    try:
        yield
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터베이스 오류: {str(e)}"
        )


def commit_and_refresh(db: Session, instance):
    """
    객체를 커밋하고 새로고침합니다.
    
    Args:
        db: SQLAlchemy 세션 객체
        instance: 새로고침할 모델 인스턴스
        
    Returns:
        새로고침된 인스턴스
        
    Raises:
        HTTPException: 커밋 실패 시
    """
    try:
        db.commit()
        db.refresh(instance)
        return instance
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터베이스 오류: {str(e)}"
        )
