# Dependencies are functions FastAPI runs automatically before your route logic
# get_current_user = "who is making this request?" — used on protected routes
# require_admin = "is this person an admin?" — used on admin-only routes

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from auth.auth_handler import decode_token

# Tells FastAPI to look for a Bearer token in the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Extracts and validates the JWT token, then returns the User object from DB
# Any route that adds Depends(get_current_user) becomes a protected route
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    email = decode_token(token)
    if email is None:
        raise credentials_exception
    
    # Look up the user in DB to make sure they still exist and are active
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# Builds on get_current_user — additionally checks if the user is an admin
# Use this on routes that only admins should access
def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

