from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import Category


class CategoryNameConflictError(Exception):
    """Raised when a category name conflicts with a visible category."""


class CategoryNotFoundError(Exception):
    """Raised when a user-owned category cannot be found."""


class CategoryInUseError(Exception):
    """Raised when a category is referenced by a transaction."""


def list_visible_categories(
    db: Session,
    *,
    user_id: int,
    category_type: str | None = None,
) -> list[Category]:
    statement = select(Category).where(
        or_(
            Category.user_id.is_(None),
            Category.user_id == user_id,
        )
    )

    if category_type is not None:
        statement = statement.where(Category.type == category_type)

    statement = statement.order_by(Category.type, Category.name, Category.id)
    return list(db.scalars(statement).all())


def create_custom_category(
    db: Session,
    *,
    user_id: int,
    name: str,
    category_type: str,
) -> Category:
    existing = db.scalar(
        select(Category).where(
            Category.type == category_type,
            or_(
                Category.user_id.is_(None),
                Category.user_id == user_id,
            ),
            Category.name.ilike(name),
        )
    )
    if existing is not None:
        raise CategoryNameConflictError

    category = Category(
        user_id=user_id,
        name=name,
        type=category_type,
    )
    db.add(category)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CategoryNameConflictError from exc

    db.refresh(category)
    return category


def rename_custom_category(
    db: Session,
    *,
    category_id: int,
    user_id: int,
    name: str,
) -> Category:
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
        )
    )
    if category is None:
        raise CategoryNotFoundError

    existing = db.scalar(
        select(Category).where(
            Category.id != category_id,
            Category.type == category.type,
            or_(
                Category.user_id.is_(None),
                Category.user_id == user_id,
            ),
            Category.name.ilike(name),
        )
    )
    if existing is not None:
        raise CategoryNameConflictError

    category.name = name

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CategoryNameConflictError from exc

    db.refresh(category)
    return category


def delete_custom_category(
    db: Session,
    *,
    category_id: int,
    user_id: int,
) -> None:
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
        )
    )
    if category is None:
        raise CategoryNotFoundError

    db.delete(category)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CategoryInUseError from exc
