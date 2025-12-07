# tests/test_user_router.py
"""사용자 API 테스트."""
import pytest


class TestUserRegistration:
    """회원가입 테스트."""

    def test_create_user_success(self, client, test_user_data):
        """회원가입 성공."""
        response = client.post("/users", data=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["name"] == test_user_data["name"]
        assert "id" in data

    def test_create_user_duplicate_email(self, client, test_user_data):
        """중복 이메일로 회원가입 실패."""
        # 첫 번째 가입
        client.post("/users", data=test_user_data)
        
        # 같은 이메일로 다시 가입 시도
        response = client.post("/users", data=test_user_data)
        
        # API가 409 Conflict 반환 (HTTP 표준에 맞음)
        assert response.status_code == 409

    def test_create_user_password_mismatch(self, client, test_user_data):
        """비밀번호 불일치로 회원가입 실패."""
        test_user_data["password_confirm"] = "DifferentPassword!"
        
        # Pydantic ValidationError가 발생 → 422 반환
        response = client.post("/users", data=test_user_data)
        
        assert response.status_code == 422

    def test_create_user_invalid_email(self, client, test_user_data):
        """잘못된 이메일 형식으로 회원가입 실패."""
        test_user_data["email"] = "invalid-email"
        
        response = client.post("/users", data=test_user_data)
        
        assert response.status_code == 422  # Validation Error


class TestUserLogin:
    """로그인 테스트."""

    def test_login_success(self, client, test_user_data):
        """로그인 성공."""
        # 먼저 회원가입
        client.post("/users", data=test_user_data)
        
        # 로그인
        response = client.post("/users/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        assert response.status_code == 200

    def test_login_wrong_password(self, client, test_user_data):
        """잘못된 비밀번호로 로그인 실패."""
        # 먼저 회원가입
        client.post("/users", data=test_user_data)
        
        # 잘못된 비밀번호로 로그인
        response = client.post("/users/login", json={
            "email": test_user_data["email"],
            "password": "WrongPassword!"
        })
        
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """존재하지 않는 사용자로 로그인 실패."""
        response = client.post("/users/login", json={
            "email": "nonexistent@example.com",
            "password": "SomePassword!"
        })
        
        assert response.status_code == 401


class TestCheckDuplicate:
    """중복 확인 테스트."""

    def test_check_email_available(self, client):
        """사용 가능한 이메일."""
        response = client.get("/users/check-email", params={"email": "new@example.com"})
        
        assert response.status_code == 200
        # API가 {"exists": False} 형태로 반환
        assert response.json()["exists"] == False

    def test_check_email_taken(self, client, test_user_data):
        """이미 사용 중인 이메일."""
        # 회원가입
        client.post("/users", data=test_user_data)
        
        # 중복 확인
        response = client.get("/users/check-email", params={"email": test_user_data["email"]})
        
        assert response.status_code == 200
        # API가 {"exists": True} 형태로 반환
        assert response.json()["exists"] == True

    def test_check_name_available(self, client):
        """사용 가능한 이름."""
        response = client.get("/users/check-name", params={"name": "새이름"})
        
        assert response.status_code == 200
        # API가 {"exists": False} 형태로 반환
        assert response.json()["exists"] == False


class TestUserProfile:
    """프로필 관련 테스트."""

    def test_get_my_info(self, authenticated_client):
        """내 정보 조회."""
        response = authenticated_client.get("/users/me")
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "name" in data

    def test_get_my_info_unauthorized(self, client):
        """비로그인 상태에서 내 정보 조회 실패."""
        response = client.get("/users/me")
        
        assert response.status_code == 401


class TestUserLogout:
    """로그아웃 테스트."""

    def test_logout_success(self, authenticated_client):
        """로그아웃 성공."""
        response = authenticated_client.post("/users/logout")
        
        assert response.status_code == 200
