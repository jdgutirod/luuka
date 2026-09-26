from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_account
from app.db.database import get_db
from app.models.account import Account
from app.models.enums import ChargeState
from app.schemas.group_charge import GroupChargeCreate, GroupChargeResponse
from app.services.group_charges import create_group_charge, get_created_group_charges, get_group_charge

router = APIRouter(prefix="/group-charges", tags=["group charges"])

@router.post("", response_model=GroupChargeResponse, status_code=status.HTTP_201_CREATED)
def register_group_charge(
    data: GroupChargeCreate,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
    idempotency_key: Annotated[str | None, Header(max_length=255)] = None,
):
    """Create a group charge. The total is split equally into one member charge per member."""
    return create_group_charge(db, data, current_account.id, idempotency_key)

# Declared before /{group_charge_id}, otherwise "created" would be read as a group charge id
@router.get("/created", response_model=list[GroupChargeResponse])
def read_created_group_charges(
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
    state: ChargeState | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List the group charges created by the current account, newest first, with who has paid."""
    return get_created_group_charges(db, current_account.id, state, limit, offset)

@router.get("/{group_charge_id}", response_model=GroupChargeResponse)
def read_group_charge(
    group_charge_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
):
    """Get a group charge with its member charges. Only visible to its creator and members."""
    return get_group_charge(db, group_charge_id, current_account.id)
