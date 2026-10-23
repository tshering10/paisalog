from datetime import datetime
from typing import TYPE_CHECKING
from unicodedata import category

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

if TYPE_CHECKING:
    from app.models.session import UserSession


def validate_full_name(value: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError("Full name must not be blank")

    has_letter = False
    allowed_punctuation = {"'", "\u2019", "-", "\u2010", "\u2011", "."}
    for character in normalized:
        character_category = category(character)
        if character_category.startswith("L"):
            has_letter = True
        elif (
            character_category.startswith("M")
            or character.isspace()
            or character in allowed_punctuation
        ):
            continue
        else:
            raise ValueError(
                "Full name may contain letters, spaces, apostrophes, hyphens, and periods"
            )

    if not has_letter:
        raise ValueError("Full name must contain at least one letter")

    return normalized


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=150)

    _validate_full_name = field_validator("full_name")(validate_full_name)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserProfileUpdate(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)

    _validate_full_name = field_validator("full_name")(validate_full_name)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_new_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_must_match(self) -> "PasswordChangeRequest":
        if self.new_password != self.confirm_new_password:
            raise ValueError("New passwords do not match")
        return self


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_new_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_must_match(self) -> "PasswordResetConfirmRequest":
        if self.new_password != self.confirm_new_password:
            raise ValueError("New passwords do not match")
        return self


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SessionRead(BaseModel):
    id: str
    user_agent: str | None
    ip_address: str | None
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime
    is_current: bool

    @classmethod
    def from_session(
        cls,
        session: "UserSession",
        *,
        is_current: bool,
    ) -> "SessionRead":
        return cls(
            id=session.id,
            user_agent=session.user_agent,
            ip_address=session.ip_address,
            created_at=session.created_at,
            last_used_at=session.last_used_at,
            expires_at=session.expires_at,
            is_current=is_current,
        )
