from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.category import Category


DEFAULT_CATEGORIES = (
    ("Food & Dining", "expense"),
    ("Groceries", "expense"),
    ("Housing", "expense"),
    ("Utilities", "expense"),
    ("Transport", "expense"),
    ("Health", "expense"),
    ("Education", "expense"),
    ("Shopping", "expense"),
    ("Entertainment", "expense"),
    ("Travel", "expense"),
    ("Other", "expense"),
    ("Salary", "income"),
    ("Freelance", "income"),
    ("Business", "income"),
    ("Gifts", "income"),
    ("Interest", "income"),
    ("Other", "income"),
)


def seed_default_categories() -> int:
    db = SessionLocal()
    inserted_count = 0

    try:
        for name, category_type in DEFAULT_CATEGORIES:
            existing = db.scalar(
                select(Category).where(
                    Category.user_id.is_(None),
                    Category.type == category_type,
                    Category.name.ilike(name),
                )
            )

            if existing is None:
                db.add(
                    Category(
                        user_id=None,
                        name=name,
                        type=category_type,
                    )
                )
                inserted_count += 1

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return inserted_count


if __name__ == "__main__":
    inserted_count = seed_default_categories()
    print(f"Inserted {inserted_count} default categories.")
