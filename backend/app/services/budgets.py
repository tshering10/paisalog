from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.budget import MonthlyBudget
from app.models.category import Category
from app.models.transaction import Transaction
from app.services.analytics import get_month_range

MONEY_QUANTUM = Decimal("0.01")
ALERT_THRESHOLDS = (80, 90, 99, 100)


class BudgetCategoryError(Exception):
    """Raised when a budget category is missing, inaccessible, or not expenses."""


class BudgetConflictError(Exception):
    """Raised when a budget already exists for a month and category."""


class BudgetNotFoundError(Exception):
    """Raised when an owned budget cannot be found."""


def _validate_category(
    db: Session,
    *,
    category_id: int,
    user_id: int,
) -> Category:
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.type == "expense",
            (Category.user_id.is_(None) | (Category.user_id == user_id)),
        )
    )
    if category is None:
        raise BudgetCategoryError
    return category


def _find_existing(
    db: Session,
    *,
    user_id: int,
    year: int,
    month: int,
    category_id: int | None,
) -> MonthlyBudget | None:
    statement = select(MonthlyBudget).where(
        MonthlyBudget.user_id == user_id,
        MonthlyBudget.year == year,
        MonthlyBudget.month == month,
    )
    if category_id is None:
        statement = statement.where(MonthlyBudget.category_id.is_(None))
    else:
        statement = statement.where(MonthlyBudget.category_id == category_id)
    return db.scalar(statement)


def _usage(
    db: Session,
    *,
    user_id: int,
    year: int,
    month: int,
    category_id: int | None,
) -> Decimal:
    start_date, end_date = get_month_range(year, month)
    statement = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.type == "expense",
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date < end_date,
    )
    if category_id is not None:
        statement = statement.where(Transaction.category_id == category_id)
    return Decimal(db.scalar(statement) or 0).quantize(MONEY_QUANTUM)


def _serialize_budget(
    db: Session,
    budget: MonthlyBudget,
    spent: Decimal | None = None,
) -> dict:
    if spent is None:
        spent = _usage(
            db,
            user_id=budget.user_id,
            year=budget.year,
            month=budget.month,
            category_id=budget.category_id,
        )
    percentage = (spent / budget.amount * Decimal(100)).quantize(MONEY_QUANTUM)
    alert_threshold = next(
        (
            threshold
            for threshold in reversed(ALERT_THRESHOLDS)
            if percentage >= threshold
        ),
        None,
    )
    return {
        "id": budget.id,
        "year": budget.year,
        "month": budget.month,
        "category_id": budget.category_id,
        "category_name": budget.category.name if budget.category else None,
        "amount": budget.amount,
        "spent": spent,
        "remaining": (budget.amount - spent).quantize(MONEY_QUANTUM),
        "percentage_used": percentage,
        "alert_threshold": alert_threshold,
        "is_exceeded": spent >= budget.amount,
        "created_at": budget.created_at,
        "updated_at": budget.updated_at,
    }


def create_budget(
    db: Session,
    *,
    user_id: int,
    year: int,
    month: int,
    category_id: int | None,
    amount: Decimal,
) -> dict:
    if category_id is not None:
        _validate_category(db, category_id=category_id, user_id=user_id)
    if _find_existing(
        db,
        user_id=user_id,
        year=year,
        month=month,
        category_id=category_id,
    ):
        raise BudgetConflictError
    budget = MonthlyBudget(
        user_id=user_id,
        category_id=category_id,
        year=year,
        month=month,
        amount=amount,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return _serialize_budget(db, budget)


def list_budgets(
    db: Session,
    *,
    user_id: int,
    year: int,
    month: int,
) -> list[dict]:
    budgets = db.scalars(
        select(MonthlyBudget)
        .options(selectinload(MonthlyBudget.category))
        .where(
            MonthlyBudget.user_id == user_id,
            MonthlyBudget.year == year,
            MonthlyBudget.month == month,
        )
        .order_by(MonthlyBudget.category_id.is_not(None), MonthlyBudget.category_id)
    ).all()
    start_date, end_date = get_month_range(year, month)
    spending_rows = db.execute(
        select(
            Transaction.category_id,
            func.sum(Transaction.amount).label("spent"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date < end_date,
        )
        .group_by(Transaction.category_id)
    ).all()
    spent_by_category = {
        row.category_id: Decimal(row.spent).quantize(MONEY_QUANTUM)
        for row in spending_rows
    }
    total_spent = sum(spent_by_category.values(), Decimal("0.00"))
    return [
        _serialize_budget(
            db,
            budget,
            total_spent if budget.category_id is None else spent_by_category.get(
                budget.category_id,
                Decimal("0.00"),
            ),
        )
        for budget in budgets
    ]


def update_budget(
    db: Session,
    *,
    budget_id: int,
    user_id: int,
    amount: Decimal,
) -> dict:
    budget = db.scalar(
        select(MonthlyBudget)
        .options(selectinload(MonthlyBudget.category))
        .where(
            MonthlyBudget.id == budget_id,
            MonthlyBudget.user_id == user_id,
        )
    )
    if budget is None:
        raise BudgetNotFoundError
    budget.amount = amount
    db.commit()
    db.refresh(budget)
    return _serialize_budget(db, budget)


def delete_budget(db: Session, *, budget_id: int, user_id: int) -> None:
    budget = db.scalar(
        select(MonthlyBudget).where(
            MonthlyBudget.id == budget_id,
            MonthlyBudget.user_id == user_id,
        )
    )
    if budget is None:
        raise BudgetNotFoundError
    db.delete(budget)
    db.commit()
