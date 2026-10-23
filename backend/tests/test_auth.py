import re
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models.user import User
from app.services.reactivation import (
    InvalidReactivationTokenError,
    create_reactivation_token,
    reactivate_account,
)

REGISTER_PAYLOAD = {
    "email": "User1@Example.com",
    "password": "password123",
    "full_name": "Test User",
}


def test_register_returns_safe_user(client):
    response = client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 201
    assert "access_token=" in response.headers["set-cookie"]
    assert "httponly" in response.headers["set-cookie"].lower()
    body = response.json()
    assert body["email"] == "user1@example.com"
    assert body["full_name"] == "Test User"
    assert body["is_active"] is True
    assert "password" not in body
    assert "hashed_password" not in body

    me_response = client.get("/api/v1/auth/me")

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "user1@example.com"


def test_duplicate_email_is_case_insensitive(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    duplicate = {
        **REGISTER_PAYLOAD,
        "email": "user1@example.com",
    }
    response = client.post("/api/v1/auth/register", json=duplicate)

    assert response.status_code == 409
    assert response.json() == {"detail": "Email is already registered"}


@pytest.mark.parametrize(
    "full_name",
    ["John123", "!!!", "John@", "😀 User"],
)
def test_register_rejects_invalid_full_names(client, full_name):
    response = client.post(
        "/api/v1/auth/register",
        json={
            **REGISTER_PAYLOAD,
            "email": f"{full_name.replace(' ', '')}@example.com",
            "full_name": full_name,
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize("full_name", ["Mary Jane", "O'Connor", "Jean-Luc", "李小龍"])
def test_register_accepts_realistic_full_names(client, full_name):
    response = client.post(
        "/api/v1/auth/register",
        json={
            **REGISTER_PAYLOAD,
            "email": f"{full_name.replace(' ', '')}@example.com",
            "full_name": full_name,
        },
    )

    assert response.status_code == 201
    assert response.json()["full_name"] == full_name


def test_login_sets_http_only_cookie(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user1@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == "user1@example.com"
    assert "access_token=" in response.headers["set-cookie"]
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "hashed_password" not in response.json()


def test_wrong_password_and_unknown_email_have_same_error(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    wrong_password = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user1@example.com",
            "password": "wrong-password",
        },
    )
    unknown_email = client.post(
        "/api/v1/auth/login",
        json={
            "email": "missing@example.com",
            "password": "wrong-password",
        },
    )

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_me_returns_logged_in_user(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    client.post(
        "/api/v1/auth/login",
        json={
            "email": "user1@example.com",
            "password": "password123",
        },
    )

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == "user1@example.com"
    assert "hashed_password" not in response.json()


def test_me_requires_authentication(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_profile_update_requires_authentication(client):
    response = client.patch(
        "/api/v1/auth/profile",
        json={"full_name": "Updated User"},
    )

    assert response.status_code == 401


def test_profile_update_changes_full_name(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    response = client.patch(
        "/api/v1/auth/profile",
        json={"full_name": "  Updated User  "},
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated User"
    assert response.json()["email"] == "user1@example.com"
    assert client.get("/api/v1/auth/me").json()["full_name"] == "Updated User"


def test_profile_update_rejects_blank_name(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    response = client.patch(
        "/api/v1/auth/profile",
        json={"full_name": "   "},
    )

    assert response.status_code == 422


@pytest.mark.parametrize("full_name", ["Updated123", "!!!", "Updated@User"])
def test_profile_update_rejects_invalid_full_names(client, full_name):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    response = client.patch(
        "/api/v1/auth/profile",
        json={"full_name": full_name},
    )

    assert response.status_code == 422


def test_me_rejects_tampered_token(client):
    client.cookies.set("access_token", "tampered-token")

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_rejects_expired_token(client):
    settings = get_settings()
    token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.secret_key,
        algorithm="HS256",
    )
    client.cookies.set("access_token", token)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_logout_clears_cookie_and_protected_access(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    client.post(
        "/api/v1/auth/login",
        json={
            "email": "user1@example.com",
            "password": "password123",
        },
    )

    logout_response = client.post("/api/v1/auth/logout")
    me_response = client.get("/api/v1/auth/me")

    assert logout_response.status_code == 204
    assert me_response.status_code == 401


def test_login_creates_active_session(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    response = client.get("/api/v1/auth/sessions")

    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 1
    assert sessions[0]["is_current"] is True
    assert sessions[0]["user_agent"]


def test_logout_revokes_current_session(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    logout_response = client.post("/api/v1/auth/logout")
    sessions_response = client.get("/api/v1/auth/sessions")

    assert logout_response.status_code == 204
    assert sessions_response.status_code == 401


def test_deactivate_account_requires_correct_password(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    response = client.post(
        "/api/v1/auth/deactivate",
        json={"password": "wrong-password"},
    )

    assert response.status_code == 400
    assert client.get("/api/v1/auth/me").status_code == 200


def test_deactivate_account_blocks_current_session_and_login(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    response = client.post(
        "/api/v1/auth/deactivate",
        json={"password": "password123"},
    )

    assert response.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user1@example.com", "password": "password123"},
    )
    assert login_response.status_code == 403
    assert login_response.json() == {
        "detail": "Your account is temporarily deactivated"
    }


def test_deactivated_account_with_wrong_password_has_invalid_credentials_error(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    client.post("/api/v1/auth/deactivate", json={"password": "password123"})

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user1@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_reactivation_token_reactivates_account_and_is_single_use(client, db_session):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    client.post("/api/v1/auth/deactivate", json={"password": "password123"})
    user = db_session.scalar(select(User).where(User.email == "user1@example.com"))

    token = create_reactivation_token(
        db_session,
        user=user,
        expires_minutes=30,
        rate_limit_count=3,
        rate_limit_window_minutes=15,
    )
    assert token is not None

    reactivate_account(db_session, raw_token=token)

    assert db_session.get(User, user.id).is_active is True
    with pytest.raises(InvalidReactivationTokenError):
        reactivate_account(db_session, raw_token=token)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user1@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200


def test_reactivation_request_is_generic_and_rate_limited(client):
    unknown_response = client.post(
        "/api/v1/auth/reactivation/request",
        json={"email": "missing@example.com"},
    )
    assert unknown_response.status_code == 202

    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    client.post("/api/v1/auth/deactivate", json={"password": "password123"})
    for _ in range(3):
        response = client.post(
            "/api/v1/auth/reactivation/request",
            json={"email": "user1@example.com"},
        )
        assert response.status_code == 202


def test_reactivation_rejects_active_account_token_request(client, db_session):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    user = db_session.scalar(select(User).where(User.email == "user1@example.com"))

    token = create_reactivation_token(
        db_session,
        user=user,
        expires_minutes=30,
        rate_limit_count=3,
        rate_limit_window_minutes=15,
    )

    assert token is None


def test_delete_account_removes_user_and_owned_data(client, db_session):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    user_id = db_session.execute(
        select(User.id).where(User.email == "user1@example.com")
    ).scalar_one()

    response = client.request(
        "DELETE",
        "/api/v1/auth/account",
        json={"password": "password123"},
    )

    assert response.status_code == 204
    assert db_session.get(User, user_id) is None
    assert client.get("/api/v1/auth/me").status_code == 401


def test_delete_account_requires_correct_password(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    response = client.request(
        "DELETE",
        "/api/v1/auth/account",
        json={"password": "wrong-password"},
    )

    assert response.status_code == 400
    assert client.get("/api/v1/auth/me").status_code == 200


def test_user_can_revoke_another_session(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    client.post(
        "/api/v1/auth/login",
        json={"email": "user1@example.com", "password": "password123"},
    )
    sessions = client.get("/api/v1/auth/sessions").json()
    other_session = next(session for session in sessions if not session["is_current"])

    response = client.delete(f"/api/v1/auth/sessions/{other_session['id']}")

    assert response.status_code == 204
    assert len(client.get("/api/v1/auth/sessions").json()) == 1


def test_user_can_revoke_other_sessions(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    client.post(
        "/api/v1/auth/login",
        json={"email": "user1@example.com", "password": "password123"},
    )

    response = client.post("/api/v1/auth/sessions/revoke-others")

    assert response.status_code == 204
    sessions = client.get("/api/v1/auth/sessions").json()
    assert len(sessions) == 1
    assert sessions[0]["is_current"] is True


def test_change_password_requires_authentication(client):
    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "password123",
            "new_password": "new-password123",
            "confirm_new_password": "new-password123",
        },
    )

    assert response.status_code == 401


def test_change_password_rejects_wrong_current_password(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "wrong-password",
            "new_password": "new-password123",
            "confirm_new_password": "new-password123",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Current password is incorrect"}


def test_change_password_rejects_mismatched_new_passwords(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "password123",
            "new_password": "new-password123",
            "confirm_new_password": "different-password123",
        },
    )

    assert response.status_code == 422


def test_change_password_allows_login_with_new_password(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    change_response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "password123",
            "new_password": "new-password123",
            "confirm_new_password": "new-password123",
        },
    )

    assert change_response.status_code == 204

    old_password_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user1@example.com",
            "password": "password123",
        },
    )
    assert old_password_response.status_code == 401

    new_password_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user1@example.com",
            "password": "new-password123",
        },
    )
    assert new_password_response.status_code == 200


def test_change_password_invalidates_existing_session(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "password123",
            "new_password": "new-password123",
            "confirm_new_password": "new-password123",
        },
    )

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_password_reset_request_uses_generic_response_for_unknown_email(client):
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "missing@example.com"},
    )

    assert response.status_code == 202
    assert response.json() is None


def test_password_reset_request_is_rate_limited(client, caplog):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    for _ in range(3):
        response = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "user1@example.com"},
        )
        assert response.status_code == 202

    caplog.clear()
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "user1@example.com"},
    )

    assert response.status_code == 202
    assert "Password reset link" not in caplog.text


def test_password_reset_changes_password_and_token_is_single_use(client, caplog):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    request_response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "user1@example.com"},
    )

    assert request_response.status_code == 202
    match = re.search(r"reset-password\?token=([A-Za-z0-9_-]+)", caplog.text)
    assert match is not None
    token = match.group(1)

    reset_response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": token,
            "new_password": "reset-password123",
            "confirm_new_password": "reset-password123",
        },
    )

    assert reset_response.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401

    old_password_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user1@example.com",
            "password": "password123",
        },
    )
    assert old_password_response.status_code == 401

    new_password_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user1@example.com",
            "password": "reset-password123",
        },
    )
    assert new_password_response.status_code == 200

    reused_token_response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": token,
            "new_password": "another-password123",
            "confirm_new_password": "another-password123",
        },
    )
    assert reused_token_response.status_code == 400


def test_password_reset_rejects_mismatched_passwords(client, caplog):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "user1@example.com"},
    )

    match = re.search(r"reset-password\?token=([A-Za-z0-9_-]+)", caplog.text)
    assert match is not None

    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": match.group(1),
            "new_password": "new-password123",
            "confirm_new_password": "different-password123",
        },
    )

    assert response.status_code == 422
