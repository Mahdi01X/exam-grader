from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    name: str
    user_id: int


class UserOut(BaseModel):
    id: int
    # str (pas EmailStr) : modèle de SORTIE — on n'impose pas la validation stricte
    # ici (ex. admin@local). La validation reste sur les entrées (login, create, update).
    email: str
    name: str
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: UserRole = UserRole.professeur


class UpdateMeRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)
