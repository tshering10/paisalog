from datetime import date

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
        json={
            "email": email,
            "password": "password123",
        },
    )


def test_monthly_summary(client, db_session):
    register_and_login(
        client,
        "analytics@example.com",
        "Analytics User",
    )

    user = db_session.query(User).filter(
        User.email == "analytics@example.com"
    ).one()

    expense_category = Category(
        user_id=None,
        name="Food",
        type="expense",
    )
    income_category = Category(
        user_id=None,
        name="Salary",
        type="income",
    )

    db_session.add_all([expense_category, income_category])
    db_session.commit()

    db_session.add_all(
        [
            Transaction(
                user_id=user.id,
                category_id=expense_category.id,
                type="expense",
                amount="100.00",
                transaction_date=date(2026, 10, 10),
            ),
            Transaction(
                user_id=user.id,
                category_id=income_category.id,
                type="income",
                amount="500.00",
                transaction_date=date(2026, 10, 15),
            ),
            Transaction(
                user_id=user.id,
                category_id=expense_category.id,
                type="expense",
                amount="25.00",
                transaction_date=date(2026, 9, 30),
            ),
        ]
    )
    db_session.commit()

    response = client.get(
        "/api/v1/analytics/summary?year=2026&month=10"
    )

    assert response.status_code == 200
    assert response.json() == {
        "year": 2026,
        "month": 10,
        "income": "500.00",
        "expenses": "100.00",
        "net": "400.00",
        "transaction_count": 2,
    }


def test_monthly_summary_requires_authentication(client):
    response = client.get(
        "/api/v1/analytics/summary?year=2026&month=10"
    )

    assert response.status_code == 401


def test_monthly_summary_has_zero_values_when_empty(client):
    register_and_login(
        client,
        "empty-analytics@example.com",
        "Empty Analytics User",
    )

    response = client.get(
        "/api/v1/analytics/summary?year=2026&month=10"
    )

    assert response.status_code == 200
    assert response.json() == {
        "year": 2026,
        "month": 10,
        "income": "0.00",
        "expenses": "0.00",
        "net": "0.00",
        "transaction_count": 0,
    }


def test_monthly_summary_rejects_invalid_month(client):
    register_and_login(
        client,
        "invalid-month@example.com",
        "Invalid Month User",
    )

    response = client.get(
        "/api/v1/analytics/summary?year=2026&month=13"
    )

    assert response.status_code == 422


def test_expenses_by_category(client, db_session):
    register_and_login(
        client,
        "category-analytics@example.com",
        "Category Analytics User",
    )
    user = db_session.query(User).filter(
        User.email == "category-analytics@example.com"
    ).one()
    food = Category(user_id=None, name="Food", type="expense")
    transport = Category(user_id=None, name="Transport", type="expense")
    db_session.add_all([food, transport])
    db_session.commit()
    db_session.add_all(
        [
            Transaction(
                user_id=user.id,
                category_id=food.id,
                type="expense",
                amount="100.00",
                transaction_date=date(2026, 10, 10),
            ),
            Transaction(
                user_id=user.id,
                category_id=food.id,
                type="expense",
                amount="50.00",
                transaction_date=date(2026, 10, 11),
            ),
            Transaction(
                user_id=user.id,
                category_id=transport.id,
                type="expense",
                amount="50.00",
                transaction_date=date(2026, 10, 12),
            ),
        ]
    )
    db_session.commit()

    response = client.get(
        "/api/v1/analytics/expenses-by-category?year=2026&month=10"
    )

    assert response.status_code == 200
    assert response.json() == {
        "year": 2026,
        "month": 10,
        "total_expenses": "200.00",
        "categories": [
            {
                "category_id": food.id,
                "category_name": "Food",
                "amount": "150.00",
                "percentage": "75.00",
            },
            {
                "category_id": transport.id,
                "category_name": "Transport",
                "amount": "50.00",
                "percentage": "25.00",
            },
        ],
    }


def test_expenses_by_category_empty_month(client):
    register_and_login(
        client,
        "empty-category-analytics@example.com",
        "Empty Category Analytics",
    )

    response = client.get(
        "/api/v1/analytics/expenses-by-category?year=2026&month=10"
    )

    assert response.status_code == 200
    assert response.json() == {
        "year": 2026,
        "month": 10,
        "total_expenses": "0.00",
        "categories": [],
    }


def test_expenses_by_category_requires_authentication(client):
    response = client.get(
        "/api/v1/analytics/expenses-by-category?year=2026&month=10"
    )

    assert response.status_code == 401


def test_monthly_trend_returns_zero_filled_ascending_months(client, db_session):
    register_and_login(
        client,
        "trend@example.com",
        "Trend User",
    )
    user = db_session.query(User).filter(
        User.email == "trend@example.com"
    ).one()
    category = Category(user_id=None, name="Salary", type="income")
    db_session.add(category)
    db_session.commit()
    db_session.add(
        Transaction(
            user_id=user.id,
            category_id=category.id,
            type="income",
            amount="500.00",
            transaction_date=date(2026, 9, 15),
        )
    )
    db_session.commit()

    response = client.get(
        "/api/v1/analytics/monthly-trend"
        "?year=2026&month=10&months=3"
    )

    assert response.status_code == 200
    assert response.json() == {
        "months": [
            {
                "year": 2026,
                "month": 8,
                "income": "0.00",
                "expenses": "0.00",
                "net": "0.00",
            },
            {
                "year": 2026,
                "month": 9,
                "income": "500.00",
                "expenses": "0.00",
                "net": "500.00",
            },
            {
                "year": 2026,
                "month": 10,
                "income": "0.00",
                "expenses": "0.00",
                "net": "0.00",
            },
        ]
    }


def test_monthly_trend_rejects_invalid_range(client):
    register_and_login(client, "trend-invalid@example.com", "Trend Invalid")

    response = client.get(
        "/api/v1/analytics/monthly-trend"
        "?year=2026&month=10&months=25"
    )

    assert response.status_code == 422


def test_monthly_trend_requires_authentication(client):
    response = client.get(
        "/api/v1/analytics/monthly-trend?year=2026&month=10"
    )

    assert response.status_code == 401