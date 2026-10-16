from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.transaction import Transaction


MONEY_QUANTUM = Decimal("0.01")


class InvalidAnalyticsPeriodError(Exception):
    """Raised when an analytics year or month is invalid."""


class InvalidAnalyticsRangeError(Exception):
    """Raised when the requested trend range is invalid."""


def get_month_range(year: int, month: int) -> tuple[date, date]:
    if year < 1 or month < 1 or month > 12:
        raise InvalidAnalyticsPeriodError

    first_day = date(year, month, 1)

    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)

    return first_day, next_month


def get_monthly_summary(
    db: Session,
    *,
    user_id: int,
    year: int,
    month: int,
) -> dict:
    start_date, end_date = get_month_range(year, month)

    income_expression = case(
        (Transaction.type == "income", Transaction.amount),
        else_=Decimal("0.00"),
    )

    expense_expression = case(
        (Transaction.type == "expense", Transaction.amount),
        else_=Decimal("0.00"),
    )

    statement = select(
        func.coalesce(func.sum(income_expression), 0),
        func.coalesce(func.sum(expense_expression), 0),
        func.count(Transaction.id),
    ).where(
        Transaction.user_id == user_id,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date < end_date,
    )

    income, expenses, transaction_count = db.execute(statement).one()

    income = Decimal(income or 0).quantize(MONEY_QUANTUM)
    expenses = Decimal(expenses or 0).quantize(MONEY_QUANTUM)
    net = (income - expenses).quantize(MONEY_QUANTUM)

    return {
        "year": year,
        "month": month,
        "income": income,
        "expenses": expenses,
        "net": net,
        "transaction_count": transaction_count,
    }


def get_expenses_by_category(
    db: Session,
    *,
    user_id: int,
    year: int,
    month: int,
) -> dict:
    start_date, end_date = get_month_range(year, month)
    statement = (
        select(
            Category.id,
            Category.name,
            func.sum(Transaction.amount).label("amount"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date < end_date,
        )
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Transaction.amount).desc(), Category.id)
    )
    rows = db.execute(statement).all()
    total_expenses = sum(
        (Decimal(row.amount or 0) for row in rows),
        Decimal("0.00"),
    ).quantize(MONEY_QUANTUM)

    categories = []
    for row in rows:
        amount = Decimal(row.amount or 0).quantize(MONEY_QUANTUM)
        percentage = (
            (amount / total_expenses * Decimal("100"))
            if total_expenses
            else Decimal("0.00")
        ).quantize(MONEY_QUANTUM)
        categories.append(
            {
                "category_id": row.id,
                "category_name": row.name,
                "amount": amount,
                "percentage": percentage,
            }
        )

    return {
        "year": year,
        "month": month,
        "total_expenses": total_expenses,
        "categories": categories,
    }


def get_monthly_trend(
    db: Session,
    *,
    user_id: int,
    year: int,
    month: int,
    months: int,
) -> dict:
    if months < 1 or months > 24:
        raise InvalidAnalyticsRangeError

    get_month_range(year, month)
    requested_months: list[tuple[int, int]] = []
    current_year = year
    current_month = month
    for _ in range(months):
        requested_months.append((current_year, current_month))
        current_month -= 1
        if current_month == 0:
            current_month = 12
            current_year -= 1

    start_year, start_month = requested_months[-1]
    start_date, _ = get_month_range(start_year, start_month)
    _, end_date = get_month_range(year, month)

    income_expression = case(
        (Transaction.type == "income", Transaction.amount),
        else_=Decimal("0.00"),
    )
    expense_expression = case(
        (Transaction.type == "expense", Transaction.amount),
        else_=Decimal("0.00"),
    )
    statement = select(
        func.extract("year", Transaction.transaction_date).label("year"),
        func.extract("month", Transaction.transaction_date).label("month"),
        func.sum(income_expression).label("income"),
        func.sum(expense_expression).label("expenses"),
    ).where(
        Transaction.user_id == user_id,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date < end_date,
    ).group_by(
        func.extract("year", Transaction.transaction_date),
        func.extract("month", Transaction.transaction_date),
    )
    rows = {
        (int(row.year), int(row.month)): row
        for row in db.execute(statement).all()
    }

    trend = []
    for trend_year, trend_month in reversed(requested_months):
        row = rows.get((trend_year, trend_month))
        income = Decimal(row.income if row else 0).quantize(MONEY_QUANTUM)
        expenses = Decimal(row.expenses if row else 0).quantize(
            MONEY_QUANTUM
        )
        trend.append(
            {
                "year": trend_year,
                "month": trend_month,
                "income": income,
                "expenses": expenses,
                "net": (income - expenses).quantize(MONEY_QUANTUM),
            }
        )

    return {"months": trend}