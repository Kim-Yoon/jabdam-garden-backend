# tests/conftest.py
"""테스트 설정 및 공통 fixtures."""
import sys
from pathlib import Path

# backend 디렉토리를 Python 경로에 추가
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db


# 테스트용 인메모리 SQLite DB (비동기)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

async_engine = create_async_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestingAsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db():
    """테스트용 DB 세션."""
    async with TestingAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """각 테스트마다 새로운 DB 세션 제공."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def async_client():
    """테스트용 비동기 API 클라이언트."""
    app.dependency_overrides[get_db] = override_get_db
    
    # 테스트 전 테이블 생성
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    
    # 테스트 후 정리
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """테스트용 사용자 데이터."""
    return {
        "email": "test@example.com",
        "name": "테스트유저",
        "password": "Test1234!",
        "password_confirm": "Test1234!"
    }


@pytest.fixture
def test_post_data():
    """테스트용 게시물 데이터."""
    return {
        "title": "테스트 씨앗",
        "content": "이것은 테스트 게시물입니다."
    }


@pytest_asyncio.fixture
async def authenticated_client(async_client, test_user_data):
    """로그인된 상태의 테스트 클라이언트."""
    # 1. 회원가입
    await async_client.post("/users", data=test_user_data)
    
    # 2. 로그인
    login_response = await async_client.post("/users/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    
    # 쿠키가 자동으로 설정됨
    return async_client
