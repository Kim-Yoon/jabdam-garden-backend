from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from config import settings

async_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# 비동기 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base 클래스 (모든 모델이 상속받을 클래스)
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """요청 생명주기 동안 사용할 DB 세션을 제공하는 의존성."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()