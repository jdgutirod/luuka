from pydantic import BaseModel, ConfigDict, Field, model_validator
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from app.models.enums import ChargeState
from app.schemas.member_charge import MemberChargeCreate, MemberChargeResponse

class GroupChargeBase(BaseModel):
    name: str = Field(..., max_length=100)
    total_amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2, description="El monto total debe ser mayor a cero")

class GroupChargeCreate(GroupChargeBase):
    member_charges: list[MemberChargeCreate] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_amounts(self):
        if sum(m.assigned_amount for m in self.member_charges) != self.total_amount:
            raise ValueError("La suma de los montos asignados debe ser igual al monto total")
        return self

class GroupChargeResponse(GroupChargeBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    creator_id: UUID
    state: ChargeState
    created_at: datetime
    member_charges: list[MemberChargeResponse] = []
