import secrets
import string
from collections.abc import Sequence
from uuid import UUID
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from app.core.exceptions import (
    AccountNotFoundError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    PlateNotFoundError,
)
from app.core.security import DUMMY_HASH, create_access_token, hash_password, verify_password
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.account import AccountCreate

# No I or O, so they are not confused with 1 and 0
PLATE_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"
PLATE_ATTEMPTS = 5


def generate_plate() -> str:
    """Random plate like a Colombian car plate: 3 letters + 3 digits (e.g. KQX482)."""
    letters = "".join(secrets.choice(PLATE_LETTERS) for _ in range(3))
    digits = "".join(secrets.choice(string.digits) for _ in range(3))
    return letters + digits


def normalize_plate(plate: str) -> str:
    """Accepts the plate as people write it: 'kqx-482', 'KQX 482' or 'KQX482'."""
    return plate.replace("-", "").replace(" ", "").upper()


def create_account(db: Session, data: AccountCreate) -> Account:
    email = data.email.lower()

    # Validate email
    if _email_exists(db, email):
        raise EmailAlreadyRegisteredError(email)

    # Insertion, retrying with another plate if the generated one is already taken
    for _ in range(PLATE_ATTEMPTS):
        new_account = Account(
            owner_name=data.owner_name,
            email=email,
            plate=generate_plate(),
            password_hash=hash_password(data.password),
        )
        db.add(new_account)

        # Commit (the unique constraints on email and plate catch concurrent registrations)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            if _email_exists(db, email):
                raise EmailAlreadyRegisteredError(email)
            continue
        except Exception:
            db.rollback()
            raise
        db.refresh(new_account)
        return new_account

    raise RuntimeError("No se pudo generar una placa única para la cuenta")


def authenticate_account(db: Session, email: str, password: str) -> str:
    account = db.scalar(select(Account).where(Account.email == email.lower()))

    # Same error and similar response time whether the email exists or not
    if account is None:
        verify_password(password, DUMMY_HASH)
        raise InvalidCredentialsError()
    if not verify_password(password, account.password_hash):
        raise InvalidCredentialsError()

    return create_access_token(str(account.id))


def get_account_by_plate(db: Session, plate: str) -> Account:
    normalized_plate = normalize_plate(plate)
    account = db.scalar(select(Account).where(Account.plate == normalized_plate))
    if account is None:
        raise PlateNotFoundError(normalized_plate)
    return account


def get_balance(db: Session, account_id: UUID) -> int:
    balance = db.scalar(select(Account.balance).where(Account.id == account_id))
    if balance is None:
        raise AccountNotFoundError(account_id)
    return balance


def get_transaction_history(db: Session, account_id: UUID, limit: int = 20, offset: int = 0) -> Sequence[Transaction]:
    return db.scalars(
        select(Transaction)
        .where(or_(Transaction.from_account_id == account_id, Transaction.to_account_id == account_id))
        .options(selectinload(Transaction.from_account), selectinload(Transaction.to_account))
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()


def _email_exists(db: Session, email: str) -> bool:
    return db.scalar(select(Account.id).where(Account.email == email)) is not None
