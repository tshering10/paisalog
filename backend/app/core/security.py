import jwt
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(
    *,
    user_id: int,
    secret_key: str,
    expires_minutes: int,
) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_access_token(*, token: str, secret_key: str) -> int:
    payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    subject = payload.get("sub")

    if not isinstance(subject, str):
        raise jwt.InvalidTokenError("Token subject is missing")

    try:
        return int(subject)
    except ValueError as exc:
        raise jwt.InvalidTokenError("Token subject is invalid") from exc