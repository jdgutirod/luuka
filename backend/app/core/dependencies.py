from typing import Annotated
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.account import Account

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="accounts/login")

def get_current_account(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Account:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    subject = decode_access_token(token)
    if subject is None:
        raise credentials_exception

    try:
        account_id = UUID(subject)
    except ValueError:
        raise credentials_exception

    account = db.get(Account, account_id)
    if account is None:
        raise credentials_exception
    return account
