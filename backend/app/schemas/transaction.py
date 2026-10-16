from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


TransactionType = Literal["income", "expense"]


class TransactionCreate(BaseModel):
    category_id: int = Field(gt=0)
    type: TransactionType
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    transaction_date: date
    description: str | None = Field(default=None, max_length=500)


class TransactionUpdate(BaseModel):
    category_id: int | None = Field(default=None, gt=0)
    type: TransactionType | None = None
    amount: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )
    transaction_date: date | None = None
    description: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def require_update_field(self) -> "TransactionUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        return self


class CategorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: TransactionType


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    type: TransactionType
    amount: Decimal
    transaction_date: date
    description: str | None
    created_at: datetime
    updated_at: datetime
    category: CategorySummary
