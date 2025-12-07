from fastapi import APIRouter, UploadFile, File, HTTPException, Form

from config import settings
from typing import Optional
from pathlib import Path

from controllers.genai_controller import generate_draft
from utils.img_validators import validate_uploaded_image, get_image_info

router = APIRouter(prefix="/ai-posts", tags=["ai-posts"])

@router.post("/generate-draft")
async def generate_post_draft(
    file: Optional[UploadFile] = File(None),  # ✅ Optional로 변경
    text: Optional[str] = Form(None),  # 텍스트만으로도 생성 가능하게
    style: str = Form("casual")
):
    # 1. 입력 검증
    if not file and not text:
        raise HTTPException(
            400, 
            "이미지 또는 텍스트 중 하나는 필수입니다"
        )
    try:
        image_bytes = None
        img_info = None
        filename = None
        
        # 2. 이미지가 있으면 검증
        if file:
            image_bytes = await validate_uploaded_image(file)
            img_info = get_image_info(image_bytes)
            filename = file.filename
            print(f"✅ 이미지 검증 성공: {img_info}")
        
        # ✅ controller에 필요한 모든 데이터 전달
        return await generate_draft(
            image_bytes=image_bytes,
            filename=filename,
            text=text,
            style=style,
            img_info=img_info
        )
        
    except HTTPException as e:
        # 검증 실패 시 에러 그대로 전달
        raise e