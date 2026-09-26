from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_account
from app.db.database import get_db
from app.models.account import Account
from app.models.enums import ChargeState
from app.schemas.member_charge import MyMemberChargeResponse
from app.services.member_charges import get_member_charges, pay_member_charge

router = APIRouter(prefix="/group-charges/member-charges", tags=["member charges"])

@router.get("/me", response_model=list[MyMemberChargeResponse])
def read_my_member_charges(
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
    state: ChargeState | None = None,
):
    """List the member charges assigned to the current account, optionally filtered by state."""
    return get_member_charges(db, current_account.id, state)

@router.post("/{member_charge_id}/pay", response_model=MyMemberChargeResponse)
def pay_my_member_charge(
    member_charge_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
):
    """Pay a member charge of the current account. The money goes to the group charge creator."""
    return pay_member_charge(db, member_charge_id, current_account.id)
