from pydantic import BaseModel, ConfigDict, EmailStr, Field
from decimal import Decimal
from uuid import UUID
from datetime import datetime

class AccountBase(BaseModel):
    owner_name: str = Field(..., max_length=100)
    email: EmailStr

class AccountCreate(AccountBase):
    pass

class AccountResponse(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    balance: Decimal
    created_at: datetime
