from pydantic import BaseModel, ConfigDict, EmailStr, Field
from uuid import UUID
from datetime import datetime

class AccountBase(BaseModel):
    owner_name: str = Field(..., max_length=100)
    email: EmailStr

class AccountCreate(AccountBase):
    password: str = Field(..., min_length=8, max_length=128, description="La contraseña debe tener al menos 8 caracteres")

class AccountResponse(AccountBase):
    """Private data of the current account."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plate: str
    balance: int
    created_at: datetime

class AccountPublic(BaseModel):
    """What other people can see of an account: never the email or the balance."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_name: str
    plate: str

class BalanceResponse(BaseModel):
    account_id: UUID
    balance: int
