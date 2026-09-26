from pydantic import BaseModel, ConfigDict, EmailStr, Field
from decimal import Decimal
from uuid import UUID
from datetime import datetime

class AccountBase(BaseModel):
    owner_name: str = Field(..., max_length=100)
    email: EmailStr

class AccountCreate(AccountBase):
    password: str = Field(..., min_length=8, max_length=128, description="La contraseña debe tener al menos 8 caracteres")

class AccountResponse(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    balance: Decimal
    created_at: datetime

class BalanceResponse(BaseModel):
    account_id: UUID
    balance: Decimal
