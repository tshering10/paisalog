from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User


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


def test_user_can_create_custom_category(client):
    register_and_login(client, "category@example.com", "Category User")

    response = client.post(
        "/api/v1/categories",
        json={"name": "Pet Care", "type": "expense"},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Pet Care"
    assert response.json()["type"] == "expense"
    assert response.json()["user_id"] is not None


def test_custom_category_name_is_normalized(client):
    register_and_login(client, "normalize@example.com", "Normalize User")

    response = client.post(
        "/api/v1/categories",
        json={"name": "  Pet   Care  ", "type": "expense"},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Pet Care"


def test_user_cannot_duplicate_visible_category(client, db_session):
    register_and_login(client, "duplicate@example.com", "Duplicate User")
    db_session.add(
        Category(user_id=None, name="Food & Dining", type="expense")
    )
    db_session.commit()

    response = client.post(
        "/api/v1/categories",
        json={"name": "food & dining", "type": "expense"},
    )

    assert response.status_code == 409


def test_category_creation_requires_authentication(client):
    response = client.post(
        "/api/v1/categories",
        json={"name": "Pet Care", "type": "expense"},
    )

    assert response.status_code == 401


def test_user_can_rename_custom_category(client):
    register_and_login(client, "rename@example.com", "Rename User")
    category = client.post(
        "/api/v1/categories",
        json={"name": "Pet Care", "type": "expense"},
    ).json()

    response = client.patch(
        f"/api/v1/categories/{category['id']}",
        json={"name": "Veterinary Care"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Veterinary Care"
    assert response.json()["type"] == "expense"


def test_category_rename_normalizes_name(client):
    register_and_login(client, "rename-normalize@example.com", "Rename User")
    category = client.post(
        "/api/v1/categories",
        json={"name": "Pet Care", "type": "expense"},
    ).json()

    response = client.patch(
        f"/api/v1/categories/{category['id']}",
        json={"name": "  Veterinary   Care  "},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Veterinary Care"


def test_user_cannot_rename_system_category(client, db_session):
    register_and_login(client, "rename-system@example.com", "Rename User")
    system_category = Category(
        user_id=None,
        name="Food & Dining",
        type="expense",
    )
    db_session.add(system_category)
    db_session.commit()

    response = client.patch(
        f"/api/v1/categories/{system_category.id}",
        json={"name": "Groceries"},
    )

    assert response.status_code == 404


def test_user_cannot_rename_another_users_category(client):
    register_and_login(client, "owner@example.com", "Owner")
    category = client.post(
        "/api/v1/categories",
        json={"name": "Pet Care", "type": "expense"},
    ).json()

    client.post("/api/v1/auth/logout")
    register_and_login(client, "other@example.com", "Other User")
    response = client.patch(
        f"/api/v1/categories/{category['id']}",
        json={"name": "Veterinary Care"},
    )

    assert response.status_code == 404


def test_user_cannot_rename_to_duplicate_visible_category(client, db_session):
    register_and_login(client, "rename-duplicate@example.com", "Rename User")
    category = client.post(
        "/api/v1/categories",
        json={"name": "Pet Care", "type": "expense"},
    ).json()
    db_session.add(
        Category(user_id=None, name="Food & Dining", type="expense")
    )
    db_session.commit()

    response = client.patch(
        f"/api/v1/categories/{category['id']}",
        json={"name": "food & dining"},
    )

    assert response.status_code == 409


def test_user_can_delete_custom_category(client):
    register_and_login(client, "delete@example.com", "Delete User")
    category = client.post(
        "/api/v1/categories",
        json={"name": "Pet Care", "type": "expense"},
    ).json()

    response = client.delete(f"/api/v1/categories/{category['id']}")

    assert response.status_code == 204
    categories = client.get("/api/v1/categories").json()
    assert all(item["id"] != category["id"] for item in categories)


def test_category_deletion_requires_authentication(client):
    response = client.delete("/api/v1/categories/1")

    assert response.status_code == 401


def test_user_cannot_delete_system_category(client, db_session):
    register_and_login(client, "delete-system@example.com", "Delete User")
    system_category = Category(
        user_id=None,
        name="Food & Dining",
        type="expense",
    )
    db_session.add(system_category)
    db_session.commit()

    response = client.delete(
        f"/api/v1/categories/{system_category.id}"
    )

    assert response.status_code == 404


def test_user_cannot_delete_another_users_category(client):
    register_and_login(client, "delete-owner@example.com", "Owner")
    category = client.post(
        "/api/v1/categories",
        json={"name": "Pet Care", "type": "expense"},
    ).json()

    client.post("/api/v1/auth/logout")
    register_and_login(client, "delete-other@example.com", "Other User")
    response = client.delete(f"/api/v1/categories/{category['id']}")

    assert response.status_code == 404


def test_user_cannot_delete_category_used_by_transaction(client, db_session):
    register_and_login(client, "delete-used@example.com", "Delete User")
    category = client.post(
        "/api/v1/categories",
        json={"name": "Pet Care", "type": "expense"},
    ).json()
    user = db_session.scalar(
        select(User).where(User.email == "delete-used@example.com")
    )
    db_session.add(
        Transaction(
            user_id=user.id,
            category_id=category["id"],
            type="expense",
            amount=Decimal("25.00"),
            transaction_date=date.today(),
        )
    )
    db_session.commit()

    response = client.delete(f"/api/v1/categories/{category['id']}")

    assert response.status_code == 409
