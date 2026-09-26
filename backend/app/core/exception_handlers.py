from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions import (
    AccountNotFoundError,
    CreatorCannotBeMemberError,
    DomainError,
    EmailAlreadyRegisteredError,
    GroupChargeNotFoundError,
    IdempotencyKeyConflictError,
    InsufficientFundsError,
    InvalidCredentialsError,
    MemberChargeNotFoundError,
    PlateNotFoundError,
    SameAccountTransferError,
)

STATUS_CODES: dict[type[DomainError], int] = {
    AccountNotFoundError: status.HTTP_404_NOT_FOUND,
    PlateNotFoundError: status.HTTP_404_NOT_FOUND,
    GroupChargeNotFoundError: status.HTTP_404_NOT_FOUND,
    MemberChargeNotFoundError: status.HTTP_404_NOT_FOUND,
    EmailAlreadyRegisteredError: status.HTTP_409_CONFLICT,
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    SameAccountTransferError: status.HTTP_400_BAD_REQUEST,
    CreatorCannotBeMemberError: status.HTTP_400_BAD_REQUEST,
    InsufficientFundsError: status.HTTP_400_BAD_REQUEST,
    IdempotencyKeyConflictError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}

async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    status_code = STATUS_CODES.get(type(exc), status.HTTP_400_BAD_REQUEST)
    headers = {"WWW-Authenticate": "Bearer"} if status_code == status.HTTP_401_UNAUTHORIZED else None
    return JSONResponse(status_code=status_code, content={"detail": str(exc)}, headers=headers)

def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)
