from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import current_user, require_role
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import (
    TokenResponse,
    UserOut,
    UserCreate,
    UpdateMeRequest,
    ChangePasswordRequest,
)
from app.services import audit

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "account disabled")
    token = create_access_token(str(user.id), user.role.value)
    return TokenResponse(
        access_token=token, role=user.role, name=user.name, user_id=user.id
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UpdateMeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Met à jour son propre profil (nom, email)."""
    old = {"name": user.name, "email": user.email}
    data = payload.model_dump(exclude_unset=True)
    new_email = data.get("email")
    if new_email and new_email != user.email:
        exists = (
            db.query(User)
            .filter(User.email == new_email, User.id != user.id)
            .first()
        )
        if exists:
            raise HTTPException(status.HTTP_409_CONFLICT, "email already used")
        user.email = new_email
    if data.get("name"):
        user.name = data["name"]
    audit.log_action(
        db, entity="user", entity_id=user.id, action="update_profile",
        user_id=user.id, old_value=old, new_value=data,
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Change son propre mot de passe (vérifie le mot de passe actuel)."""
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "current password incorrect")
    user.hashed_password = hash_password(payload.new_password)
    audit.log_action(
        db, entity="user", entity_id=user.id, action="change_password", user_id=user.id,
    )
    db.commit()


@router.post(
    "/users",
    response_model=UserOut,
    dependencies=[Depends(require_role(UserRole.admin))],
)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "email already used")
    u = User(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u
