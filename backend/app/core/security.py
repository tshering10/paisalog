from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(
    *,
    user_id: int,
    token_version: int,
    session_id: str,
    secret_key: str,
    expires_minutes: int,
) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=expires_minutes)

    payload = {
        "sub": str(user_id),
        "ver": token_version,
        "sid": session_id,
        "exp": expires_at,
    }

    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_access_token(*, token: str, secret_key: str) -> tuple[int, int, str]:
    payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    subject = payload.get("sub")

    if not isinstance(subject, str):
        raise jwt.InvalidTokenError("Token subject is missing")
    token_version = payload.get("ver")
    if not isinstance(token_version, int):
        raise jwt.InvalidTokenError("Token version is missing")
    session_id = payload.get("sid")
    if not isinstance(session_id, str):
        raise jwt.InvalidTokenError("Token session is missing")

    try:
        return int(subject), token_version, session_id
    except ValueError as exc:
        raise jwt.InvalidTokenError("Token subject is invalid") from exc
