from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import DbSession, VerifiedCurrentUser
from app.schemas.budget import (
    MonthlyBudgetCreate,
    MonthlyBudgetRead,
    MonthlyBudgetUpdate,
)
from app.services.budgets import (
    BudgetCategoryError,
    BudgetConflictError,
    BudgetNotFoundError,
    create_budget,
    delete_budget,
    list_budgets,
    update_budget,
)

router = APIRouter(
    prefix="/api/v1/budgets",
    tags=["budgets"],
)


@router.post("", response_model=MonthlyBudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget_endpoint(
    budget_data: MonthlyBudgetCreate,
    current_user: VerifiedCurrentUser,
    db: DbSession,
) -> MonthlyBudgetRead:
    try:
        budget = create_budget(
            db,
            user_id=current_user.id,
            year=budget_data.year,
            month=budget_data.month,
            category_id=budget_data.category_id,
            amount=budget_data.amount,
        )
    except BudgetCategoryError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Budget category must be an accessible expense category",
        ) from None
    except BudgetConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A budget already exists for this month and category",
        ) from None
    return MonthlyBudgetRead.model_validate(budget)


@router.get("", response_model=list[MonthlyBudgetRead])
def list_budget_endpoint(
    current_user: VerifiedCurrentUser,
    db: DbSession,
    year: Annotated[int, Query(ge=1)],
    month: Annotated[int, Query(ge=1, le=12)],
) -> list[MonthlyBudgetRead]:
    budgets = list_budgets(
        db,
        user_id=current_user.id,
        year=year,
        month=month,
    )
    return [MonthlyBudgetRead.model_validate(budget) for budget in budgets]


@router.patch("/{budget_id}", response_model=MonthlyBudgetRead)
def update_budget_endpoint(
    budget_id: int,
    budget_data: MonthlyBudgetUpdate,
    current_user: VerifiedCurrentUser,
    db: DbSession,
) -> MonthlyBudgetRead:
    try:
        budget = update_budget(
            db,
            budget_id=budget_id,
            user_id=current_user.id,
            amount=budget_data.amount,
        )
    except BudgetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found",
        ) from None
    return MonthlyBudgetRead.model_validate(budget)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget_endpoint(
    budget_id: int,
    current_user: VerifiedCurrentUser,
    db: DbSession,
) -> None:
    try:
        delete_budget(db, budget_id=budget_id, user_id=current_user.id)
    except BudgetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found",
        ) from None
