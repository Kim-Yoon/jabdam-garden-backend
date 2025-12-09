# model/user_model.py
"""사용자 ORM 모델 및 데이터 접근 함수."""
from typing import Any, Optional
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    img = Column(String, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 좋아요 관계 추가
    likes = relationship("PostLike", back_populates="user", cascade="all, delete-orphan")


# 모든 사용자 조회
async def get_users(db: AsyncSession):
    result = await db.execute(
        select(User).where(User.is_deleted != True)
    )
    return result.scalars().all()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalars().first()


async def get_user_by_name(db: AsyncSession, name: str) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.name == name)
    )
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalars().first()


async def create_user(db: AsyncSession, user_data: Any, hashed_pwd: str, img_path: Optional[str] = None) -> User:
    """신규 사용자 생성."""
    new_user = User( 
        email=user_data.email,
        name=user_data.name,
        password=hashed_pwd,
        img=img_path
    )
    db.add(new_user)
    await db.flush()
    return new_user


async def update_user(db: AsyncSession, user_id: int, updates: dict):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        return None
        
    for key, value in updates.items():
        setattr(user, key, value)
    return user


async def delete_user(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        return False
          
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    user.email = f"deleted_{user.id}_{timestamp}@deleted.com"
    user.name = f"탈퇴한사용자_{user.id}"
    user.is_deleted = True
    user.deleted_at = func.now()  # DB 서버 시간 사용  
    
    return True
    