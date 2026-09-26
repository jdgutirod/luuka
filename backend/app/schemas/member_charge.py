from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from app.models.enums import ChargeState
from app.schemas.account import AccountPublic

class MemberChargeResponse(BaseModel):
    """A member charge as shown inside its group charge."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account: AccountPublic
    assigned_amount: int
    state: ChargeState
    paid_at: datetime | None = None
    transaction_id: UUID | None = None

class MemberChargeGroup(BaseModel):
    """The group charge a member charge belongs to: what the court is and who to pay."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    total_amount: int
    state: ChargeState
    creator: AccountPublic
    created_at: datetime

class MyMemberChargeResponse(MemberChargeResponse):
    """A member charge as shown to the member who has to pay it."""
    group_charge: MemberChargeGroup
