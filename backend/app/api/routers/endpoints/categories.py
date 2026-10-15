from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import CurrentUser, DbSession
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.categories import (
    CategoryNameConflictError,
    CategoryInUseError,
    CategoryNotFoundError,
    create_custom_category,
    delete_custom_category,
    list_visible_categories,
    rename_custom_category,
)


router = APIRouter(
    prefix="/api/v1/categories",
    tags=["categories"],
)


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom category",
)
def create_category(
    category_data: CategoryCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> CategoryRead:
    try:
        category = create_custom_category(
            db,
            user_id=current_user.id,
            name=category_data.name,
            category_type=category_data.type,
        )
    except CategoryNameConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A category with this name and type already exists",
        ) from None

    return CategoryRead.model_validate(category)


@router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Rename a custom category",
)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> CategoryRead:
    try:
        category = rename_custom_category(
            db,
            category_id=category_id,
            user_id=current_user.id,
            name=category_data.name,
        )
    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom category not found",
        ) from None
    except CategoryNameConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A category with this name and type already exists",
        ) from None

    return CategoryRead.model_validate(category)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a custom category",
)
def delete_category(
    category_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    try:
        delete_custom_category(
            db,
            category_id=category_id,
            user_id=current_user.id,
        )
    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom category not found",
        ) from None
    except CategoryInUseError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category cannot be deleted because it is used by a transaction",
        ) from None


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="List visible categories",
)
def list_categories(
    current_user: CurrentUser,
    db: DbSession,
    category_type: Annotated[
        Literal["income", "expense"] | None,
        Query(alias="type"),
    ] = None,
) -> list[CategoryRead]:
    categories = list_visible_categories(
        db,
        user_id=current_user.id,
        category_type=category_type,
    )
    return [CategoryRead.model_validate(category) for category in categories]
