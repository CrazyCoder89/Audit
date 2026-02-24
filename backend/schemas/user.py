#going in requests and coming out request from api routes.
from pydantic import BaseModel, EmailStr
from enum import Enum
from typing import Optional
from datetime import datetime

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

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    class Config: #allows reading data from sqlalchemy models objects

        from_attributes = True

#return after successful login
class Token(BaseModel):
    access_token: str    #jwt token 
    token_type: str      #alwys "bearer" 

#used internally when decoding a jwt token to get user info
class TokenData(BaseModel):
    email: Optional[str] = None

