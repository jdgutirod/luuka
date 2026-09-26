from typing import Annotated
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_account
from app.db.database import get_db
from app.models.account import Account
from app.schemas.transaction import ReloadCreate, TransactionCreate, TransactionResponse
from app.services.transactions import reload_balance, transfer_balance

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/reloads", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_reload(
    data: ReloadCreate,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
    idempotency_key: Annotated[str | None, Header(max_length=255)] = None,
):
    """Reload balance into the current account."""
    return reload_balance(db, data, current_account.id, idempotency_key)

@router.post("/transfers", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(
    data: TransactionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
    idempotency_key: Annotated[str | None, Header(max_length=255)] = None,
):
    """Transfer balance from the current account to another account."""
    return transfer_balance(db, data, current_account.id, idempotency_key)
