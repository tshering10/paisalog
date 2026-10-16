from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.category import Category
from app.models.transaction import Transaction


class InvalidTransactionCategoryError(Exception):
    """Raised when a category is unavailable or mismatched for a transaction."""


class TransactionNotFoundError(Exception):
    """Raised when an owned transaction cannot be found."""


class InvalidTransactionFilterError(Exception):
    """Raised when transaction list filters are inconsistent."""


def _get_visible_category(
    db: Session,
    *,
    category_id: int,
    user_id: int,
    transaction_type: str,
) -> Category:
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            or_(
                Category.user_id.is_(None),
                Category.user_id == user_id,
            ),
        )
    )
    if category is None or category.type != transaction_type:
        raise InvalidTransactionCategoryError
    return category


def create_transaction(
    db: Session,
    *,
    user_id: int,
    category_id: int,
    transaction_type: str,
    amount: Decimal,
    transaction_date: date,
    description: str | None,
) -> Transaction:
    _get_visible_category(
        db,
        category_id=category_id,
        user_id=user_id,
        transaction_type=transaction_type,
    )

    transaction = Transaction(
        user_id=user_id,
        category_id=category_id,
        type=transaction_type,
        amount=amount,
        transaction_date=transaction_date,
        description=description,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def get_transaction(
    db: Session,
    *,
    transaction_id: int,
    user_id: int,
) -> Transaction:
    transaction = db.scalar(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
        )
    )
    if transaction is None:
        raise TransactionNotFoundError
    return transaction


def list_transactions(
    db: Session,
    *,
    user_id: int,
    page: int,
    page_size: int,
    transaction_type: str | None = None,
    category_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[Transaction], int]:
    base_query = select(Transaction).where(Transaction.user_id == user_id)
    if date_from is not None and date_to is not None and date_from > date_to:
        raise InvalidTransactionFilterError
    if transaction_type is not None:
        base_query = base_query.where(Transaction.type == transaction_type)
    if category_id is not None:
        base_query = base_query.where(Transaction.category_id == category_id)
    if date_from is not None:
        base_query = base_query.where(Transaction.transaction_date >= date_from)
    if date_to is not None:
        base_query = base_query.where(Transaction.transaction_date <= date_to)

    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    statement = (
        base_query.options(selectinload(Transaction.category))
        .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.scalars(statement).all()), total


def update_transaction(
    db: Session,
    *,
    transaction_id: int,
    user_id: int,
    changes: dict,
) -> Transaction:
    transaction = db.scalar(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
        )
    )
    if transaction is None:
        raise TransactionNotFoundError

    resulting_category_id = changes.get("category_id", transaction.category_id)
    resulting_type = changes.get("type", transaction.type)
    if "category_id" in changes or "type" in changes:
        _get_visible_category(
            db,
            category_id=resulting_category_id,
            user_id=user_id,
            transaction_type=resulting_type,
        )

    for field, value in changes.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)
    return get_transaction(
        db,
        transaction_id=transaction.id,
        user_id=user_id,
    )


def delete_transaction(
    db: Session,
    *,
    transaction_id: int,
    user_id: int,
) -> None:
    transaction = db.scalar(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
        )
    )
    if transaction is None:
        raise TransactionNotFoundError

    db.delete(transaction)
    db.commit()
