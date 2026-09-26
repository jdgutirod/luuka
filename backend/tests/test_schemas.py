import uuid
from decimal import Decimal
import pytest
from pydantic import ValidationError
from app.schemas.group_charge import GroupChargeCreate


def test_group_charge_accepts_member_amounts_that_add_up_to_total():
    group_charge = GroupChargeCreate(
        name="Cancha sábado",
        total_amount="100.00",
        member_charges=[
            {"account_id": uuid.uuid4(), "assigned_amount": "60"},
            {"account_id": uuid.uuid4(), "assigned_amount": "40"},
        ],
    )

    assert group_charge.total_amount == Decimal("100")


def test_group_charge_rejects_member_amounts_that_do_not_add_up():
    with pytest.raises(ValidationError, match="La suma de los montos asignados debe ser igual al monto total"):
        GroupChargeCreate(
            name="Cancha sábado",
            total_amount="100",
            member_charges=[{"account_id": uuid.uuid4(), "assigned_amount": "50"}],
        )


def test_group_charge_requires_at_least_one_member():
    with pytest.raises(ValidationError):
        GroupChargeCreate(name="Cancha sábado", total_amount="100", member_charges=[])
