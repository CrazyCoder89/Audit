from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.user import UserCreate, UserResponse, Token
from auth.auth_handler import hash_password, verify_password, create_access_token
from auth.dependencies import get_current_user
from services.audit_services import log_action

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        role=user_data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Log the registration
    log_action(
        db=db,
        action="user.register",
        user_id=new_user.id,
        resource_type="user",
        resource_id=new_user.id,
        details={"email": new_user.email, "role": new_user.role},
        ip_address=request.client.host
    )

    return new_user

@router.post("/login", response_model=Token)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Log failed login attempt
        log_action(
            db=db,
            action="user.login_failed",
            details={"email": form_data.username},
            ip_address=request.client.host
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"sub": user.email, "role": user.role})

    # Log successful login
    log_action(
        db=db,
        action="user.login",
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
        details={"email": user.email},
        ip_address=request.client.host
    )

    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


