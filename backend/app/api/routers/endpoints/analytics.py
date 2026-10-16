from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import CurrentUser, DbSession
from app.schemas.analytics import (
    ExpenseByCategoryResponse,
    MonthlySummary,
    MonthlyTrendResponse,
)
from app.services.analytics import (
    InvalidAnalyticsRangeError,
    InvalidAnalyticsPeriodError,
    get_expenses_by_category,
    get_monthly_summary,
    get_monthly_trend,
)


router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["analytics"],
)


@router.get(
    "/summary",
    response_model=MonthlySummary,
    summary="Get monthly income and expense summary",
)
def monthly_summary(
    current_user: CurrentUser,
    db: DbSession,
    year: Annotated[int, Query(ge=1)],
    month: Annotated[int, Query(ge=1, le=12)],
) -> MonthlySummary:
    try:
        summary = get_monthly_summary(
            db,
            user_id=current_user.id,
            year=year,
            month=month,
        )
    except InvalidAnalyticsPeriodError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid analytics period",
        ) from None

    return MonthlySummary.model_validate(summary)


@router.get(
    "/expenses-by-category",
    response_model=ExpenseByCategoryResponse,
    summary="Get monthly expenses grouped by category",
)
def expenses_by_category(
    current_user: CurrentUser,
    db: DbSession,
    year: Annotated[int, Query(ge=1)],
    month: Annotated[int, Query(ge=1, le=12)],
) -> ExpenseByCategoryResponse:
    try:
        breakdown = get_expenses_by_category(
            db,
            user_id=current_user.id,
            year=year,
            month=month,
        )
    except InvalidAnalyticsPeriodError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid analytics period",
        ) from None

    return ExpenseByCategoryResponse.model_validate(breakdown)


@router.get(
    "/monthly-trend",
    response_model=MonthlyTrendResponse,
    summary="Get monthly income and expense trends",
)
def monthly_trend(
    current_user: CurrentUser,
    db: DbSession,
    year: Annotated[int, Query(ge=1)],
    month: Annotated[int, Query(ge=1, le=12)],
    months: Annotated[int, Query(ge=1, le=24)] = 6,
) -> MonthlyTrendResponse:
    try:
        trend = get_monthly_trend(
            db,
            user_id=current_user.id,
            year=year,
            month=month,
            months=months,
        )
    except (InvalidAnalyticsPeriodError, InvalidAnalyticsRangeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid analytics period or range",
        ) from None

    return MonthlyTrendResponse.model_validate(trend)