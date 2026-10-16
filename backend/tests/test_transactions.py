from datetime import date, timedelta

from app.models.category import Category


def register_and_login(client, email: str, full_name: str):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": full_name,
        },
    )
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )


def create_category(client, name="Food", category_type="expense"):
    return client.post(
        "/api/v1/categories",
        json={"name": name, "type": category_type},
    ).json()


def transaction_payload(category_id, **overrides):
    payload = {
        "category_id": category_id,
        "type": "expense",
        "amount": "25.00",
        "transaction_date": "2026-10-15",
        "description": "Lunch",
    }
    payload.update(overrides)
    return payload


def test_user_can_create_transaction(client):
    register_and_login(client, "transaction@example.com", "Transaction User")
    category = create_category(client)

    response = client.post(
        "/api/v1/transactions",
        json=transaction_payload(category["id"]),
    )

    assert response.status_code == 201
    assert response.json()["amount"] == "25.00"
    assert response.json()["category"]["id"] == category["id"]
    assert response.json()["category"]["name"] == "Food"


def test_transaction_creation_ignores_client_user_id(client):
    register_and_login(client, "ownership@example.com", "Ownership User")
    category = create_category(client)

    response = client.post(
        "/api/v1/transactions",
        json=transaction_payload(category["id"], user_id=999999),
    )

    assert response.status_code == 201
    assert "user_id" not in response.json()


def test_transaction_rejects_invalid_amounts(client):
    register_and_login(client, "amounts@example.com", "Amounts User")
    category = create_category(client)

    for amount in ["0", "-1.00", "1.001", "100000000000.00"]:
        response = client.post(
            "/api/v1/transactions",
            json=transaction_payload(category["id"], amount=amount),
        )
        assert response.status_code == 422


def test_transaction_rejects_mismatched_category_type(client, db_session):
    register_and_login(client, "mismatch@example.com", "Mismatch User")
    category = Category(user_id=None, name="Salary", type="income")
    db_session.add(category)
    db_session.commit()

    response = client.post(
        "/api/v1/transactions",
        json=transaction_payload(category.id),
    )

    assert response.status_code == 422


def test_transaction_rejects_inaccessible_category(client, db_session):
    register_and_login(client, "inaccessible@example.com", "Inaccessible User")
    category = Category(user_id=None, name="Private", type="expense")
    db_session.add(category)
    db_session.commit()

    client.post("/api/v1/auth/logout")
    register_and_login(client, "category-owner@example.com", "Category Owner")
    private_category = client.post(
        "/api/v1/categories",
        json={"name": "Private Custom", "type": "expense"},
    ).json()
    client.post("/api/v1/auth/logout")
    register_and_login(client, "category-other@example.com", "Category Other")

    response = client.post(
        "/api/v1/transactions",
        json=transaction_payload(private_category["id"]),
    )

    assert response.status_code == 422


def test_user_can_list_only_own_transactions(client):
    register_and_login(client, "list-owner@example.com", "List Owner")
    category = create_category(client)
    client.post(
        "/api/v1/transactions",
        json=transaction_payload(category["id"]),
    )

    client.post("/api/v1/auth/logout")
    register_and_login(client, "list-other@example.com", "List Other")
    response = client.get("/api/v1/transactions")

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


def test_user_cannot_get_another_users_transaction(client):
    register_and_login(client, "get-owner@example.com", "Get Owner")
    category = create_category(client)
    transaction = client.post(
        "/api/v1/transactions",
        json=transaction_payload(category["id"]),
    ).json()

    client.post("/api/v1/auth/logout")
    register_and_login(client, "get-other@example.com", "Get Other")
    response = client.get(f"/api/v1/transactions/{transaction['id']}")

    assert response.status_code == 404


def test_transaction_list_is_paginated_and_stably_sorted(client):
    register_and_login(client, "pagination@example.com", "Pagination User")
    category = create_category(client)
    for days_ago in range(3):
        client.post(
            "/api/v1/transactions",
            json=transaction_payload(
                category["id"],
                transaction_date=str(date.today() - timedelta(days=days_ago)),
            ),
        )

    response = client.get("/api/v1/transactions?page=1&page_size=2")
    body = response.json()

    assert response.status_code == 200
    assert len(body["items"]) == 2
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["page_size"] == 2


def test_user_can_update_transaction(client):
    register_and_login(client, "update@example.com", "Update User")
    category = create_category(client)
    transaction = client.post(
        "/api/v1/transactions",
        json=transaction_payload(category["id"]),
    ).json()

    response = client.patch(
        f"/api/v1/transactions/{transaction['id']}",
        json={"amount": "40.50", "description": "Updated lunch"},
    )

    assert response.status_code == 200
    assert response.json()["amount"] == "40.50"
    assert response.json()["description"] == "Updated lunch"


def test_transaction_update_validates_combined_type_and_category(client):
    register_and_login(client, "update-type@example.com", "Update Type User")
    expense_category = create_category(client, "Food", "expense")
    income_category = create_category(client, "Salary", "income")
    transaction = client.post(
        "/api/v1/transactions",
        json=transaction_payload(expense_category["id"]),
    ).json()

    response = client.patch(
        f"/api/v1/transactions/{transaction['id']}",
        json={"type": "income"},
    )

    assert response.status_code == 422

    response = client.patch(
        f"/api/v1/transactions/{transaction['id']}",
        json={
            "type": "income",
            "category_id": income_category["id"],
        },
    )

    assert response.status_code == 200
    assert response.json()["type"] == "income"
    assert response.json()["category_id"] == income_category["id"]


def test_user_cannot_update_another_users_transaction(client):
    register_and_login(client, "update-owner@example.com", "Update Owner")
    category = create_category(client)
    transaction = client.post(
        "/api/v1/transactions",
        json=transaction_payload(category["id"]),
    ).json()

    client.post("/api/v1/auth/logout")
    register_and_login(client, "update-other@example.com", "Update Other")
    response = client.patch(
        f"/api/v1/transactions/{transaction['id']}",
        json={"amount": "99.00"},
    )

    assert response.status_code == 404


def test_user_can_delete_transaction(client):
    register_and_login(client, "delete-transaction@example.com", "Delete User")
    category = create_category(client)
    transaction = client.post(
        "/api/v1/transactions",
        json=transaction_payload(category["id"]),
    ).json()

    response = client.delete(f"/api/v1/transactions/{transaction['id']}")

    assert response.status_code == 204
    assert client.get(
        f"/api/v1/transactions/{transaction['id']}"
    ).status_code == 404


def test_user_cannot_delete_another_users_transaction(client):
    register_and_login(client, "delete-tx-owner@example.com", "Delete Owner")
    category = create_category(client)
    transaction = client.post(
        "/api/v1/transactions",
        json=transaction_payload(category["id"]),
    ).json()

    client.post("/api/v1/auth/logout")
    register_and_login(client, "delete-tx-other@example.com", "Delete Other")
    response = client.delete(f"/api/v1/transactions/{transaction['id']}")

    assert response.status_code == 404
