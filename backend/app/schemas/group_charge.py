from pydantic import BaseModel, ConfigDict, Field, model_validator
from uuid import UUID
from datetime import datetime
from app.models.enums import ChargeState
from app.schemas.account import AccountPublic
from app.schemas.member_charge import MemberChargeResponse
from app.schemas.types import AmountCOP

class GroupChargeBase(BaseModel):
    name: str = Field(..., max_length=100)

class GroupChargeCreate(GroupChargeBase):
    total_amount: AmountCOP = Field(..., description="Monto total en pesos colombianos enteros")
    member_account_ids: list[UUID] = Field(..., min_length=1, description="Cuentas entre las que se divide el total en partes iguales")

    @model_validator(mode="after")
    def validate_members(self):
        if len(set(self.member_account_ids)) != len(self.member_account_ids):
            raise ValueError("Los miembros no pueden repetirse")
        if self.total_amount < len(self.member_account_ids):
            raise ValueError("El monto total debe alcanzar al menos 1 peso por miembro")
        return self

class GroupChargeResponse(GroupChargeBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    total_amount: int
    state: ChargeState
    creator: AccountPublic
    created_at: datetime
    member_charges: list[MemberChargeResponse] = []
