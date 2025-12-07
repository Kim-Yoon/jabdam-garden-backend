# tests/conftest.py
"""테스트 설정 및 공통 fixtures."""
import sys
from pathlib import Path

# backend 디렉토리를 Python 경로에 추가
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db


# 테스트용 인메모리 SQLite DB
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """테스트용 DB 세션."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """각 테스트마다 새로운 DB 세션 제공."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """테스트용 API 클라이언트."""
    app.dependency_overrides[get_db] = override_get_db
    
    # 테스트 전 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as test_client:
        yield test_client
    
    # 테스트 후 정리
    Base.metadata.drop_all(bind=engine)
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


@pytest.fixture
def authenticated_client(client, test_user_data):
    """로그인된 상태의 테스트 클라이언트."""
    # 1. 회원가입
    client.post("/users", data=test_user_data)
    
    # 2. 로그인
    login_response = client.post("/users/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    
    # 쿠키가 자동으로 설정됨
    return client
