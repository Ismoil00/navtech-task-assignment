from typing import Literal

from pydantic import BaseModel, Field

from app.domain.enums import UserRole
from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)
    # кабинет, выбранный на странице входа; должен совпадать с ролью учётной записи
    portal: UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserRead
