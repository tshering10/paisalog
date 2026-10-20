from fastapi import APIRouter, HTTPException, Response, status

from app.api.dependencies import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.security import create_access_token
from app.schemas.user import LoginRequest, UserCreate, UserRead
from app.services.auth import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    authenticate_user,
    register_user,
)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["authentication"],
)


def set_auth_cookie(response: Response, user_id: int) -> None:
    settings = get_settings()
    token = create_access_token(
        user_id=user_id,
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

    set_auth_cookie(response, user.id)
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

    set_auth_cookie(response, user.id)
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
