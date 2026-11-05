from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MonthlyBudgetCreate(BaseModel):
    year: int = Field(ge=1)
    month: int = Field(ge=1, le=12)
    category_id: int | None = Field(default=None, gt=0)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class MonthlyBudgetUpdate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class MonthlyBudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    year: int
    month: int
    category_id: int | None
    category_name: str | None
    amount: Decimal
    spent: Decimal
    remaining: Decimal
    percentage_used: Decimal
    alert_threshold: int | None
    is_exceeded: bool
    created_at: datetime
    updated_at: datetime
