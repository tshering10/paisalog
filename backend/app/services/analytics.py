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


def _previous_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def _percentage_change(current: Decimal, previous: Decimal) -> Decimal | None:
    if not previous:
        return None
    return ((current - previous) / previous * Decimal(100)).quantize(
        MONEY_QUANTUM
    )


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
    calendar_days = (end_date - start_date).days
    average_daily_expenses = (expenses / calendar_days).quantize(MONEY_QUANTUM)

    return {
        "year": year,
        "month": month,
        "income": income,
        "expenses": expenses,
        "net": net,
        "transaction_count": transaction_count,
        "average_daily_expenses": average_daily_expenses,
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
            (amount / total_expenses * Decimal(100))
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
    statement = (
        select(
            func.extract("year", Transaction.transaction_date).label("year"),
            func.extract("month", Transaction.transaction_date).label("month"),
            func.sum(income_expression).label("income"),
            func.sum(expense_expression).label("expenses"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date < end_date,
        )
        .group_by(
            func.extract("year", Transaction.transaction_date),
            func.extract("month", Transaction.transaction_date),
        )
    )
    rows = {(int(row.year), int(row.month)): row for row in db.execute(statement).all()}

    trend = []
    for trend_year, trend_month in reversed(requested_months):
        row = rows.get((trend_year, trend_month))
        income = Decimal(row.income if row else 0).quantize(MONEY_QUANTUM)
        expenses = Decimal(row.expenses if row else 0).quantize(MONEY_QUANTUM)
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


def get_monthly_spending_comparison(
    db: Session,
    *,
    user_id: int,
    year: int,
    month: int,
) -> dict:
    _, current_end = get_month_range(year, month)
    previous_year, previous_month = _previous_month(year, month)
    previous_start, _ = get_month_range(previous_year, previous_month)

    statement = (
        select(
            Category.id,
            Category.name,
            func.extract("year", Transaction.transaction_date).label("year"),
            func.extract("month", Transaction.transaction_date).label("month"),
            func.sum(Transaction.amount).label("amount"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= previous_start,
            Transaction.transaction_date < current_end,
        )
        .group_by(
            Category.id,
            Category.name,
            func.extract("year", Transaction.transaction_date),
            func.extract("month", Transaction.transaction_date),
        )
    )

    rows = db.execute(statement).all()
    spending: dict[tuple[int, int, int], Decimal] = {
        (row.id, int(row.year), int(row.month)): Decimal(row.amount).quantize(
            MONEY_QUANTUM
        )
        for row in rows
    }
    category_names = {row.id: row.name for row in rows}
    category_ids = {category_id for category_id, _, _ in spending}
    categories = []
    for category_id in sorted(category_ids):
        current = spending.get((category_id, year, month), Decimal("0.00"))
        previous = spending.get(
            (category_id, previous_year, previous_month),
            Decimal("0.00"),
        )
        categories.append(
            {
                "category_id": category_id,
                "category_name": category_names[category_id],
                "current_expenses": current,
                "previous_expenses": previous,
                "absolute_change": (current - previous).quantize(MONEY_QUANTUM),
                "percentage_change": _percentage_change(current, previous),
            }
        )

    current_expenses = sum(
        (
            amount
            for (category_id, row_year, row_month), amount in spending.items()
            if row_year == year and row_month == month
        ),
        Decimal("0.00"),
    ).quantize(MONEY_QUANTUM)
    previous_expenses = sum(
        (
            amount
            for (category_id, row_year, row_month), amount in spending.items()
            if row_year == previous_year and row_month == previous_month
        ),
        Decimal("0.00"),
    ).quantize(MONEY_QUANTUM)

    return {
        "year": year,
        "month": month,
        "previous_year": previous_year,
        "previous_month": previous_month,
        "current_expenses": current_expenses,
        "previous_expenses": previous_expenses,
        "absolute_change": (current_expenses - previous_expenses).quantize(
            MONEY_QUANTUM
        ),
        "percentage_change": _percentage_change(
            current_expenses,
            previous_expenses,
        ),
        "categories": categories,
    }
