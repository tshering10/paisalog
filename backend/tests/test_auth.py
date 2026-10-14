from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings


REGISTER_PAYLOAD = {
    "email": "User1@Example.com",
    "password": "password123",
    "full_name": "Test User",
}


def test_register_returns_safe_user(client):
    response = client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "user1@example.com"
    assert body["full_name"] == "Test User"
    assert body["is_active"] is True
    assert "password" not in body
    assert "hashed_password" not in body


def test_duplicate_email_is_case_insensitive(client):
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    duplicate = {
        **REGISTER_PAYLOAD,
        "email": "user1@example.com",
    }
    response = client.post("/api/v1/auth/register", json=duplicate)

    assert response.status_code == 409
    assert response.json() == {"detail": "Email is already registered"}


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


def test_me_rejects_tampered_token(client):
    client.cookies.set("access_token", "tampered-token")

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_rejects_expired_token(client):
    settings = get_settings()
    token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
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
