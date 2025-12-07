# utils/img_validator.py
from fastapi import UploadFile, HTTPException, status
from PIL import Image
from pathlib import Path
import io
import uuid
from config import settings

class ImageValidationError(Exception):
    """이미지 검증 실패 시 발생하는 예외"""
    pass

async def validate_uploaded_image(file: UploadFile) -> bytes:
    """
    업로드된 이미지 파일을 검증하고 바이트 데이터 반환
    
    Args:
        file: FastAPI UploadFile 객체
        
    Returns:
        bytes: 검증된 이미지 파일의 바이트 데이터
              (file.read()가 자동으로 bytes 반환)
        
    Raises:
        HTTPException: 검증 실패 시
    """
    # 1단계: MIME 타입 검증 (빠른 필터)
    validate_mime_type(file.content_type)
    
    # 2단계: 파일 확장자 검증
    validate_file_extension(file.filename)
    
    # 3단계: 파일 읽기
    contents = await file.read()
    
    # 4단계: 파일 크기 검증
    validate_file_size(contents)
    
    # 5단계: 실제 이미지 내용 검증 (가장 중요!)
    validate_image_content(contents)

    return contents

def validate_mime_type(content_type: str) -> None:
    """
    MIME 타입 검증
    
    Args:
        content_type: 파일의 MIME 타입
        
    Raises:
        HTTPException: MIME 타입이 허용되지 않는 경우
    """
    if content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. "
                   f"허용 형식: {', '.join(settings.ALLOWED_MIME_TYPES)}"
        )

def validate_file_extension(filename: str) -> None:
    """
    파일 확장자 검증
    
    Args:
        filename: 파일명
        
    Raises:
        HTTPException: 확장자가 허용되지 않는 경우
    """
    file_ext = Path(filename).suffix.lower()
    
    if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 확장자입니다: {file_ext}. "
                   f"허용 확장자: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}"
        )

def validate_file_size(contents: bytes) -> None:
    """
    파일 크기 검증
    
    Args:
        contents: 파일 바이트 데이터
        
    Raises:
        HTTPException: 파일 크기가 제한을 초과하는 경우
    """
    file_size = len(contents)
    max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
    
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"파일 크기가 너무 큽니다. "
                   f"현재: {file_size / (1024 * 1024):.2f}MB, "
                   f"최대: {max_size_mb:.0f}MB"
        )


def validate_image_content(contents: bytes) -> Image.Image:
    """
    실제 이미지 내용 검증 (PIL 사용)
    
    Args:
        contents: 이미지 파일 바이트 데이터
        
    Returns:
        Image.Image: PIL Image 객체
        
    Raises:
        HTTPException: 이미지가 손상되었거나 유효하지 않은 경우
    """
    try:
        # 이미지 열기
        image = Image.open(io.BytesIO(contents))
        
        # 이미지 검증 (손상 여부 확인)
        image.verify()
        
        # verify() 후에는 다시 열어야 함
        image = Image.open(io.BytesIO(contents))
        
        # 형식 검증
        if image.format not in settings.ALLOWED_IMAGE_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 이미지 형식: {image.format}. "
                       f"허용 형식: {', '.join(settings.ALLOWED_IMAGE_FORMATS)}"
            )
        
        # 해상도 검증
        validate_image_dimensions(image)
        
        return image
        
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"유효하지 않은 이미지 파일입니다: {str(e)}"
        )


def validate_image_dimensions(image: Image.Image) -> None:
    """
    이미지 해상도 검증
    
    Args:
        image: PIL Image 객체
        
    Raises:
        HTTPException: 해상도가 제한을 초과하는 경우
    """
    width, height = image.size
    
    if width > settings.MAX_IMAGE_WIDTH or height > settings.MAX_IMAGE_HEIGHT:
        raise HTTPException(
            status_code=400,
            detail=f"이미지 해상도가 너무 큽니다. "
                   f"현재: {width}x{height}, "
                   f"최대: {settings.MAX_IMAGE_WIDTH}x{settings.MAX_IMAGE_HEIGHT}"
        )


def get_image_info(contents: bytes) -> dict:
    """
    이미지 정보 추출 (디버깅/로깅용)
    
    Args:
        contents: 이미지 파일 바이트 데이터
        
    Returns:
        dict: 이미지 정보 (형식, 크기, 해상도 등)
    """
    try:
        image = Image.open(io.BytesIO(contents))
        
        return {
            "format": image.format,
            "mode": image.mode,
            "size": image.size,
            "width": image.width,
            "height": image.height,
            "file_size_bytes": len(contents),
            "file_size_mb": round(len(contents) / (1024 * 1024), 2)
        }
    except Exception as e:
        return {"error": str(e)}


async def save_image(contents: bytes, original_filename: str) -> str:
    """
    검증된 이미지를 로컬에 저장하고 경로 반환
    
    Args:
        contents: 검증된 이미지 바이트 데이터
        original_filename: 원본 파일명
        
    Returns:
        str: 저장된 이미지의 URL 경로 (예: /uploads/posts/uuid.jpg)
    """
    # 고유한 파일명 생성 (UUID + 원본 확장자)
    file_ext = Path(original_filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # 저장 경로
    save_path = settings.UPLOAD_DIR / unique_filename
    
    # 파일 저장
    with open(save_path, "wb") as f:
        f.write(contents)
    
    # URL 경로 반환 (프론트엔드에서 접근할 경로)
    return f"/uploads/posts/{unique_filename}"


async def save_profile_image(contents: bytes, original_filename: str) -> str:
    """
    검증된 프로필 이미지를 로컬에 저장하고 경로 반환
    
    Args:
        contents: 검증된 이미지 바이트 데이터
        original_filename: 원본 파일명
        
    Returns:
        str: 저장된 이미지의 URL 경로 (예: /uploads/profiles/uuid.jpg)
    """
    # 고유한 파일명 생성 (UUID + 원본 확장자)
    file_ext = Path(original_filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # 저장 경로
    save_path = settings.PROFILE_UPLOAD_DIR / unique_filename
    
    # 파일 저장
    with open(save_path, "wb") as f:
        f.write(contents)
    
    # URL 경로 반환 (프론트엔드에서 접근할 경로)
    return f"/uploads/profiles/{unique_filename}"


def delete_profile_image(img_path: str) -> bool:
    """
    프로필 이미지 파일 삭제
    
    Args:
        img_path: 이미지 URL 경로 (예: /uploads/profiles/uuid.jpg)
        
    Returns:
        bool: 삭제 성공 여부
    """
    if not img_path:
        return False
    
    # URL 경로에서 실제 파일 경로 추출
    filename = Path(img_path).name
    file_path = settings.PROFILE_UPLOAD_DIR / filename
    
    try:
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except Exception:
        return False


def delete_image(img_path: str) -> bool:
    """
    이미지 파일 삭제
    
    Args:
        img_path: 이미지 URL 경로 (예: /uploads/posts/uuid.jpg)
        
    Returns:
        bool: 삭제 성공 여부
    """
    if not img_path:
        return False
    
    # URL 경로에서 실제 파일 경로 추출
    filename = Path(img_path).name
    file_path = settings.UPLOAD_DIR / filename
    
    try:
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except Exception:
        return False
