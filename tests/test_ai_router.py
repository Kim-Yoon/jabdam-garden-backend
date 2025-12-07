# tests/test_ai_router.py
"""AI API 테스트."""
import pytest
from unittest.mock import patch, AsyncMock


class TestAiGardener:
    """AI 정원사 테스트."""

    @patch('controllers.genai_controller.generate_gardener_comment')
    def test_gardener_comment_success(self, mock_generate, authenticated_client, test_post_data):
        """AI 정원사 의견 생성 성공."""
        # Mock AI 응답
        mock_generate.return_value = {
            "success": True,
            "comment": "좋은 아이디어네요! 🌱",
            "type": "gardener"
        }
        
        # 게시물 생성
        create_response = authenticated_client.post("/posts", data=test_post_data)
        post_id = create_response.json()["id"]
        
        # AI 정원사 호출
        response = authenticated_client.post("/ai-posts/gardener-comment", json={
            "post_id": post_id,
            "post_title": test_post_data["title"],
            "post_content": test_post_data["content"],
            "existing_comments": []
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "comment" in data

    def test_gardener_comment_unauthorized(self, client):
        """비로그인 상태에서 AI 정원사 호출 실패."""
        response = client.post("/ai-posts/gardener-comment", json={
            "post_id": 1,
            "post_title": "테스트",
            "post_content": "내용",
            "existing_comments": []
        })
        
        assert response.status_code == 401

    def test_gardener_comment_missing_title(self, authenticated_client):
        """제목 없이 AI 정원사 호출 실패."""
        response = authenticated_client.post("/ai-posts/gardener-comment", json={
            "post_id": 1,
            "post_title": "",
            "post_content": "내용",
            "existing_comments": []
        })
        
        assert response.status_code == 400

    def test_gardener_comment_missing_content(self, authenticated_client):
        """내용 없이 AI 정원사 호출 실패."""
        response = authenticated_client.post("/ai-posts/gardener-comment", json={
            "post_id": 1,
            "post_title": "제목",
            "post_content": "",
            "existing_comments": []
        })
        
        assert response.status_code == 400


class TestAiGardenerLimit:
    """AI 정원사 호출 횟수 제한 테스트."""

    @patch('controllers.genai_controller.generate_gardener_comment')
    def test_gardener_limit_exceeded(self, mock_generate, authenticated_client, test_post_data):
        """AI 정원사 3회 초과 시 429 에러."""
        mock_generate.return_value = {
            "success": True,
            "comment": "테스트 의견 🌱",
            "type": "gardener"
        }
        
        # 게시물 생성
        create_response = authenticated_client.post("/posts", data=test_post_data)
        post_id = create_response.json()["id"]
        
        request_data = {
            "post_id": post_id,
            "post_title": test_post_data["title"],
            "post_content": test_post_data["content"],
            "existing_comments": []
        }
        
        # AI 정원사를 3번 호출한 것처럼 댓글 생성
        # (실제 로직에서는 🤖로 시작하는 댓글 개수를 센다)
        for i in range(3):
            # 🤖로 시작하는 댓글 직접 생성
            authenticated_client.post(f"/posts/{post_id}/comments", json={
                "content": f"🤖 AI 테스트 댓글 {i+1}"
            })
        
        # 4번째 호출 시 429 에러
        response = authenticated_client.post("/ai-posts/gardener-comment", json=request_data)
        
        assert response.status_code == 429


class TestSummarize:
    """잡담 정리 테스트."""

    @patch('controllers.genai_controller.summarize_discussion')
    def test_summarize_success(self, mock_summarize, authenticated_client, test_post_data):
        """잡담 정리 성공."""
        # Mock AI 응답
        mock_summarize.return_value = {
            "success": True,
            "summary": {
                "key_ideas": ["핵심 아이디어 1"],
                "common_thoughts": ["공통된 생각 1"],
                "discussion_points": ["더 이야기해볼 점 1"]
            },
            "comment_count": 0
        }
        
        response = authenticated_client.post("/ai-posts/summarize", json={
            "post_title": test_post_data["title"],
            "post_content": test_post_data["content"],
            "comments": []
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "summary" in data
        assert "key_ideas" in data["summary"]

    def test_summarize_unauthorized(self, client):
        """비로그인 상태에서 잡담 정리 실패."""
        response = client.post("/ai-posts/summarize", json={
            "post_title": "테스트",
            "post_content": "내용",
            "comments": []
        })
        
        assert response.status_code == 401

    def test_summarize_missing_title(self, authenticated_client):
        """제목 없이 잡담 정리 실패."""
        response = authenticated_client.post("/ai-posts/summarize", json={
            "post_title": "",
            "post_content": "내용",
            "comments": []
        })
        
        assert response.status_code == 400

    @patch('controllers.genai_controller.summarize_discussion')
    def test_summarize_with_comments(self, mock_summarize, authenticated_client, test_post_data):
        """댓글이 있을 때 잡담 정리."""
        mock_summarize.return_value = {
            "success": True,
            "summary": {
                "key_ideas": ["핵심 1", "핵심 2"],
                "common_thoughts": ["공통점 1"],
                "discussion_points": ["논의점 1"]
            },
            "comment_count": 3
        }
        
        response = authenticated_client.post("/ai-posts/summarize", json={
            "post_title": test_post_data["title"],
            "post_content": test_post_data["content"],
            "comments": ["댓글 1", "댓글 2", "댓글 3"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["comment_count"] == 3
