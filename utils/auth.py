"""인증/인가 관련 유틸리티 (JWT, 비밀번호 해시 등)."""
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status, Cookie
from jose import JWTError, jwt

from config import settings

ALGORITHM = "HS256"
SECRET_KEY = settings.SECRET_KEY

def get_current_user_id(access_token: str = Cookie(None)) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if access_token is None:
        raise credentials_exception

    try:
        # 토큰 디코딩
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # user_id 추출
        user_id: str = payload.get("sub")
        if user_id is None:
            # logger.warning("토큰에 user_id가 없음")
            raise credentials_exception     
        return int(user_id)
        
    except JWTError as e:
        # logger.warning(f"JWT 검증 실패: {str(e)}")
        raise credentials_exception


def hash_password(pwd: str, rounds:int = 10) -> str:
    salt = bcrypt.gensalt(rounds=rounds)
    hashed_password = bcrypt.hashpw(pwd.encode("utf-8"), salt).decode("utf-8")
    return hashed_password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def create_access_token(data: dict, expires_delta: timedelta = None):
    """JWT 토큰 생성"""
    to_encode = data.copy()   
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt