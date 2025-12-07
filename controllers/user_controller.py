"""사용자 관련 비즈니스 로직."""
import logging
from datetime import datetime, timedelta

from fastapi import HTTPException, status, Response
from sqlalchemy.orm import Session

from models import user_model
from typing import Optional
from schemas.user_schema import (
    PasswordUpdate,
    UserAuthResponse,
    UserCreateRequest,
    UserLogin,
    UserResponse,
)
from utils.auth import create_access_token, hash_password, verify_password


logger = logging.getLogger(__name__)

# 사용자 목록 조회
def get_users(db: Session):
    users = user_model.get_users(db)
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return [UserResponse.model_validate(u) for u in users]

# 특정 사용자 조회
def get_user(user_id: int, db: Session):
    user = user_model.get_user_by_id(db, user_id)  
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            profile_image=user.img,
        )

# 이메일 중복 확인
def check_email_exists(email: str, db: Session):
    existing_user = user_model.get_user_by_email(db, email)
    return {"exists": existing_user is not None}

# 이름 중복 확인
def check_name_exists(name: str, db: Session):
    existing_user = user_model.get_user_by_name(db, name)
    return {"exists": existing_user is not None}

# 사용자 생성 - 회원가입
def create_user(user_data: UserCreateRequest, db: Session, img_path: Optional[str] = None):
    salt_rounds = 10

    try: 
        # 이메일 중복 확인
        existing_user = user_model.get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 존재하는 이메일입니다"
                )
    
        # 비밀번호 암호화
        hashed_pwd = hash_password(user_data.password, salt_rounds)
    
        # DB에 저장 (아직 commit 안 함)
        new_user = user_model.create_user(db, user_data, hashed_pwd, img_path)

        # 모든 작업이 성공하면 commit
        db.commit()
        db.refresh(new_user)
        
        return UserAuthResponse(
            id=new_user.id,
            email=new_user.email,
            name=new_user.name,
            profile_image=new_user.img,
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        logger.exception("Unexpected error during user creation")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="user_creation_failed")

def login(user_input: UserLogin, response: Response, db: Session):
    try:
        user = user_model.get_user_by_email(db, user_input.email)
        #이메일로 사용자 검색
        if not user:
            # logger.warning(f"로그인 실패: 존재하지 않는 이메일 - {user_input.email}")
            # 보안: 이메일/비밀번호 둘 다 같은 메시지
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다",
                headers={"WWW-Authenticate": "Bearer"}
            )
        if user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="탈퇴한 계정입니다"
            )
    
        # 3. 비밀번호 검증
        if not verify_password(user_input.password, user.password):
            # logger.warning(f"로그인 실패: 잘못된 비밀번호 - {user_input.email}")
            # 보안: 같은 메시지 사용
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
        # 4. JWT 토큰 생성
        access_token = create_access_token(
            data={"sub": str(user.id),
                  "email" : user.email,
                  "name" : user.name
                 }, 
            expires_delta=timedelta(minutes=15)
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,       # JavaScript 접근 차단
            secure=False,        # 개발 환경: False, 프로덕션: True (HTTPS)
            samesite="lax",      # CSRF 방어
            max_age=900          # 15분 (초 단위)
        )
        # # 5. 로그인 성공 로그
        #     logger.info(f"로그인 성공: {user.email}")
    
        #로그인 성공 시
        return UserAuthResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                profile_image=user.img
               )

    except HTTPException:
            # HTTPException은 그대로 전달
            raise
    except Exception as e:
        # 예상치 못한 에러 처리
        logger.exception("Unexpected error during login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다"
        )

def logout(user_id: int):
    user = user_model.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="no_user_found")

# 회원정보 수정
def update_my_info(name: Optional[str], img_path: Optional[str], user_id: int, db: Session):
    # 사용자 존재 확인
    user = user_model.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    updates = {}
    old_img_path = user.img  # 기존 이미지 경로 저장
    
    if name:
        existing_user = user_model.get_user_by_name(db, name.strip())
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="중복되는 닉네임입니다"
                )             
        updates["name"] = name.strip()

    if img_path:
        updates["img"] = img_path

    updated_user = user_model.update_user(db, user_id, updates)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="update_failed"
        )

    try:
        db.commit()
        db.refresh(updated_user)
        
        # 새 이미지가 저장되었으면 기존 이미지 삭제
        if img_path and old_img_path:
            from utils.img_validators import delete_profile_image
            delete_profile_image(old_img_path)
        
        # 수정된 유저 정보 반환
        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            name=updated_user.name,
            profile_image=updated_user.img
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"update_failed: {str(e)}"
        )

# 회원 비밀번호 수정
def change_pwd(data: PasswordUpdate, user_id: int, db: Session):
    user = user_model.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 3. 비밀번호 검증
    if not verify_password(data.current_pwd, user.password):
        # logger.warning(f"로그인 실패: 잘못된 비밀번호 - {user_input.email}")
        # 보안: 같은 메시지 사용
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="현재 비밀번호가 일치하지 않습니다"
        )

    updates={}

    # 비밀번호 암호화
    hashed_password = hash_password(data.password)
    updates = {
        "password": hashed_password,
        "updated_at": datetime.now()
    }
    try:
        updated_user = user_model.update_user(db, user_id, updates)
    
        db.commit()
        db.refresh(updated_user)
        return {"message": "비밀번호가 성공적으로 수정되었습니다"}
    except HTTPException:
        db.rollback()
        # 6. HTTPException은 그대로 전달
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"update_failed: {str(e)}"
        )

# 회원정보 탈퇴
def delete_user(user_id: int, db: Session):
    # 사용자 존재 확인
    user = user_model.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 이미 삭제된 사용자인지 확인
    if user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 삭제된 계정입니다"
        )
    
    try:
        del_user = user_model.delete_user(db, user_id)
        db.commit()
        return {"message": "계정이 성공적으로 삭제되었습니다"}
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터베이스 오류: {str(e)}"
        )
        
    