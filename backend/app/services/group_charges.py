from collections.abc import Sequence
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from app.core.exceptions import (
    AccountNotFoundError,
    CreatorCannotBeMemberError,
    GroupChargeNotFoundError,
    IdempotencyKeyConflictError,
)
from app.models.account import Account
from app.models.enums import ChargeState
from app.models.group_charge import GroupCharge
from app.models.member_charge import MemberCharge
from app.schemas.group_charge import GroupChargeCreate

# Loads the creator and each member's account in a few queries, instead of one query per person
_WITH_PEOPLE = [
    selectinload(GroupCharge.creator),
    selectinload(GroupCharge.member_charges).selectinload(MemberCharge.account),
]

def split_amount(total: int, parts: int) -> list[int]:
    """Splits the total (whole pesos) into equal parts. Leftover pesos go one by one to the first parts."""
    base, leftover = divmod(total, parts)
    return [base + 1 if index < leftover else base for index in range(parts)]


def split_member_amounts(total: int, members: int, creator_plays: bool) -> list[int]:
    """What each member is charged.

    When the creator also played, the total is split among the members and the creator, and the creator's part
    is not charged. The leftover pesos stay in the creator's part, so no member pays more than an equal part.
    """
    if creator_plays:
        return [total // (members + 1)] * members
    return split_amount(total, members)


def create_group_charge(
    db: Session,
    data: GroupChargeCreate,
    creator_id: UUID,
    idempotency_key: str | None = None,
) -> GroupCharge:
    # Validate members
    if creator_id in data.member_account_ids:
        raise CreatorCannotBeMemberError()

    if idempotency_key is not None:
        existing_group_charge = _find_by_idempotency_key(db, creator_id, idempotency_key)
        if existing_group_charge is not None:
            return _ensure_same_request(existing_group_charge, data, idempotency_key)

    existing_account_ids = set(db.scalars(select(Account.id).where(Account.id.in_(data.member_account_ids))).all())
    for account_id in data.member_account_ids:
        if account_id not in existing_account_ids:
            raise AccountNotFoundError(account_id)

    # Insertion: one member charge per member, splitting the total equally (the creator's part, if any, is not charged)
    new_group_charge = GroupCharge(
        name=data.name,
        total_amount=data.total_amount,
        creator_id=creator_id,
        idempotency_key=idempotency_key,
    )
    amounts = split_member_amounts(data.total_amount, len(data.member_account_ids), data.creator_plays)
    new_group_charge.member_charges = [
        MemberCharge(account_id=account_id, assigned_amount=amount)
        for account_id, amount in zip(data.member_account_ids, amounts)
    ]
    db.add(new_group_charge)

    # Atomic commit
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # A concurrent retry with the same idempotency key was saved first
        if idempotency_key is not None:
            existing_group_charge = _find_by_idempotency_key(db, creator_id, idempotency_key)
            if existing_group_charge is not None:
                return _ensure_same_request(existing_group_charge, data, idempotency_key)
        raise
    except Exception:
        db.rollback()
        raise
    db.refresh(new_group_charge)
    return new_group_charge


def get_group_charge(db: Session, group_charge_id: UUID, account_id: UUID) -> GroupCharge:
    """Only the creator and the members can see a group charge."""
    group_charge = db.get(GroupCharge, group_charge_id, options=_WITH_PEOPLE)
    if group_charge is None:
        raise GroupChargeNotFoundError(group_charge_id)

    is_member = any(member_charge.account_id == account_id for member_charge in group_charge.member_charges)
    if group_charge.creator_id != account_id and not is_member:
        raise GroupChargeNotFoundError(group_charge_id)
    return group_charge


def get_created_group_charges(
    db: Session,
    creator_id: UUID,
    state: ChargeState | None = None,
    limit: int = 20,
    offset: int = 0,
) -> Sequence[GroupCharge]:
    query = (
        select(GroupCharge)
        .where(GroupCharge.creator_id == creator_id)
        .options(*_WITH_PEOPLE)
        .order_by(GroupCharge.created_at.desc(), GroupCharge.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if state is not None:
        query = query.where(GroupCharge.state == state)
    return db.scalars(query).all()


def complete_if_fully_paid(db: Session, group_charge: GroupCharge) -> None:
    """Marks the group charge as completed when none of its member charges is left unpaid.

    Runs inside the caller's transaction: the group charge must be locked and pending changes flushed.
    It does not commit.
    """
    unpaid_count = db.scalar(
        select(func.count())
        .select_from(MemberCharge)
        .where(
            MemberCharge.group_charge_id == group_charge.id,
            MemberCharge.state != ChargeState.COMPLETED,
        )
    )
    if unpaid_count == 0:
        group_charge.state = ChargeState.COMPLETED


def _find_by_idempotency_key(db: Session, creator_id: UUID, idempotency_key: str) -> GroupCharge | None:
    return db.scalar(
        select(GroupCharge).where(
            GroupCharge.creator_id == creator_id,
            GroupCharge.idempotency_key == idempotency_key,
        )
    )


def _ensure_same_request(group_charge: GroupCharge, data: GroupChargeCreate, idempotency_key: str) -> GroupCharge:
    member_account_ids = {member_charge.account_id for member_charge in group_charge.member_charges}
    if (
        group_charge.name != data.name
        or group_charge.total_amount != data.total_amount
        or member_account_ids != set(data.member_account_ids)
        or (group_charge.creator_share > 0) != data.creator_plays
    ):
        raise IdempotencyKeyConflictError(idempotency_key)
    return group_charge
