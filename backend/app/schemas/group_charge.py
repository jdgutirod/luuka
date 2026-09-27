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
    creator_plays: bool = Field(
        False,
        description="Si el creador también jugó: el total se divide entre los miembros y él, y su parte no se le cobra a nadie",
    )

    @model_validator(mode="after")
    def validate_members(self):
        if len(set(self.member_account_ids)) != len(self.member_account_ids):
            raise ValueError("Los miembros no pueden repetirse")
        parts = len(self.member_account_ids) + (1 if self.creator_plays else 0)
        if self.total_amount < parts:
            raise ValueError("El monto total debe alcanzar al menos 1 peso por miembro")
        return self

class GroupChargeResponse(GroupChargeBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    total_amount: int
    creator_share: int = Field(..., description="Parte del total que pone el creador porque también jugó (0 si no jugó). No se cobra")
    state: ChargeState
    creator: AccountPublic
    created_at: datetime
    member_charges: list[MemberChargeResponse] = []
