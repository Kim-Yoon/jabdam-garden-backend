from fastapi import HTTPException
from google import genai
from typing import Optional, List

from config import settings


# ============================================
# 🌱 AI 정원사 - 의견 생성
# ============================================
async def generate_gardener_comment(
    post_title: str,
    post_content: str,
    existing_comments: Optional[List[str]] = None
) -> dict:
    """
    AI 정원사가 게시물에 대한 의견/질문을 생성합니다.
    - 아이디어를 발전시키는 질문
    - 새로운 관점 제시
    - 격려와 호기심 표현
    """
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        # 기존 댓글이 있으면 컨텍스트에 포함
        comments_context = ""
        if existing_comments and len(existing_comments) > 0:
            comments_context = f"""
            
기존에 나온 의견들:
{chr(10).join(f'- {c}' for c in existing_comments[:5])}

위 의견들과 다른 새로운 관점에서 이야기해주세요."""

        prompt = f"""당신은 '잡담의 화원'이라는 아이디어 커뮤니티의 AI 정원사입니다.
사용자들이 자유롭게 던진 아이디어(씨앗)를 보고, 그 아이디어가 자랄 수 있도록 도와주세요.

**당신의 역할:**
- 아이디어에 대한 호기심과 흥미를 표현
- 아이디어를 발전시킬 수 있는 질문 던지기
- 새로운 관점이나 연결고리 제시
- 따뜻하고 격려하는 톤 유지

**게시물 제목:** {post_title}
**게시물 내용:** {post_content}
{comments_context}

**규칙:**
1. 150자 이내로 짧고 친근하게
2. 이모지 1-2개 자연스럽게 사용
3. 질문으로 끝나면 좋음 (대화 유도)
4. 비판보다는 가능성에 집중
5. "AI 정원사입니다" 같은 자기소개 하지 않기

의견을 작성해주세요:"""

        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        comment_text = response.text.strip()
        
        # 너무 길면 자르기
        if len(comment_text) > 200:
            comment_text = comment_text[:197] + "..."
        
        return {
            "success": True,
            "comment": comment_text,
            "type": "gardener"
        }
        
    except Exception as e:
        raise HTTPException(500, f"AI 정원사 오류: {str(e)}")


# ============================================
# 📝 잡담 정리 - 토론 요약
# ============================================
async def summarize_discussion(
    post_title: str,
    post_content: str,
    comments: Optional[List[str]] = None
) -> dict:
    """
    게시물과 댓글들을 분석해서 핵심 인사이트를 정리합니다.
    - 핵심 아이디어 추출
    - 공통된 의견 정리
    - 더 논의가 필요한 점 제시
    """
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        # 댓글 컨텍스트
        comments_text = ""
        if comments and len(comments) > 0:
            comments_text = f"""
**나온 의견들:**
{chr(10).join(f'{i+1}. {c}' for i, c in enumerate(comments[:15]))}
"""
        else:
            comments_text = "\n(아직 의견이 없습니다)"

        prompt = f"""당신은 '잡담의 화원' 커뮤니티에서 자유로운 잡담을 정리해주는 도우미입니다.
게시물과 댓글들을 분석해서 흩어진 아이디어들을 정리하고 핵심 인사이트를 도출해주세요.

**원본 씨앗(게시물):**
제목: {post_title}
내용: {post_content}
{comments_text}

**정리 규칙:**
1. 친근하고 따뜻한 톤 유지
2. 각 섹션은 2-3개 항목으로 간결하게
3. 이모지를 적절히 사용해서 읽기 쉽게
4. 비판보다는 가능성과 발전 방향에 집중
5. 의견이 없거나 적으면 원본 아이디어의 핵심만 정리

**출력 형식 (정확히 지켜주세요):**
💡 핵심 아이디어
- [핵심1]
- [핵심2]
---
🤝 공통된 생각
- [공통점1]
- [공통점2]
---
❓ 더 이야기해볼 점
- [질문1]
- [질문2]"""

        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        # 파싱
        summary = parse_summary(response.text)
        
        return {
            "success": True,
            "summary": summary,
            "comment_count": len(comments) if comments else 0
        }
        
    except Exception as e:
        raise HTTPException(500, f"잡담 정리 오류: {str(e)}")


def parse_summary(text: str) -> dict:
    """AI 응답에서 요약 정보 파싱"""
    result = {
        "key_ideas": [],
        "common_thoughts": [],
        "discussion_points": []
    }
    
    sections = text.strip().split('---')
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        lines = section.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if '핵심 아이디어' in line or '💡' in line:
                current_section = 'key_ideas'
            elif '공통된' in line or '🤝' in line:
                current_section = 'common_thoughts'
            elif '이야기해볼' in line or '❓' in line:
                current_section = 'discussion_points'
            elif line.startswith('-') and current_section:
                item = line[1:].strip()
                if item:
                    result[current_section].append(item)
    
    # 빈 섹션 기본값
    if not result["key_ideas"]:
        result["key_ideas"] = ["원본 아이디어의 핵심을 다시 살펴보세요"]
    if not result["common_thoughts"]:
        result["common_thoughts"] = ["아직 더 많은 의견이 필요해요"]
    if not result["discussion_points"]:
        result["discussion_points"] = ["이 아이디어를 어떻게 발전시킬 수 있을까요?"]
    
    return result
