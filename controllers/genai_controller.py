from fastapi import HTTPException
from google import genai
from typing import Optional
from PIL import Image
from pathlib import Path
import io

from config import settings
from utils.img_validators import save_image, delete_image


async def generate_draft(
    image_bytes: Optional[bytes],
    filename: Optional[str],
    text: Optional[str],
    style: str,
    img_info: Optional[dict]
) -> dict:

    image_url = None
    try:
        # 1. 이미지가 있으면 저장 (기존 함수 재사용)
        if image_bytes and filename:
            image_url = await save_image(image_bytes, filename)
            
            # PIL Image로 변환 (Gemini에 전달용)
            image = Image.open(io.BytesIO(image_bytes))
        else:
            image = None
        
        # 4. Gemini 클라이언트 초기화
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        # 5. 스타일별 프롬프트
        style_guides = {
            "casual": "친근하고 일상적인 블로그 글",
            "formal": "전문적이고 정중한 리뷰",
            "emotional": "감성적이고 따뜻한 일기",
            "funny": "유머러스하고 재치있는 글"
        }
        if image and text:
            # 이미지 + 텍스트
            prompt = f"""이 이미지와 다음 텍스트를 바탕으로 한국어 게시글을 작성해주세요.

            텍스트: {text}
            
            스타일: {style_guides.get(style, style_guides["casual"])}
            
            **출력 형식:**
            제목: [20자 이내, 이모지 포함]
            ---
            [본문 300자 이내]
            
            **필수:** 제목과 본문을 반드시 위 형식대로 구분해주세요."""
            contents = [prompt, image]
            
        elif image:
            # 이미지만
            prompt = f"""이 이미지를 보고 한국어로 커뮤니티 게시글을 작성해주세요.

            스타일: {style_guides.get(style, style_guides["casual"])}
            
            **출력 형식:**
            제목: [20자 이내, 이모지 포함]
            ---
            [본문 300자 이내]
            
            **필수:** 제목과 본문을 반드시 위 형식대로 구분해주세요."""
            contents = [prompt, image]
            
        else:
            # 텍스트만
            prompt = f"""다음 텍스트를 바탕으로 한국어 게시글을 작성해주세요.

            텍스트: {text}
            
            스타일: {style_guides.get(style, style_guides["casual"])}
            
            **출력 형식:**
            제목: [20자 이내, 이모지 포함]
            ---
            [본문 300자 이내]
            
            **필수:** 제목과 본문을 반드시 위 형식대로 구분해주세요."""
            contents = prompt
        
       

        # 5. AI 생성
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )
        
        # 파싱
        parsed = parse_generated_content(response.text)
        
        # 7. 성공 응답
        result = {
            "success": True,
            "draft": {
                "title": parsed["title"],
                "content": parsed["content"]
            },
            "style": style
        }
        
        # 이미지 URL 추가 (이미지가 있을 때만)
        if image_url:
            result["draft"]["image_url"] = image_url
            result["image_info"] = img_info
        
        return result
        
    except Exception as e:
        # AI 생성 실패 시 업로드된 파일 삭제 (기존 함수 재사용)
        if image_url:
            delete_image(image_url)
        raise HTTPException(500, f"AI 생성 오류: {str(e)}")


def parse_generated_content(text: str) -> dict:
    """AI 생성 텍스트에서 제목과 본문 분리"""
    lines = text.strip().split('\n')
    
    title = ""
    body_lines = []
    found_separator = False
    
    for line in lines:
        if line.startswith("제목:"):
            title = line.replace("제목:", "").strip()
        elif "---" in line:
            found_separator = True
        elif found_separator:
            body_lines.append(line)
    
    # 제목이 없으면 첫 줄을 제목으로
    if not title and body_lines:
        title = body_lines[0]
        body_lines = body_lines[1:]
    
    return {
        "title": title[:100] if title else "제목 없음",
        "content": '\n'.join(body_lines).strip() or text
    }


# prompt = f"""이 이미지를 보고 한국어로 커뮤니티 게시글을 작성해주세요.

#         스타일: {style_guides[style]}
        
#         **출력 형식:**
#         제목: [매력적인 제목 (20자 이내, 이모지 1개 포함)]
#         ---
#         [본문 내용 (300-500자)]
        
#         **작성 가이드:**
#         1. 이미지의 핵심 내용을 정확히 파악
#         2. {style_guides[style]} 톤 유지
#         3. 구체적인 디테일 포함
        
#         **필수:** 제목과 본문을 반드시 위 형식대로 구분해주세요."""