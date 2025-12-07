# model/user_model.py
"""사용자 ORM 모델 및 데이터 접근 함수."""
from typing import Any, Optional
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import Session, relationship

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
def get_users(db: Session):
    users = db.query(User).filter(User.is_deleted != True).all()
    return users

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    return user

def get_user_by_name(db: Session, name: str) -> Optional[User]:
    user = db.query(User).filter(User.name == name).first()
    return user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    return user

def create_user(db: Session, user_data: Any, hashed_pwd: str, img_path: Optional[str] = None) -> User:
    """신규 사용자 생성."""
    new_user = User( 
        email=user_data.email,
        name=user_data.name,
        password=hashed_pwd,
        img=img_path
    )
    db.add(new_user)
    db.flush()
    return new_user

def update_user(db: Session, user_id: int, updates: dict):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
        
    for key, value in updates.items():
        setattr(user, key, value)
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first() 
    if not user:
        return False
          
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    user.email = f"deleted_{user.id}_{timestamp}@deleted.com"
    user.name = f"탈퇴한사용자_{user.id}"
    user.is_deleted = True
    user.deleted_at = datetime.now()  
    
    return True 
    