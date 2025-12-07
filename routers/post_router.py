from fastapi import APIRouter, Depends, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models.post_model import Post
from schemas.post_schema import PostCreate, PostUpdate
from utils.post_validators import get_valid_post
from utils.user_validators import get_active_user
from utils.img_validators import validate_uploaded_image, save_image
from controllers import post_controller


router = APIRouter(prefix="/posts")

## 전체 게시글 목록 조회
@router.get("")
def get_posts(db: Session=Depends(get_db)):
    return post_controller.get_posts(db)

# 특정 게시물 조회
@router.get("/{post_id}")
def get_post(
    post: Post = Depends(get_valid_post),
    db: Session=Depends(get_db),
    increment_view: bool = True  # 조회수 증가 여부 (수정 페이지에서는 False)
):
    return post_controller.get_post(post, db, increment_view)

# 게시글 생성(201 Created)
@router.post("", status_code=201)
async def upload_post(
    title: str = Form(...),
    content: str = Form(...),
    img: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db), 
    user_id: int = Depends(get_active_user)
):
    # 이미지 처리
    img_path = None
    if img:
        # 이미지 검증
        contents = await validate_uploaded_image(img)
        # 이미지 저장 후 경로 반환
        img_path = await save_image(contents, img.filename)
    
    # 스키마로 데이터 검증
    data = PostCreate(title=title, content=content, img=img_path)
    return post_controller.create_post(data, db, user_id)

# 게시글 수정
@router.patch("/{post_id}")
async def update_post(
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    img: Optional[UploadFile] = File(None),
    post: Post = Depends(get_valid_post),
    db: Session = Depends(get_db), 
    user_id: int = Depends(get_active_user)
):
    # 업데이트할 필드만 동적으로 구성 (exclude_unset이 제대로 작동하도록)
    update_fields = {}
    if title is not None:
        update_fields['title'] = title
    if content is not None:
        update_fields['content'] = content
    
    # 새 이미지가 업로드된 경우에만 img 필드 포함
    if img:
        contents = await validate_uploaded_image(img)
        img_path = await save_image(contents, img.filename)
        update_fields['img'] = img_path
    
    # 스키마로 데이터 검증
    data = PostUpdate(**update_fields)
    return post_controller.update_post(post, data, db, user_id)


# 게시글 삭제
@router.delete("/{post_id}")
def delete_post(
    post: Post = Depends(get_valid_post),
    db: Session=Depends(get_db),
    user_id: int = Depends(get_active_user)
):
    return post_controller.delete_post(post, db, user_id)

##좋아요 관련 router
@router.post("/{post_id}/like", status_code=status.HTTP_201_CREATED)
async def like_post(
    post: Post = Depends(get_valid_post),
    user_id: int = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    return post_controller.like_post(post, user_id, db)

@router.delete("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_post(
    post: Post = Depends(get_valid_post),
    user_id: int = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    return post_controller.unlike_post(post, user_id, db)

@router.get("/{post_id}/likes", status_code=status.HTTP_200_OK)
async def get_post_likes(
    post: Post = Depends(get_valid_post),
    db: Session = Depends(get_db)
):
    return post_controller.get_post_likes(post, db)
