import uuid
import pytest
from sqlalchemy import func, select
from app.core.config import MAX_TRANSACTION_AMOUNT, MIN_TRANSACTION_AMOUNT
from app.models.group_charge import GroupCharge
from app.services.group_charges import split_amount
from tests.conftest import member_charge_of


# Equal split

@pytest.mark.parametrize(
    ("total", "parts", "expected"),
    [
        (120_000, 4, [30_000, 30_000, 30_000, 30_000]),
        (100_000, 3, [33_334, 33_333, 33_333]),
        (10_000, 6, [1_667, 1_667, 1_667, 1_667, 1_666, 1_666]),
        (3, 3, [1, 1, 1]),
        (50_000, 1, [50_000]),
    ],
)
def test_split_amount_divides_equally_and_adds_up_to_total(total, parts, expected):
    amounts = split_amount(total, parts)

    assert amounts == expected
    assert sum(amounts) == total


# Create group charge

def test_create_group_charge_generates_one_pending_member_charge_per_member(client, make_account, create_group_charge):
    creator_id, creator_headers = make_account("organizador@mail.com")
    ana_id, _ = make_account("ana@mail.com")
    beto_id, _ = make_account("beto@mail.com")
    carla_id, _ = make_account("carla@mail.com")

    response = create_group_charge(creator_headers, 100_000, [ana_id, beto_id, carla_id])

    assert response.status_code == 201
    group_charge = response.json()
    assert group_charge["creator"]["id"] == creator_id
    assert group_charge["state"] == "PENDING"
    assert group_charge["total_amount"] == 100_000
    assert {m["account"]["id"] for m in group_charge["member_charges"]} == {ana_id, beto_id, carla_id}
    assert all(m["state"] == "PENDING" and m["transaction_id"] is None for m in group_charge["member_charges"])
    assert member_charge_of(group_charge, ana_id)["assigned_amount"] == 33_334
    assert member_charge_of(group_charge, beto_id)["assigned_amount"] == 33_333
    assert sum(m["assigned_amount"] for m in group_charge["member_charges"]) == 100_000


def test_create_group_charge_does_not_move_money(client, make_account, create_group_charge, balance_of):
    _, creator_headers = make_account("organizador@mail.com", balance=10_000)
    ana_id, ana_headers = make_account("ana@mail.com", balance=10_000)

    create_group_charge(creator_headers, 100_000, [ana_id])

    assert balance_of(creator_headers) == 10_000
    assert balance_of(ana_headers) == 10_000


def test_create_group_charge_with_creator_as_member_returns_400(make_account, create_group_charge):
    creator_id, creator_headers = make_account("organizador@mail.com")
    ana_id, _ = make_account("ana@mail.com")

    response = create_group_charge(creator_headers, 100_000, [ana_id, creator_id])

    assert response.status_code == 400
    assert response.json()["detail"] == "El creador del cobro grupal no puede estar entre los miembros"


def test_create_group_charge_with_unknown_member_returns_404(make_account, create_group_charge):
    _, creator_headers = make_account("organizador@mail.com")
    ana_id, _ = make_account("ana@mail.com")
    unknown_id = str(uuid.uuid4())

    response = create_group_charge(creator_headers, 100_000, [ana_id, unknown_id])

    assert response.status_code == 404
    assert response.json()["detail"] == f"La cuenta {unknown_id} no existe"


@pytest.mark.parametrize(
    "total_amount",
    [0, MIN_TRANSACTION_AMOUNT - 1, MAX_TRANSACTION_AMOUNT + 1, 100_000.5, "100000", "100.000"],
)
def test_create_group_charge_with_invalid_total_returns_422(make_account, create_group_charge, total_amount):
    _, creator_headers = make_account("organizador@mail.com")
    ana_id, _ = make_account("ana@mail.com")

    response = create_group_charge(creator_headers, total_amount, [ana_id])

    assert response.status_code == 422


def test_create_group_charge_requires_authentication(client):
    response = client.post("/group-charges", json={"name": "Cancha", "total_amount": 100_000, "member_account_ids": [str(uuid.uuid4())]})

    assert response.status_code == 401


def test_create_group_charge_retry_with_same_idempotency_key_creates_it_once(make_account, create_group_charge, session_factory):
    _, creator_headers = make_account("organizador@mail.com")
    ana_id, _ = make_account("ana@mail.com")
    headers_with_key = {**creator_headers, "Idempotency-Key": "cancha-1"}

    first = create_group_charge(headers_with_key, 100_000, [ana_id])
    retry = create_group_charge(headers_with_key, 100_000, [ana_id])

    assert first.status_code == retry.status_code == 201
    assert first.json()["id"] == retry.json()["id"]
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(GroupCharge)) == 1


def test_create_group_charge_same_idempotency_key_with_other_data_returns_422(make_account, create_group_charge):
    _, creator_headers = make_account("organizador@mail.com")
    ana_id, _ = make_account("ana@mail.com")
    beto_id, _ = make_account("beto@mail.com")
    headers_with_key = {**creator_headers, "Idempotency-Key": "cancha-1"}
    create_group_charge(headers_with_key, 100_000, [ana_id])

    other_total = create_group_charge(headers_with_key, 120_000, [ana_id])
    other_members = create_group_charge(headers_with_key, 100_000, [ana_id, beto_id])

    assert other_total.status_code == other_members.status_code == 422


# Read group charges

def test_group_charge_is_visible_to_creator_and_members_only(client, make_account, create_group_charge):
    _, creator_headers = make_account("organizador@mail.com")
    ana_id, ana_headers = make_account("ana@mail.com")
    _, outsider_headers = make_account("otro@mail.com")
    group_charge_id = create_group_charge(creator_headers, 100_000, [ana_id]).json()["id"]

    as_creator = client.get(f"/group-charges/{group_charge_id}", headers=creator_headers)
    as_member = client.get(f"/group-charges/{group_charge_id}", headers=ana_headers)
    as_outsider = client.get(f"/group-charges/{group_charge_id}", headers=outsider_headers)

    assert as_creator.status_code == as_member.status_code == 200
    assert as_creator.json()["id"] == group_charge_id
    assert as_outsider.status_code == 404


def test_unknown_group_charge_returns_404(client, make_account):
    _, headers = make_account("ana@mail.com")

    response = client.get(f"/group-charges/{uuid.uuid4()}", headers=headers)

    assert response.status_code == 404


def test_group_charge_shows_creator_and_members_names_and_plates(client, make_account, plate_of, create_group_charge):
    _, creator_headers = make_account("organizador@mail.com")
    ana_id, ana_headers = make_account("ana@mail.com")
    group_charge = create_group_charge(creator_headers, 60_000, [ana_id]).json()

    detail = client.get(f"/group-charges/{group_charge['id']}", headers=ana_headers).json()

    assert detail["creator"]["owner_name"] == "organizador"
    assert detail["creator"]["plate"] == plate_of(creator_headers)
    assert detail["member_charges"][0]["account"] == {"id": ana_id, "owner_name": "ana", "plate": plate_of(ana_headers)}


# Group charges created by me

def test_created_group_charges_lists_only_mine_newest_first(client, make_account, create_group_charge):
    _, creator_headers = make_account("organizador@mail.com")
    ana_id, ana_headers = make_account("ana@mail.com")
    create_group_charge(creator_headers, 40_000, [ana_id])
    create_group_charge(creator_headers, 60_000, [ana_id])

    as_creator = client.get("/group-charges/created", headers=creator_headers)
    as_member = client.get("/group-charges/created", headers=ana_headers)

    assert as_creator.status_code == 200
    assert [g["total_amount"] for g in as_creator.json()] == [60_000, 40_000]
    assert as_creator.json()[0]["member_charges"][0]["account"]["owner_name"] == "ana"
    assert as_member.json() == []


def test_created_group_charges_filters_by_state_and_paginates(client, make_account, create_group_charge):
    _, creator_headers = make_account("organizador@mail.com")
    ana_id, ana_headers = make_account("ana@mail.com", balance=100_000)
    paid = create_group_charge(creator_headers, 10_000, [ana_id]).json()
    create_group_charge(creator_headers, 20_000, [ana_id])
    create_group_charge(creator_headers, 30_000, [ana_id])
    client.post(f"/group-charges/member-charges/{member_charge_of(paid, ana_id)['id']}/pay", headers=ana_headers)

    completed = client.get("/group-charges/created?state=COMPLETED", headers=creator_headers).json()
    pending = client.get("/group-charges/created?state=PENDING", headers=creator_headers).json()
    second_page = client.get("/group-charges/created?limit=2&offset=2", headers=creator_headers).json()

    assert [g["total_amount"] for g in completed] == [10_000]
    assert [g["total_amount"] for g in pending] == [30_000, 20_000]
    assert [g["total_amount"] for g in second_page] == [10_000]


def test_created_group_charges_requires_authentication(client):
    assert client.get("/group-charges/created").status_code == 401
