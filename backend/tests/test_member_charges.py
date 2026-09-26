import uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from app.services.member_charges import pay_member_charge
from tests.conftest import USING_POSTGRES, member_charge_of


# Read member charges

def test_my_member_charges_lists_only_own_charges_and_filters_by_state(client, make_account, create_group_charge):
    _, creator_headers = make_account("organizador@mail.com")
    ana_id, ana_headers = make_account("ana@mail.com", balance=100_000)
    beto_id, _ = make_account("beto@mail.com")
    first = create_group_charge(creator_headers, 40_000, [ana_id, beto_id]).json()
    create_group_charge(creator_headers, 30_000, [ana_id])
    client.post(f"/group-charges/member-charges/{member_charge_of(first, ana_id)['id']}/pay", headers=ana_headers)

    all_charges = client.get("/group-charges/member-charges/me", headers=ana_headers).json()
    pending = client.get("/group-charges/member-charges/me?state=PENDING", headers=ana_headers).json()
    completed = client.get("/group-charges/member-charges/me?state=COMPLETED", headers=ana_headers).json()

    assert len(all_charges) == 2
    assert all(m["account"]["id"] == ana_id for m in all_charges)
    assert [m["assigned_amount"] for m in pending] == [30_000]
    assert [m["assigned_amount"] for m in completed] == [20_000]


# Pay member charge

def test_pay_member_charge_moves_money_to_creator_and_marks_it_paid(client, make_account, create_group_charge, balance_of):
    creator_id, creator_headers = make_account("organizador@mail.com")
    ana_id, ana_headers = make_account("ana@mail.com", balance=100_000)
    beto_id, _ = make_account("beto@mail.com")
    group_charge = create_group_charge(creator_headers, 60_000, [ana_id, beto_id]).json()
    member_charge_id = member_charge_of(group_charge, ana_id)["id"]

    response = client.post(f"/group-charges/member-charges/{member_charge_id}/pay", headers=ana_headers)

    assert response.status_code == 200
    paid = response.json()
    assert paid["state"] == "COMPLETED"
    assert paid["paid_at"] is not None
    assert paid["transaction_id"] is not None
    assert balance_of(ana_headers) == 70_000
    assert balance_of(creator_headers) == 30_000

    payment = client.get("/accounts/me/transactions", headers=ana_headers).json()[0]
    assert payment["id"] == paid["transaction_id"]
    assert payment["type"] == "COURT_PAYMENT"
    assert payment["from_account"]["id"] == ana_id
    assert payment["to_account"]["id"] == creator_id


def test_group_charge_stays_pending_until_every_member_pays(client, make_account, create_group_charge):
    _, creator_headers = make_account("organizador@mail.com")
    ana_id, ana_headers = make_account("ana@mail.com", balance=100_000)
    beto_id, beto_headers = make_account("beto@mail.com", balance=100_000)
    group_charge = create_group_charge(creator_headers, 60_000, [ana_id, beto_id]).json()
    group_charge_url = f"/group-charges/{group_charge['id']}"

    client.post(f"/group-charges/member-charges/{member_charge_of(group_charge, ana_id)['id']}/pay", headers=ana_headers)
    after_first_payment = client.get(group_charge_url, headers=creator_headers).json()

    client.post(f"/group-charges/member-charges/{member_charge_of(group_charge, beto_id)['id']}/pay", headers=beto_headers)
    after_last_payment = client.get(group_charge_url, headers=creator_headers).json()

    assert after_first_payment["state"] == "PENDING"
    assert after_last_payment["state"] == "COMPLETED"
    assert all(m["state"] == "COMPLETED" for m in after_last_payment["member_charges"])


def test_pay_member_charge_with_insufficient_funds_returns_400_and_changes_nothing(client, make_account, create_group_charge, balance_of):
    _, creator_headers = make_account("organizador@mail.com")
    ana_id, ana_headers = make_account("ana@mail.com", balance=10_000)
    group_charge = create_group_charge(creator_headers, 30_000, [ana_id]).json()
    member_charge_id = member_charge_of(group_charge, ana_id)["id"]

    response = client.post(f"/group-charges/member-charges/{member_charge_id}/pay", headers=ana_headers)

    assert response.status_code == 400
    assert balance_of(ana_headers) == 10_000
    assert balance_of(creator_headers) == 0
    assert client.get(f"/group-charges/{group_charge['id']}", headers=creator_headers).json()["state"] == "PENDING"


def test_pay_member_charge_twice_charges_only_once(client, make_account, create_group_charge, balance_of):
    _, creator_headers = make_account("organizador@mail.com")
    ana_id, ana_headers = make_account("ana@mail.com", balance=100_000)
    group_charge = create_group_charge(creator_headers, 30_000, [ana_id]).json()
    pay_url = f"/group-charges/member-charges/{member_charge_of(group_charge, ana_id)['id']}/pay"

    first = client.post(pay_url, headers=ana_headers)
    retry = client.post(pay_url, headers=ana_headers)

    assert first.status_code == retry.status_code == 200
    assert first.json()["transaction_id"] == retry.json()["transaction_id"]
    assert balance_of(ana_headers) == 70_000


def test_pay_member_charge_of_another_account_returns_404(client, make_account, create_group_charge, balance_of):
    _, creator_headers = make_account("organizador@mail.com")
    ana_id, _ = make_account("ana@mail.com", balance=100_000)
    _, beto_headers = make_account("beto@mail.com", balance=100_000)
    group_charge = create_group_charge(creator_headers, 30_000, [ana_id]).json()

    response = client.post(f"/group-charges/member-charges/{member_charge_of(group_charge, ana_id)['id']}/pay", headers=beto_headers)

    assert response.status_code == 404
    assert balance_of(beto_headers) == 100_000


def test_pay_unknown_member_charge_returns_404(client, make_account):
    _, headers = make_account("ana@mail.com", balance=100_000)

    response = client.post(f"/group-charges/member-charges/{uuid.uuid4()}/pay", headers=headers)

    assert response.status_code == 404


@pytest.mark.postgres
@pytest.mark.skipif(not USING_POSTGRES, reason="Row locks need PostgreSQL (set TEST_DATABASE_URL)")
def test_concurrent_payments_of_all_members_complete_the_group_charge(client, make_account, create_group_charge, session_factory):
    creator_id, creator_headers = make_account("organizador@mail.com")
    members = [make_account(f"miembro{i}@mail.com", balance=100_000) for i in range(8)]
    group_charge = create_group_charge(creator_headers, 80_000, [member_id for member_id, _ in members]).json()

    def pay(member_charge: dict) -> None:
        with session_factory() as db:
            pay_member_charge(db, uuid.UUID(member_charge["id"]), uuid.UUID(member_charge["account"]["id"]))

    with ThreadPoolExecutor(max_workers=8) as executor:
        for future in [executor.submit(pay, member_charge) for member_charge in group_charge["member_charges"]]:
            future.result()

    final = client.get(f"/group-charges/{group_charge['id']}", headers=creator_headers).json()
    assert final["state"] == "COMPLETED"
    assert client.get("/accounts/me/balance", headers=creator_headers).json()["balance"] == 80_000


def test_my_member_charges_show_the_group_and_who_to_pay(client, make_account, plate_of, create_group_charge):
    _, creator_headers = make_account("organizador@mail.com")
    ana_id, ana_headers = make_account("ana@mail.com")
    create_group_charge(creator_headers, 60_000, [ana_id])

    member_charge = client.get("/group-charges/member-charges/me", headers=ana_headers).json()[0]

    assert member_charge["group_charge"]["name"] == "Cancha sábado"
    assert member_charge["group_charge"]["total_amount"] == 60_000
    assert member_charge["group_charge"]["creator"]["owner_name"] == "organizador"
    assert member_charge["group_charge"]["creator"]["plate"] == plate_of(creator_headers)


def test_paying_the_last_member_charge_returns_the_completed_group(client, make_account, create_group_charge):
    _, creator_headers = make_account("organizador@mail.com")
    ana_id, ana_headers = make_account("ana@mail.com", balance=100_000)
    group_charge = create_group_charge(creator_headers, 30_000, [ana_id]).json()

    paid = client.post(f"/group-charges/member-charges/{member_charge_of(group_charge, ana_id)['id']}/pay", headers=ana_headers).json()

    assert paid["state"] == "COMPLETED"
    assert paid["group_charge"]["state"] == "COMPLETED"
