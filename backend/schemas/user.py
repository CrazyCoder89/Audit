from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from enum import Enum
import re

class UserRole(str, Enum):
    admin = "admin"
    auditor = "auditor"
    viewer = "viewer"
    guest = "guest"

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.viewer
    designation: Optional[str] = None
    department: Optional[str] = None

    @field_validator('email')
    @classmethod
    def validate_email_domain(cls, v):
        fake_domains = [
            'fake.com', 'test.com', 'example.com', 'dummy.com',
            'notreal.com', 'noemail.com', 'nomail.com', 'fakemail.com',
            'tempmail.com', 'throwaway.com', 'mailinator.com',
            'guerrillamail.com', 'yopmail.com', 'trashmail.com',
            'sharklasers.com', 'spam4.me'
        ]
        domain = v.split('@')[-1].lower()
        if domain in fake_domains:
            raise ValueError(f'{domain} is not accepted. Use a real email.')
        return v

    @field_validator('full_name')
    @classmethod
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters')
        return v.strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    designation: Optional[str]
    department: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None

class UserAdminUpdate(BaseModel):
    full_name: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('New password must be at least 6 characters')
        return v
    