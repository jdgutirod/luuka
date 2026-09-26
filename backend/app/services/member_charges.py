from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.core.exceptions import InsufficientFundsError, MemberChargeNotFoundError
from app.models.account import Account
from app.models.enums import ChargeState, TransactionType
from app.models.group_charge import GroupCharge
from app.models.member_charge import MemberCharge
from app.models.transaction import Transaction
from app.services.group_charges import complete_if_fully_paid


def get_member_charges(db: Session, account_id: UUID, state: ChargeState | None = None) -> Sequence[MemberCharge]:
    query = (
        select(MemberCharge)
        .join(MemberCharge.group_charge)
        .where(MemberCharge.account_id == account_id)
        .options(
            selectinload(MemberCharge.account),
            selectinload(MemberCharge.group_charge).selectinload(GroupCharge.creator),
        )
        .order_by(GroupCharge.created_at.desc(), MemberCharge.id)
    )
    if state is not None:
        query = query.where(MemberCharge.state == state)
    return db.scalars(query).all()


def pay_member_charge(db: Session, member_charge_id: UUID, account_id: UUID) -> MemberCharge:
    member_charge = db.get(MemberCharge, member_charge_id)
    if member_charge is None or member_charge.account_id != account_id:
        raise MemberChargeNotFoundError(member_charge_id)

    # Block rows always in the same order to avoid deadlocks: group charge -> member charge -> accounts (by id).
    # Locking the group charge makes payments of the same group run one at a time, so the last one sees all others.
    group_charge = db.scalar(
        select(GroupCharge)
        .where(GroupCharge.id == member_charge.group_charge_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    member_charge = db.scalar(
        select(MemberCharge)
        .where(MemberCharge.id == member_charge_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )

    # Paying twice is harmless: a retry gets the already paid charge back without charging again
    if member_charge.state == ChargeState.COMPLETED:
        return member_charge

    accounts = db.scalars(
        select(Account)
        .where(Account.id.in_([account_id, group_charge.creator_id]))
        .order_by(Account.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).all()
    accounts_by_id = {account.id: account for account in accounts}
    payer_account = accounts_by_id[account_id]
    creator_account = accounts_by_id[group_charge.creator_id]

    # Business Logic
    if payer_account.balance < member_charge.assigned_amount:
        raise InsufficientFundsError()

    # Insertion: the member pays the creator, who paid for the court
    new_transaction = Transaction(
        from_account_id=payer_account.id,
        to_account_id=creator_account.id,
        amount=member_charge.assigned_amount,
        type=TransactionType.COURT_PAYMENT,
    )
    db.add(new_transaction)

    # Update
    payer_account.balance -= member_charge.assigned_amount
    creator_account.balance += member_charge.assigned_amount
    member_charge.transaction = new_transaction
    member_charge.state = ChargeState.COMPLETED
    member_charge.paid_at = datetime.now(timezone.utc)

    # Atomic commit, completing the group charge when this was the last unpaid member charge
    try:
        db.flush()
        complete_if_fully_paid(db, group_charge)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(member_charge)
    return member_charge
