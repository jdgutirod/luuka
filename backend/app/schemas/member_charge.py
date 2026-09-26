from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from app.models.enums import ChargeState

class MemberChargeCreate(BaseModel):
    account_id: UUID
    assigned_amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2, description="El monto asignado debe ser mayor a cero")

class MemberChargeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    group_charge_id: UUID
    transaction_id: UUID | None = None
    assigned_amount: Decimal
    state: ChargeState
    paid_at: datetime | None = None
