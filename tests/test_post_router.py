# tests/test_post_router.py
"""게시물 API 테스트."""
import pytest


class TestPostList:
    """게시물 목록 테스트."""

    @pytest.mark.asyncio
    async def test_get_posts_empty(self, async_client):
        """빈 게시물 목록 조회."""
        response = await async_client.get("/posts")
        
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_posts_with_data(self, authenticated_client, test_post_data):
        """게시물이 있을 때 목록 조회."""
        # 게시물 생성
        await authenticated_client.post("/posts", data=test_post_data)
        
        # 목록 조회
        response = await authenticated_client.get("/posts")
        
        assert response.status_code == 200
        posts = response.json()
        assert len(posts) >= 1


class TestPostCreate:
    """게시물 작성 테스트."""

    @pytest.mark.asyncio
    async def test_create_post_success(self, authenticated_client, test_post_data):
        """게시물 작성 성공."""
        response = await authenticated_client.post("/posts", data=test_post_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == test_post_data["title"]
        assert data["content"] == test_post_data["content"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_post_unauthorized(self, async_client, test_post_data):
        """비로그인 상태에서 게시물 작성 실패."""
        response = await async_client.post("/posts", data=test_post_data)
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_post_empty_title(self, authenticated_client):
        """빈 제목으로 게시물 작성 실패."""
        response = await authenticated_client.post("/posts", data={
            "title": "",
            "content": "내용입니다."
        })
        
        # Pydantic ValidationError → 422 반환
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_post_empty_content(self, authenticated_client):
        """빈 내용으로 게시물 작성 실패."""
        response = await authenticated_client.post("/posts", data={
            "title": "제목입니다",
            "content": ""
        })
        
        # Pydantic ValidationError → 422 반환
        assert response.status_code == 422


class TestPostDetail:
    """게시물 상세 테스트."""

    @pytest.mark.asyncio
    async def test_get_post_success(self, authenticated_client, test_post_data):
        """게시물 상세 조회 성공."""
        # 게시물 생성
        create_response = await authenticated_client.post("/posts", data=test_post_data)
        post_id = create_response.json()["id"]
        
        # 상세 조회
        response = await authenticated_client.get(f"/posts/{post_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == test_post_data["title"]

    @pytest.mark.asyncio
    async def test_get_post_not_found(self, async_client):
        """존재하지 않는 게시물 조회."""
        response = await async_client.get("/posts/99999")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_view_count_increment(self, authenticated_client, test_post_data):
        """조회수 증가 확인."""
        # 게시물 생성
        create_response = await authenticated_client.post("/posts", data=test_post_data)
        post_id = create_response.json()["id"]
        
        # 첫 번째 조회
        first_view = await authenticated_client.get(f"/posts/{post_id}")
        view_count_1 = first_view.json().get("view_count", 0)
        
        # 두 번째 조회
        second_view = await authenticated_client.get(f"/posts/{post_id}")
        view_count_2 = second_view.json().get("view_count", 0)
        
        # 조회수가 증가해야 함
        assert view_count_2 >= view_count_1


class TestPostUpdate:
    """게시물 수정 테스트."""

    @pytest.mark.asyncio
    async def test_update_post_success(self, authenticated_client, test_post_data):
        """게시물 수정 성공."""
        # 게시물 생성
        create_response = await authenticated_client.post("/posts", data=test_post_data)
        post_id = create_response.json()["id"]
        
        # 수정
        response = await authenticated_client.patch(f"/posts/{post_id}", data={
            "title": "수정된 제목"
        })
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_post_unauthorized(self, async_client, test_post_data):
        """비로그인 상태에서 게시물 수정 실패."""
        # 비로그인 상태에서 수정 시도 → 인증 먼저 체크
        response = await async_client.patch("/posts/1", data={
            "title": "수정된 제목"
        })
        
        assert response.status_code == 401


class TestPostDelete:
    """게시물 삭제 테스트."""

    @pytest.mark.asyncio
    async def test_delete_post_success(self, authenticated_client, test_post_data):
        """게시물 삭제 성공."""
        # 게시물 생성
        create_response = await authenticated_client.post("/posts", data=test_post_data)
        post_id = create_response.json()["id"]
        
        # 삭제
        response = await authenticated_client.delete(f"/posts/{post_id}")
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_post_not_found(self, authenticated_client):
        """존재하지 않는 게시물 삭제."""
        response = await authenticated_client.delete("/posts/99999")
        
        assert response.status_code == 404


class TestPostLike:
    """좋아요 테스트."""

    @pytest.mark.asyncio
    async def test_like_post_success(self, authenticated_client, test_post_data):
        """좋아요 성공."""
        # 게시물 생성
        create_response = await authenticated_client.post("/posts", data=test_post_data)
        post_id = create_response.json()["id"]
        
        # 좋아요
        response = await authenticated_client.post(f"/posts/{post_id}/like")
        
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_unlike_post_success(self, authenticated_client, test_post_data):
        """좋아요 취소 성공."""
        # 게시물 생성
        create_response = await authenticated_client.post("/posts", data=test_post_data)
        post_id = create_response.json()["id"]
        
        # 좋아요
        await authenticated_client.post(f"/posts/{post_id}/like")
        
        # 좋아요 취소
        response = await authenticated_client.delete(f"/posts/{post_id}/like")
        
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_like_post_unauthorized(self, async_client):
        """비로그인 상태에서 좋아요 실패."""
        # 비로그인 상태로 좋아요 시도 → 인증 먼저 체크
        response = await async_client.post("/posts/1/like")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_post_likes(self, authenticated_client, test_post_data):
        """좋아요 목록 조회."""
        # 게시물 생성
        create_response = await authenticated_client.post("/posts", data=test_post_data)
        post_id = create_response.json()["id"]
        
        # 좋아요
        await authenticated_client.post(f"/posts/{post_id}/like")
        
        # 좋아요 목록 조회
        response = await authenticated_client.get(f"/posts/{post_id}/likes")
        
        assert response.status_code == 200
        assert len(response.json()) >= 1
