from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional
from utils.pwd_validators import validate_password_strength, check_passwords_match

class UserCreateRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=10)
    password: str = Field(..., min_length=8, max_length=20)
    password_confirm: str = Field(..., min_length=8, max_length=20)
    # profile_image는 UploadFile로 라우터에서 별도 처리

    # 개별 필드 검증
    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)
    
    @model_validator(mode='after')
    def passwords_match(self):
        check_passwords_match(self.password, self.password_confirm) 
        return self

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=20)

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    profile_image: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserAuthResponse(UserResponse):
    """인증 응답용 (회원가입, 로그인)"""
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=10)
    # profile_image는 UploadFile로 라우터에서 별도 처리

class PasswordUpdate(BaseModel):
    current_pwd: str = Field(..., min_length=8, max_length=20)
    password: str = Field(..., min_length=8, max_length=20)
    password_confirm: str = Field(..., min_length=8, max_length=20)

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)
    
    @model_validator(mode='after')
    def passwords_match(self):
        check_passwords_match(self.password, self.password_confirm) 
        return self