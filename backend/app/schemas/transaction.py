from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from app.models.enums import TransactionType

class ReloadCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2, description="El monto de recarga debe ser mayor a cero")

class TransactionCreate(BaseModel):
    to_account_id: UUID
    amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2, description="El monto a transferir debe ser mayor a cero")

class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    from_account_id: UUID | None = None
    to_account_id: UUID | None = None
    amount: Decimal
    type: TransactionType
    created_at: datetime
