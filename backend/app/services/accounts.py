from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.exceptions import AccountNotFoundError, EmailAlreadyRegisteredError, InvalidCredentialsError
from app.core.security import DUMMY_HASH, create_access_token, hash_password, verify_password
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.account import AccountCreate


def create_account(db: Session, data: AccountCreate) -> Account:
    email = data.email.lower()

    # Validate email
    if db.scalar(select(Account.id).where(Account.email == email)) is not None:
        raise EmailAlreadyRegisteredError(email)

    # Insertion
    new_account = Account(
        owner_name=data.owner_name,
        email=email,
        password_hash=hash_password(data.password),
    )
    db.add(new_account)

    # Commit (the unique constraint on email catches concurrent registrations)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise EmailAlreadyRegisteredError(email)
    except Exception:
        db.rollback()
        raise
    db.refresh(new_account)
    return new_account


def authenticate_account(db: Session, email: str, password: str) -> str:
    account = db.scalar(select(Account).where(Account.email == email.lower()))

    # Same error and similar response time whether the email exists or not
    if account is None:
        verify_password(password, DUMMY_HASH)
        raise InvalidCredentialsError()
    if not verify_password(password, account.password_hash):
        raise InvalidCredentialsError()

    return create_access_token(str(account.id))


def get_balance(db: Session, account_id: UUID) -> Decimal:
    balance = db.scalar(select(Account.balance).where(Account.id == account_id))
    if balance is None:
        raise AccountNotFoundError(account_id)
    return balance


def get_transaction_history(db: Session, account_id: UUID, limit: int = 20, offset: int = 0) -> Sequence[Transaction]:
    return db.scalars(
        select(Transaction)
        .where(or_(Transaction.from_account_id == account_id, Transaction.to_account_id == account_id))
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
