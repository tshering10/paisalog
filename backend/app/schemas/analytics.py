from decimal import Decimal
from pydantic import BaseModel, Field


class MonthlySummary(BaseModel):
    year: int
    month: int = Field(ge=1, le=12)
    income: Decimal
    expenses: Decimal
    net: Decimal
    transaction_count: int


class ExpenseCategoryBreakdown(BaseModel):
    category_id: int
    category_name: str
    amount: Decimal
    percentage: Decimal


class ExpenseByCategoryResponse(BaseModel):
    year: int
    month: int = Field(ge=1, le=12)
    total_expenses: Decimal
    categories: list[ExpenseCategoryBreakdown]


class MonthlyTrendItem(BaseModel):
    year: int
    month: int = Field(ge=1, le=12)
    income: Decimal
    expenses: Decimal
    net: Decimal


class MonthlyTrendResponse(BaseModel):
    months: list[MonthlyTrendItem]