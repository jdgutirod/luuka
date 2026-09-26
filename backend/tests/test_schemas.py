import uuid
import pytest
from pydantic import ValidationError
from app.schemas.group_charge import GroupChargeCreate


def test_group_charge_accepts_valid_members():
    members = [uuid.uuid4(), uuid.uuid4()]

    group_charge = GroupChargeCreate(name="Cancha sábado", total_amount=100_000, member_account_ids=members)

    assert group_charge.total_amount == 100_000
    assert group_charge.member_account_ids == members


def test_group_charge_requires_at_least_one_member():
    with pytest.raises(ValidationError):
        GroupChargeCreate(name="Cancha sábado", total_amount=100_000, member_account_ids=[])


def test_group_charge_rejects_repeated_members():
    member = uuid.uuid4()

    with pytest.raises(ValidationError, match="Los miembros no pueden repetirse"):
        GroupChargeCreate(name="Cancha sábado", total_amount=100_000, member_account_ids=[member, member])


def test_group_charge_rejects_total_smaller_than_one_peso_per_member():
    with pytest.raises(ValidationError, match="al menos 1 peso por miembro"):
        GroupChargeCreate(name="Cancha sábado", total_amount=1_000, member_account_ids=[uuid.uuid4() for _ in range(1_001)])


def test_group_charge_total_must_be_a_whole_peso_number():
    with pytest.raises(ValidationError):
        GroupChargeCreate(name="Cancha sábado", total_amount="100.000", member_account_ids=[uuid.uuid4()])
