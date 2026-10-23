import logging

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import select

from app.api.dependencies import CurrentSession, CurrentUser, DbSession
from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.session import UserSession
from app.models.user import User
from app.schemas.user import (
    AccountPasswordRequest,
    AccountReactivationConfirmRequest,
    AccountReactivationRequest,
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    SessionRead,
    UserCreate,
    UserProfileUpdate,
    UserRead,
)
from app.services.account import (
    AccountPasswordIncorrectError,
    deactivate_account,
    delete_account,
)
from app.services.auth import (
    AccountDeactivatedError,
    CurrentPasswordIncorrectError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidPasswordResetTokenError,
    authenticate_user,
    change_password,
    create_password_reset_token,
    register_user,
    reset_password,
    update_profile,
)
from app.services.reactivation import (
    InvalidReactivationTokenError,
    create_reactivation_token,
    reactivate_account,
)
from app.services.sessions import (
    create_session,
    list_active_sessions,
    revoke_other_sessions,
    revoke_session,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["authentication"],
)


def set_auth_cookie(
    response: Response,
    user_id: int,
    token_version: int,
    session_id: str,
) -> None:
    settings = get_settings()
    token = create_access_token(
        user_id=user_id,
        token_version=token_version,
        session_id=session_id,
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
    request: Request,
    db: DbSession,
) -> UserRead:
    try:
        user = register_user(db, user_data)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from None

    session = create_session(
        db,
        user_id=user.id,
        expires_minutes=get_settings().access_token_expire_minutes,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    set_auth_cookie(response, user.id, user.token_version, session.id)
    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def login(
    login_data: LoginRequest,
    response: Response,
    request: Request,
    db: DbSession,
) -> UserRead:
    try:
        user = authenticate_user(
            db=db,
            email=str(login_data.email),
            password=login_data.password,
        )
    except AccountDeactivatedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is temporarily deactivated",
        ) from None
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from None

    session = create_session(
        db,
        user_id=user.id,
        expires_minutes=get_settings().access_token_expire_minutes,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    set_auth_cookie(response, user.id, user.token_version, session.id)
    return UserRead.model_validate(user)


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def get_me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post(
    "/reactivation/request",
    status_code=status.HTTP_202_ACCEPTED,
)
def request_account_reactivation(
    reactivation_data: AccountReactivationRequest,
    db: DbSession,
) -> None:
    user = db.scalar(
        select(User).where(User.email == str(reactivation_data.email).strip().lower())
    )
    if user is not None and not user.is_active:
        settings = get_settings()
        raw_token = create_reactivation_token(
            db,
            user=user,
            expires_minutes=settings.account_reactivation_token_expire_minutes,
            rate_limit_count=settings.account_reactivation_rate_limit_count,
            rate_limit_window_minutes=(
                settings.account_reactivation_rate_limit_window_minutes
            ),
        )
        if raw_token is not None:
            logger.info("Account reactivation email queued for %s", user.email)


@router.post(
    "/reactivation/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
)
def confirm_account_reactivation(
    reactivation_data: AccountReactivationConfirmRequest,
    db: DbSession,
) -> None:
    try:
        reactivate_account(db, raw_token=reactivation_data.token)
    except InvalidReactivationTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired account reactivation token",
        ) from None


@router.patch(
    "/profile",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def update_profile_endpoint(
    profile_data: UserProfileUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> UserRead:
    user = update_profile(db=db, user=current_user, profile_data=profile_data)
    return UserRead.model_validate(user)


@router.post(
    "/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deactivate_account_endpoint(
    account_data: AccountPasswordRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    try:
        deactivate_account(db, current_user, account_data.password)
    except AccountPasswordIncorrectError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect",
        ) from None


@router.delete(
    "/account",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_account_endpoint(
    account_data: AccountPasswordRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    try:
        delete_account(db, current_user, account_data.password)
    except AccountPasswordIncorrectError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect",
        ) from None


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    response: Response,
    current_session: CurrentSession,
    db: DbSession,
) -> None:
    settings = get_settings()
    revoke_session(db, current_session)

    response.delete_cookie(
        key="access_token",
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )


@router.get("/sessions", response_model=list[SessionRead])
def get_sessions(
    current_user: CurrentUser,
    current_session: CurrentSession,
    db: DbSession,
) -> list[SessionRead]:
    return [
        SessionRead.from_session(
            session,
            is_current=session.id == current_session.id,
        )
        for session in list_active_sessions(db, current_user.id)
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_session_endpoint(
    session_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    session = db.scalar(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == current_user.id,
        )
    )
    if session is not None:
        revoke_session(db, session)


@router.post(
    "/sessions/revoke-others",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revoke_other_sessions_endpoint(
    current_user: CurrentUser,
    current_session: CurrentSession,
    db: DbSession,
) -> None:
    revoke_other_sessions(
        db,
        user_id=current_user.id,
        current_session_id=current_session.id,
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
