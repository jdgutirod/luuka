from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.exceptions import (
    AccountNotFoundError,
    IdempotencyKeyConflictError,
    InsufficientFundsError,
    SameAccountTransferError,
)
from app.models.account import Account
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, ReloadCreate


def reload_balance(db: Session, data: ReloadCreate, to_account_id: UUID, idempotency_key: str | None = None) -> Transaction:
    # Block account
    to_account = db.scalar(
        select(Account)
        .where(Account.id == to_account_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if to_account is None:
        raise AccountNotFoundError(to_account_id)

    # Idempotency: the lock on to_account serializes retries that use the same key
    if idempotency_key is not None:
        existing_transaction = db.scalar(
            select(Transaction).where(
                Transaction.type == TransactionType.RELOAD,
                Transaction.to_account_id == to_account_id,
                Transaction.idempotency_key == idempotency_key,
            )
        )
        if existing_transaction is not None:
            if existing_transaction.amount != data.amount:
                raise IdempotencyKeyConflictError(idempotency_key)
            return existing_transaction

    # Insertion
    new_transaction = Transaction(
        from_account_id=None,
        to_account_id=to_account.id,
        amount=data.amount,
        idempotency_key=idempotency_key,
        type=TransactionType.RELOAD,
    )
    db.add(new_transaction)

    # Update
    to_account.balance += data.amount

    # Atomic commit
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(new_transaction)
    return new_transaction


def transfer_balance(db: Session, data: TransactionCreate, from_account_id: UUID, idempotency_key: str | None = None) -> Transaction:
    # Validate accounts
    if from_account_id == data.to_account_id:
        raise SameAccountTransferError()

    # Block accounts
    accounts = db.scalars(
        select(Account)
        .where(Account.id.in_([from_account_id, data.to_account_id]))
        .order_by(Account.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).all()
    accounts_by_id = {account.id: account for account in accounts}

    from_account = accounts_by_id.get(from_account_id)
    to_account = accounts_by_id.get(data.to_account_id)
    if from_account is None:
        raise AccountNotFoundError(from_account_id)
    if to_account is None:
        raise AccountNotFoundError(data.to_account_id)

    # Idempotency: the lock on to_account serializes retries that use the same key
    if idempotency_key is not None:
        existing_transaction = db.scalar(
            select(Transaction).where(
                Transaction.from_account_id == from_account_id,
                Transaction.idempotency_key == idempotency_key,
            )
        )
        if existing_transaction is not None:
            if (
                existing_transaction.type != TransactionType.DIRECT_TRANSFER
                or existing_transaction.to_account_id != data.to_account_id
                or existing_transaction.amount != data.amount
            ):
                raise IdempotencyKeyConflictError(idempotency_key)
            return existing_transaction

    # Business Logic
    if from_account.balance < data.amount:
        raise InsufficientFundsError()

    # Insertion
    new_transaction = Transaction(
        from_account_id=from_account.id,
        to_account_id=to_account.id,
        amount=data.amount,
        idempotency_key=idempotency_key,
        type=TransactionType.DIRECT_TRANSFER,
    )
    db.add(new_transaction)

    # Update
    from_account.balance -= data.amount
    to_account.balance += data.amount

    # Atomic commit
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(new_transaction)
    return new_transaction
