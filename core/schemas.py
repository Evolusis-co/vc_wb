# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class SignupSchema(BaseModel):
    email: EmailStr
    password: str
    name: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class UserInfo(BaseModel):
    id: int
    name: str
    email: str
    user_type: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo

class UserResponse(BaseModel):
    user_id: int
    email: str
    name: str
    user_type: str
    trial_status: str
    company_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[UserResponse] = None

class LogoutResponse(BaseModel):
    message: str
    success: bool

class BusinessSignupSchema(BaseModel):
    company_name: str
    company_email: EmailStr
    admin_name: str
    admin_email: EmailStr
    admin_password: str

class AddBusinessUserSchema(BaseModel):
    name: str
    email: EmailStr
    password: str
    user_type: str