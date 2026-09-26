from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from app.models.enums import TransactionType
from app.schemas.account import AccountPublic
from app.schemas.types import AmountCOP

class ReloadCreate(BaseModel):
    amount: AmountCOP = Field(..., description="Monto de la recarga en pesos colombianos enteros")

class TransactionCreate(BaseModel):
    to_account_id: UUID
    amount: AmountCOP = Field(..., description="Monto a transferir en pesos colombianos enteros")

class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: TransactionType
    amount: int
    from_account: AccountPublic | None = None
    to_account: AccountPublic | None = None
    created_at: datetime
