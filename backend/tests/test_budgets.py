from tests.helpers import verify_registered_user


def register_and_login(client, email: str, full_name: str):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": full_name,
        },
    )
    verify_registered_user(client, email)
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )


def create_category(client, name="Food"):
    return client.post(
        "/api/v1/categories",
        json={"name": name, "type": "expense"},
    ).json()


def create_transaction(client, category_id, amount="80.00"):
    return client.post(
        "/api/v1/transactions",
        json={
            "category_id": category_id,
            "type": "expense",
            "amount": amount,
            "transaction_date": "2026-11-15",
        },
    )


def test_user_can_create_and_list_category_budget_with_usage(client):
    register_and_login(client, "budget@example.com", "Budget User")
    category = create_category(client)
    assert create_transaction(client, category["id"]).status_code == 201

    response = client.post(
        "/api/v1/budgets",
        json={
            "year": 2026,
            "month": 11,
            "category_id": category["id"],
            "amount": "100.00",
        },
    )

    assert response.status_code == 201
    assert response.json()["category_name"] == "Food"
    assert response.json()["spent"] == "80.00"
    assert response.json()["remaining"] == "20.00"
    assert response.json()["percentage_used"] == "80.00"
    assert response.json()["alert_threshold"] == 80
    assert response.json()["is_exceeded"] is False

    listed = client.get("/api/v1/budgets?year=2026&month=11")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_total_budget_tracks_all_expenses(client):
    register_and_login(client, "total-budget@example.com", "Total Budget User")
    food = create_category(client, "Food")
    transport = create_category(client, "Transport")
    assert create_transaction(client, food["id"], "80.00").status_code == 201
    assert create_transaction(client, transport["id"], "30.00").status_code == 201

    response = client.post(
        "/api/v1/budgets",
        json={"year": 2026, "month": 11, "amount": "100.00"},
    )

    assert response.status_code == 201
    assert response.json()["category_id"] is None
    assert response.json()["spent"] == "110.00"
    assert response.json()["remaining"] == "-10.00"
    assert response.json()["alert_threshold"] == 100
    assert response.json()["is_exceeded"] is True


def test_budget_rejects_income_category_and_duplicates(client):
    register_and_login(client, "budget-validation@example.com", "Budget Validation")
    income = client.post(
        "/api/v1/categories",
        json={"name": "Salary", "type": "income"},
    ).json()

    invalid = client.post(
        "/api/v1/budgets",
        json={
            "year": 2026,
            "month": 11,
            "category_id": income["id"],
            "amount": "100.00",
        },
    )
    assert invalid.status_code == 422

    first = client.post(
        "/api/v1/budgets",
        json={"year": 2026, "month": 11, "amount": "100.00"},
    )
    duplicate = client.post(
        "/api/v1/budgets",
        json={"year": 2026, "month": 11, "amount": "200.00"},
    )
    assert first.status_code == 201
    assert duplicate.status_code == 409


def test_user_cannot_access_another_users_budget(client):
    register_and_login(client, "budget-owner@example.com", "Budget Owner")
    budget = client.post(
        "/api/v1/budgets",
        json={"year": 2026, "month": 11, "amount": "100.00"},
    ).json()

    client.post("/api/v1/auth/logout")
    register_and_login(client, "budget-other@example.com", "Budget Other")
    response = client.patch(
        f"/api/v1/budgets/{budget['id']}",
        json={"amount": "200.00"},
    )

    assert response.status_code == 404


def test_budget_endpoints_require_email_verification(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "unverified-budget@example.com",
            "password": "password123",
            "full_name": "Unverified Budget",
        },
    )
    client.post(
        "/api/v1/auth/login",
        json={
            "email": "unverified-budget@example.com",
            "password": "password123",
        },
    )

    response = client.get("/api/v1/budgets?year=2026&month=11")

    assert response.status_code == 403
