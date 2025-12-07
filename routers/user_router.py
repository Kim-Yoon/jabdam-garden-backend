# router/user_router.py
"""사용자 관련 라우터 정의."""
from typing import Optional
from fastapi import APIRouter, Depends, status, Response, Form, File, UploadFile
from sqlalchemy.orm import Session

from controllers import user_controller
from database import get_db
from schemas.user_schema import PasswordUpdate, UserCreateRequest, UserLogin, UserUpdate
from utils.user_validators import get_active_user
from utils.img_validators import validate_uploaded_image, save_profile_image, delete_profile_image



router = APIRouter(prefix="/users")

## 전체 사용자 목록 조회
@router.get("")
def get_users(db: Session=Depends(get_db)):
    return user_controller.get_users(db)

# # 특정 사용자 조회 - 모든 유저에게 보여지는 공개 프로필
# @router.get("/{user_id}")
# def get_user(user_id: int):
#     return user_controller.get_user(user_id)

# 사용자 생성(201 Created) - 회원가입
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    email: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    profile_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # 이미지 처리
    img_path = None
    if profile_image:
        contents = await validate_uploaded_image(profile_image)
        img_path = await save_profile_image(contents, profile_image.filename)
    
    # 스키마로 데이터 검증
    user_data = UserCreateRequest(
        email=email,
        name=name,
        password=password,
        password_confirm=password_confirm
    )
    return user_controller.create_user(user_data, db, img_path)

# 이메일 중복 확인
@router.get("/check-email")
def check_email(email: str, db: Session = Depends(get_db)):
    return user_controller.check_email_exists(email, db)

# 이름 중복 확인
@router.get("/check-name")
def check_name(name: str, db: Session = Depends(get_db)):
    return user_controller.check_name_exists(name, db)

# 로그인
@router.post("/login")
def login(user_input: UserLogin, response: Response, db: Session = Depends(get_db)):
    return user_controller.login(user_input, response, db)

# 로그아웃
@router.post("/logout")
def logout(user_id: int = Depends(get_active_user)):
    # logger.info(f"로그아웃: {user_id}")
    return {"message": "로그아웃 되었습니다"}

# 회원정보 불러오기 
@router.get("/me")
def get_user_info(user_id: int = Depends(get_active_user), db: Session = Depends(get_db)):
    return user_controller.get_user(user_id, db)

# 회원정보 수정
@router.patch("/me")
async def update_my_info(
    name: Optional[str] = Form(None),
    profile_image: Optional[UploadFile] = File(None),
    user_id: int = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    # 이미지 처리
    img_path = None
    if profile_image:
        contents = await validate_uploaded_image(profile_image)
        img_path = await save_profile_image(contents, profile_image.filename)
    
    # 최소 하나의 필드는 수정되어야 함
    if name is None and img_path is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="최소 하나의 필드는 수정되어야 합니다")
    
    return user_controller.update_my_info(name, img_path, user_id, db)

# 비밀번호 수정
@router.patch("/me/password")
def change_pwd(data: PasswordUpdate, user_id = Depends(get_active_user), db: Session=Depends(get_db)):
    return user_controller.change_pwd(data, user_id, db)

# 회원탈퇴
@router.delete("/me")
def delete_user(user_id: int = Depends(get_active_user), db: Session=Depends(get_db)):
    return user_controller.delete_user(user_id, db)

