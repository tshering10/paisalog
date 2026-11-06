import csv
import io
from collections.abc import Iterator
from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import DbSession, VerifiedCurrentUser
from app.schemas.common import Page
from app.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionType,
    TransactionUpdate,
)
from app.services.transactions import (
    InvalidTransactionCategoryError,
    InvalidTransactionFilterError,
    TransactionNotFoundError,
    create_transaction,
    delete_transaction,
    export_transactions,
    get_transaction,
    list_transactions,
    sanitize_csv_cell,
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
    current_user: VerifiedCurrentUser,
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
    current_user: VerifiedCurrentUser,
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
    cursor: str | None = None,
) -> Page[TransactionRead]:
    try:
        transactions, total, next_cursor = list_transactions(
            db,
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            transaction_type=transaction_type,
            category_id=category_id,
            date_from=date_from,
            date_to=date_to,
            cursor=cursor,
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
        next_cursor=next_cursor,
    )


@router.get(
    "/export.csv",
    response_class=StreamingResponse,
    summary="Export the user's filtered transactions as CSV",
)
def export_transactions_endpoint(
    current_user: VerifiedCurrentUser,
    db: DbSession,
    transaction_type: Annotated[
        TransactionType | None,
        Query(alias="type"),
    ] = None,
    category_id: Annotated[int | None, Query(gt=0)] = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> StreamingResponse:
    try:
        transactions = export_transactions(
            db,
            user_id=current_user.id,
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

    def csv_rows() -> Iterator[str]:
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(["date", "type", "category", "amount", "description"])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        for transaction in transactions:
            writer.writerow(
                [
                    transaction.transaction_date.isoformat(),
                    transaction.type,
                    sanitize_csv_cell(transaction.category.name),
                    f"{transaction.amount:.2f}",
                    sanitize_csv_cell(transaction.description),
                ]
            )
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    filename = "transactions.csv"
    return StreamingResponse(
        csv_rows(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Get one of the user's transactions",
)
def get_transaction_endpoint(
    transaction_id: int,
    current_user: VerifiedCurrentUser,
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
    current_user: VerifiedCurrentUser,
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
    current_user: VerifiedCurrentUser,
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
