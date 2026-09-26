import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import pytest
from sqlalchemy import update
from app.models.account import Account
from app.schemas.transaction import TransactionCreate
from app.core.exceptions import InsufficientFundsError
from app.services.transactions import transfer_balance
from tests.conftest import USING_POSTGRES


# Reloads

def test_reload_increases_balance(client, make_account, balance_of):
    account_id, headers = make_account("ana@mail.com")

    response = client.post("/transactions/reloads", json={"amount": "50.25"}, headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "RELOAD"
    assert body["from_account_id"] is None
    assert body["to_account_id"] == account_id
    assert Decimal(body["amount"]) == Decimal("50.25")
    assert Decimal(balance_of(headers)) == Decimal("50.25")


def test_reload_requires_authentication(client):
    response = client.post("/transactions/reloads", json={"amount": "50"})

    assert response.status_code == 401


@pytest.mark.parametrize("amount", ["0", "-10", "10.001", "abc"])
def test_reload_with_invalid_amount_returns_422(client, make_account, amount):
    _, headers = make_account("ana@mail.com")

    response = client.post("/transactions/reloads", json={"amount": amount}, headers=headers)

    assert response.status_code == 422


def test_reload_retry_with_same_idempotency_key_is_applied_once(client, make_account, balance_of):
    _, headers = make_account("ana@mail.com")
    headers_with_key = {**headers, "Idempotency-Key": "recarga-1"}

    first = client.post("/transactions/reloads", json={"amount": "50"}, headers=headers_with_key)
    retry = client.post("/transactions/reloads", json={"amount": "50"}, headers=headers_with_key)

    assert first.status_code == retry.status_code == 201
    assert first.json()["id"] == retry.json()["id"]
    assert Decimal(balance_of(headers)) == Decimal("50")


def test_reload_same_idempotency_key_with_other_amount_returns_422(client, make_account, balance_of):
    _, headers = make_account("ana@mail.com")
    headers_with_key = {**headers, "Idempotency-Key": "recarga-1"}
    client.post("/transactions/reloads", json={"amount": "50"}, headers=headers_with_key)

    response = client.post("/transactions/reloads", json={"amount": "20"}, headers=headers_with_key)

    assert response.status_code == 422
    assert Decimal(balance_of(headers)) == Decimal("50")


def test_same_idempotency_key_in_different_accounts_is_independent(client, make_account, balance_of):
    _, ana_headers = make_account("ana@mail.com")
    _, beto_headers = make_account("beto@mail.com")

    ana = client.post("/transactions/reloads", json={"amount": "50"}, headers={**ana_headers, "Idempotency-Key": "k1"})
    beto = client.post("/transactions/reloads", json={"amount": "20"}, headers={**beto_headers, "Idempotency-Key": "k1"})

    assert ana.status_code == beto.status_code == 201
    assert Decimal(balance_of(ana_headers)) == Decimal("50")
    assert Decimal(balance_of(beto_headers)) == Decimal("20")


# Transfers

def test_transfer_moves_balance_between_accounts(client, make_account, balance_of):
    ana_id, ana_headers = make_account("ana@mail.com", balance="100")
    beto_id, beto_headers = make_account("beto@mail.com")

    response = client.post("/transactions/transfers", json={"to_account_id": beto_id, "amount": "30"}, headers=ana_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "DIRECT_TRANSFER"
    assert body["from_account_id"] == ana_id
    assert body["to_account_id"] == beto_id
    assert Decimal(balance_of(ana_headers)) == Decimal("70")
    assert Decimal(balance_of(beto_headers)) == Decimal("30")


def test_transfer_of_whole_balance_leaves_zero(client, make_account, balance_of):
    _, ana_headers = make_account("ana@mail.com", balance="100")
    beto_id, _ = make_account("beto@mail.com")

    response = client.post("/transactions/transfers", json={"to_account_id": beto_id, "amount": "100"}, headers=ana_headers)

    assert response.status_code == 201
    assert Decimal(balance_of(ana_headers)) == Decimal("0")


def test_transfer_with_insufficient_funds_returns_400_and_keeps_balances(client, make_account, balance_of):
    _, ana_headers = make_account("ana@mail.com", balance="100")
    beto_id, beto_headers = make_account("beto@mail.com")

    response = client.post("/transactions/transfers", json={"to_account_id": beto_id, "amount": "100.01"}, headers=ana_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Saldo insuficiente para realizar la transferencia"
    assert Decimal(balance_of(ana_headers)) == Decimal("100")
    assert Decimal(balance_of(beto_headers)) == Decimal("0")


def test_transfer_to_same_account_returns_400(client, make_account):
    ana_id, ana_headers = make_account("ana@mail.com", balance="100")

    response = client.post("/transactions/transfers", json={"to_account_id": ana_id, "amount": "10"}, headers=ana_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "La cuenta de origen y la de destino deben ser distintas"


def test_transfer_to_unknown_account_returns_404(client, make_account):
    _, ana_headers = make_account("ana@mail.com", balance="100")
    unknown_id = str(uuid.uuid4())

    response = client.post("/transactions/transfers", json={"to_account_id": unknown_id, "amount": "10"}, headers=ana_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == f"La cuenta {unknown_id} no existe"


def test_transfer_requires_authentication(client):
    response = client.post("/transactions/transfers", json={"to_account_id": str(uuid.uuid4()), "amount": "10"})

    assert response.status_code == 401


def test_transfer_retry_with_same_idempotency_key_is_applied_once(client, make_account, balance_of):
    _, ana_headers = make_account("ana@mail.com", balance="100")
    beto_id, beto_headers = make_account("beto@mail.com")
    headers_with_key = {**ana_headers, "Idempotency-Key": "transferencia-1"}
    body = {"to_account_id": beto_id, "amount": "30"}

    first = client.post("/transactions/transfers", json=body, headers=headers_with_key)
    retry = client.post("/transactions/transfers", json=body, headers=headers_with_key)

    assert first.status_code == retry.status_code == 201
    assert first.json()["id"] == retry.json()["id"]
    assert Decimal(balance_of(ana_headers)) == Decimal("70")
    assert Decimal(balance_of(beto_headers)) == Decimal("30")


def test_transfer_same_idempotency_key_with_other_data_returns_422(client, make_account, balance_of):
    _, ana_headers = make_account("ana@mail.com", balance="100")
    beto_id, _ = make_account("beto@mail.com")
    carla_id, _ = make_account("carla@mail.com")
    headers_with_key = {**ana_headers, "Idempotency-Key": "transferencia-1"}
    client.post("/transactions/transfers", json={"to_account_id": beto_id, "amount": "30"}, headers=headers_with_key)

    other_amount = client.post("/transactions/transfers", json={"to_account_id": beto_id, "amount": "5"}, headers=headers_with_key)
    other_destination = client.post("/transactions/transfers", json={"to_account_id": carla_id, "amount": "30"}, headers=headers_with_key)

    assert other_amount.status_code == other_destination.status_code == 422
    assert Decimal(balance_of(ana_headers)) == Decimal("70")


def test_transfers_without_idempotency_key_are_all_applied(client, make_account, balance_of):
    _, ana_headers = make_account("ana@mail.com", balance="100")
    beto_id, _ = make_account("beto@mail.com")
    body = {"to_account_id": beto_id, "amount": "10"}

    client.post("/transactions/transfers", json=body, headers=ana_headers)
    client.post("/transactions/transfers", json=body, headers=ana_headers)

    assert Decimal(balance_of(ana_headers)) == Decimal("80")


def test_transfer_uses_balance_read_under_lock_not_stale_one(make_account, session_factory):
    """The sender account can already be loaded in the session (by get_current_account) with an old balance."""
    ana_id, _ = make_account("ana@mail.com", balance="100")
    beto_id, _ = make_account("beto@mail.com")
    ana_uuid, beto_uuid = uuid.UUID(ana_id), uuid.UUID(beto_id)

    with session_factory() as db:
        # Keep a reference, like FastAPI does with current_account, so the session keeps the loaded object
        current_account = db.get(Account, ana_uuid)
        assert current_account.balance == Decimal("100")

        with session_factory() as other_db:  # another request spends almost everything meanwhile
            other_db.execute(update(Account).where(Account.id == ana_uuid).values(balance=Decimal("5")))
            other_db.commit()

        with pytest.raises(InsufficientFundsError):
            transfer_balance(db, TransactionCreate(to_account_id=beto_uuid, amount=Decimal("20")), ana_uuid)


@pytest.mark.postgres
@pytest.mark.skipif(not USING_POSTGRES, reason="Row locks need PostgreSQL (set TEST_DATABASE_URL)")
def test_concurrent_transfers_in_both_directions_keep_balances_consistent(make_account, session_factory):
    ana_id, _ = make_account("ana@mail.com", balance="1000")
    beto_id, _ = make_account("beto@mail.com", balance="1000")
    ana_uuid, beto_uuid = uuid.UUID(ana_id), uuid.UUID(beto_id)
    transfers_per_direction = 20

    def transfer(from_id: uuid.UUID, to_id: uuid.UUID) -> None:
        with session_factory() as db:
            transfer_balance(db, TransactionCreate(to_account_id=to_id, amount=Decimal("1")), from_id)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(transfer, ana_uuid, beto_uuid) for _ in range(transfers_per_direction)]
        futures += [executor.submit(transfer, beto_uuid, ana_uuid) for _ in range(transfers_per_direction)]
        for future in futures:
            future.result()  # re-raises any error, e.g. a deadlock

    with session_factory() as db:
        assert db.get(Account, ana_uuid).balance == Decimal("1000")
        assert db.get(Account, beto_uuid).balance == Decimal("1000")
