from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # 연결 상태 체크
    echo=settings.DEBUG,     # 개발 중 SQL 쿼리 로깅
)

# 세션 로컬 생성
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base 클래스 (모든 모델이 상속받을 클래스)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """요청 생명주기 동안 사용할 DB 세션을 제공하는 의존성."""
    db = SessionLocal()
    try:
        yield db  
    finally:
        db.close()  # 사용 후 반드시 닫기