from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_account
from app.db.database import get_db
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountResponse, BalanceResponse
from app.schemas.auth import Token
from app.schemas.transaction import TransactionResponse
from app.services.accounts import authenticate_account, create_account, get_balance, get_transaction_history

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def register_account(
    data: AccountCreate,
    db: Annotated[Session, Depends(get_db)],
):
    """Create a new account with zero balance."""
    return create_account(db, data)

@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    """Authenticate with email (sent as `username`) and password, and get an access token."""
    access_token = authenticate_account(db, form_data.username, form_data.password)
    return Token(access_token=access_token)

@router.get("/me/balance", response_model=BalanceResponse)
def read_balance(
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
):
    """Get the current account balance."""
    return BalanceResponse(account_id=current_account.id, balance=get_balance(db, current_account.id))

@router.get("/me/transactions", response_model=list[TransactionResponse])
def read_transaction_history(
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List the transactions sent or received by the current account, newest first."""
    return get_transaction_history(db, current_account.id, limit, offset)
