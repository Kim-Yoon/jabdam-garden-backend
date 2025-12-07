from pydantic_settings import BaseSettings

from pathlib import Path

class Settings(BaseSettings):

    # 이미지 업로드 설정
    UPLOAD_DIR: Path = Path("uploads/posts")
    PROFILE_UPLOAD_DIR: Path = Path("uploads/profiles")
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_IMAGE_WIDTH: int = 4096
    MAX_IMAGE_HEIGHT: int = 4096

    # 허용된 이미지 형식
    ALLOWED_IMAGE_FORMATS: set = {'JPEG', 'PNG', 'GIF', 'WEBP'}
    ALLOWED_IMAGE_EXTENSIONS: set = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    ALLOWED_MIME_TYPES: set = {
        'image/jpeg',
        'image/jpg', 
        'image/png',
        'image/gif',
        'image/webp'
    }
    
    DATABASE_URL: str
    SECRET_KEY: str
    DEBUG: bool = False
    GEMINI_API_KEY: str
    
    class Config:
        env_file = ".env"  # 루트의 .env 파일을 찾음

settings = Settings()

settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.PROFILE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)