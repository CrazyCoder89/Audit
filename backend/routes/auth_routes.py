from fastapi import APIRouter, Depends, HTTPException, Request
#from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.user import (UserCreate, UserResponse, Token, UserUpdate,
                           UserAdminUpdate, PasswordChange)
from auth.auth_handler import hash_password, verify_password, create_access_token
from auth.dependencies import get_current_user, require_admin
from services.audit_services import log_action
from pydantic import BaseModel
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, request: Request,
             db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        designation=user_data.designation,
        department=user_data.department
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_action(db=db, action="user.register", user_id=new_user.id,
               resource_type="user", resource_id=new_user.id,
               details={"email": new_user.email, "role": new_user.role},
               ip_address=request.client.host)
    return new_user

class LoginRequest(BaseModel):
    email: str
    password: str
@router.post("/login", response_model=Token)
def login(
    request: Request,
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    token = create_access_token(
        data={"sub": user.email, "role": user.role}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_profile(
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """User updates their own profile — name, designation, department."""
    if update_data.full_name:
        current_user.full_name = update_data.full_name
    if update_data.designation is not None:
        current_user.designation = update_data.designation
    if update_data.department is not None:
        current_user.department = update_data.department
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/change-password")
def change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """User changes their own password."""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    log_action(db=db, action="user.password_changed",
               user_id=current_user.id, resource_type="user",
               resource_id=current_user.id)
    return {"message": "Password changed successfully"}


@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all users — admin and auditor only."""
    if current_user.role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return db.query(User).all()


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
def admin_update_user(
    user_id: int,
    update_data: UserAdminUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin updates any user — role, designation, department, active status."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from deactivating themselves
    if user_id == current_user.id and update_data.is_active == False:
        raise HTTPException(status_code=400,
                           detail="You cannot deactivate your own account")

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    log_action(db=db, action="user.admin_update", user_id=current_user.id,
               resource_type="user", resource_id=user_id,
               details=update_dict, ip_address=request.client.host)
    return user


@router.post("/users", response_model=UserResponse)
def admin_create_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin creates a user directly — bypasses self-registration."""
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        designation=user_data.designation,
        department=user_data.department
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_action(db=db, action="user.admin_create", user_id=current_user.id,
               resource_type="user", resource_id=new_user.id,
               details={"email": new_user.email, "role": new_user.role},
               ip_address=request.client.host)
    return new_user


@router.delete("/users/{user_id}")
def admin_delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin hard-deletes a user. Use deactivate for soft disable."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    log_action(db=db, action="user.delete", user_id=current_user.id,
               resource_type="user", resource_id=user_id,
               details={"email": user.email}, ip_address=request.client.host)
    return {"message": f"User {user_id} deleted"}

