import logging

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.user import (
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    UserCreate,
    UserRead,
)
from app.services.auth import (
    CurrentPasswordIncorrectError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidPasswordResetTokenError,
    authenticate_user,
    change_password,
    create_password_reset_token,
    register_user,
    reset_password,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["authentication"],
)


def set_auth_cookie(response: Response, user_id: int, token_version: int) -> None:
    settings = get_settings()
    token = create_access_token(
        user_id=user_id,
        token_version=token_version,
        secret_key=settings.secret_key,
        expires_minutes=settings.access_token_expire_minutes,
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserCreate,
    response: Response,
    db: DbSession,
) -> UserRead:
    try:
        user = register_user(db, user_data)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from None

    set_auth_cookie(response, user.id, user.token_version)
    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def login(
    login_data: LoginRequest,
    response: Response,
    db: DbSession,
) -> UserRead:
    try:
        user = authenticate_user(
            db=db,
            email=str(login_data.email),
            password=login_data.password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from None

    set_auth_cookie(response, user.id, user.token_version)
    return UserRead.model_validate(user)


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def get_me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(response: Response) -> None:
    settings = get_settings()

    response.delete_cookie(
        key="access_token",
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
)
def change_password_endpoint(
    password_data: PasswordChangeRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    try:
        change_password(
            db=db,
            user=current_user,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
        )
    except CurrentPasswordIncorrectError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        ) from None


@router.post(
    "/password-reset/request",
    status_code=status.HTTP_202_ACCEPTED,
)
def request_password_reset(
    reset_data: PasswordResetRequest,
    db: DbSession,
) -> None:
    user = db.scalar(
        select(User).where(User.email == str(reset_data.email).strip().lower())
    )
    if user is not None and user.is_active:
        settings = get_settings()
        raw_token = create_password_reset_token(
            db=db,
            user=user,
            expires_minutes=settings.password_reset_token_expire_minutes,
            rate_limit_count=settings.password_reset_rate_limit_count,
            rate_limit_window_minutes=(
                settings.password_reset_rate_limit_window_minutes
            ),
        )
        if raw_token is None:
            return
        reset_url = (
            f"{settings.frontend_url.rstrip('/')}/reset-password?token={raw_token}"
        )
        logger.warning("Password reset link for %s: %s", user.email, reset_url)


@router.post(
    "/password-reset/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
)
def confirm_password_reset(
    reset_data: PasswordResetConfirmRequest,
    db: DbSession,
) -> None:
    try:
        reset_password(
            db=db,
            raw_token=reset_data.token,
            new_password=reset_data.new_password,
        )
    except InvalidPasswordResetTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        ) from None
