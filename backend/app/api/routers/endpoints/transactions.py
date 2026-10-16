from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import Page
from app.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionType,
    TransactionUpdate,
)
from app.services.transactions import (
    InvalidTransactionFilterError,
    InvalidTransactionCategoryError,
    TransactionNotFoundError,
    create_transaction,
    delete_transaction,
    get_transaction,
    list_transactions,
    update_transaction,
)


router = APIRouter(
    prefix="/api/v1/transactions",
    tags=["transactions"],
)


@router.post(
    "",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a transaction",
)
def create_transaction_endpoint(
    transaction_data: TransactionCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> TransactionRead:
    try:
        transaction = create_transaction(
            db,
            user_id=current_user.id,
            category_id=transaction_data.category_id,
            transaction_type=transaction_data.type,
            amount=transaction_data.amount,
            transaction_date=transaction_data.transaction_date,
            description=transaction_data.description,
        )
    except InvalidTransactionCategoryError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category is unavailable or does not match the transaction type",
        ) from None

    transaction = get_transaction(
        db,
        transaction_id=transaction.id,
        user_id=current_user.id,
    )
    return TransactionRead.model_validate(transaction)


@router.get(
    "",
    response_model=Page[TransactionRead],
    summary="List the user's transactions",
)
def list_transaction_endpoint(
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    transaction_type: Annotated[
        TransactionType | None,
        Query(alias="type"),
    ] = None,
    category_id: Annotated[int | None, Query(gt=0)] = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Page[TransactionRead]:
    try:
        transactions, total = list_transactions(
            db,
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            transaction_type=transaction_type,
            category_id=category_id,
            date_from=date_from,
            date_to=date_to,
        )
    except InvalidTransactionFilterError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from must be earlier than or equal to date_to",
        ) from None
    return Page[TransactionRead](
        items=[TransactionRead.model_validate(item) for item in transactions],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Get one of the user's transactions",
)
def get_transaction_endpoint(
    transaction_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> TransactionRead:
    try:
        transaction = get_transaction(
            db,
            transaction_id=transaction_id,
            user_id=current_user.id,
        )
    except TransactionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        ) from None

    return TransactionRead.model_validate(transaction)


@router.patch(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Update one of the user's transactions",
)
def update_transaction_endpoint(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> TransactionRead:
    try:
        transaction = update_transaction(
            db,
            transaction_id=transaction_id,
            user_id=current_user.id,
            changes=transaction_data.model_dump(exclude_unset=True),
        )
    except TransactionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        ) from None
    except InvalidTransactionCategoryError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category is unavailable or does not match the transaction type",
        ) from None

    return TransactionRead.model_validate(transaction)


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete one of the user's transactions",
)
def delete_transaction_endpoint(
    transaction_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    try:
        delete_transaction(
            db,
            transaction_id=transaction_id,
            user_id=current_user.id,
        )
    except TransactionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        ) from None
