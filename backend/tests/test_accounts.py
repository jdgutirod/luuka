from datetime import datetime, timedelta, timezone
from decimal import Decimal
import jwt
import pytest
from sqlalchemy import select
from app.core.config import SECRET_KEY
from app.core.security import ALGORITHM
from app.models.account import Account

NEW_ACCOUNT = {"owner_name": "Ana", "email": "ana@mail.com", "password": "secreta123"}


# Create account

def test_create_account_returns_account_with_zero_balance(client):
    response = client.post("/accounts", json=NEW_ACCOUNT)

    assert response.status_code == 201
    body = response.json()
    assert body["owner_name"] == "Ana"
    assert body["email"] == "ana@mail.com"
    assert Decimal(body["balance"]) == Decimal("0")
    assert "password" not in body
    assert "password_hash" not in body


def test_create_account_stores_email_in_lowercase(client):
    response = client.post("/accounts", json={**NEW_ACCOUNT, "email": "Ana@Mail.COM"})

    assert response.json()["email"] == "ana@mail.com"


def test_create_account_stores_password_hashed(client, session_factory):
    client.post("/accounts", json=NEW_ACCOUNT)

    with session_factory() as db:
        password_hash = db.scalar(select(Account.password_hash).where(Account.email == "ana@mail.com"))
    assert password_hash != NEW_ACCOUNT["password"]
    assert password_hash.startswith("$argon2")


def test_create_account_with_registered_email_returns_409(client):
    client.post("/accounts", json=NEW_ACCOUNT)

    response = client.post("/accounts", json={**NEW_ACCOUNT, "email": "ANA@mail.com"})

    assert response.status_code == 409
    assert response.json()["detail"] == "El email ana@mail.com ya está registrado"


@pytest.mark.parametrize(
    "changes",
    [
        {"password": "1234567"},
        {"email": "no-es-un-email"},
        {"owner_name": "x" * 101},
    ],
)
def test_create_account_with_invalid_data_returns_422(client, changes):
    response = client.post("/accounts", json={**NEW_ACCOUNT, **changes})

    assert response.status_code == 422


# Login

def test_login_returns_bearer_token(client):
    client.post("/accounts", json=NEW_ACCOUNT)

    response = client.post("/accounts/login", data={"username": "ana@mail.com", "password": "secreta123"})

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_ignores_email_case(client):
    client.post("/accounts", json=NEW_ACCOUNT)

    response = client.post("/accounts/login", data={"username": "ANA@MAIL.com", "password": "secreta123"})

    assert response.status_code == 200


@pytest.mark.parametrize(
    "credentials",
    [
        {"username": "ana@mail.com", "password": "incorrecta"},
        {"username": "nadie@mail.com", "password": "secreta123"},
    ],
)
def test_login_with_wrong_credentials_returns_same_401(client, credentials):
    client.post("/accounts", json=NEW_ACCOUNT)

    response = client.post("/accounts/login", data=credentials)

    assert response.status_code == 401
    assert response.json()["detail"] == "Email o contraseña incorrectos"
    assert response.headers["www-authenticate"] == "Bearer"


# Authentication on protected endpoints

@pytest.mark.parametrize("path", ["/accounts/me/balance", "/accounts/me/transactions"])
def test_protected_endpoint_without_token_returns_401(client, path):
    response = client.get(path)

    assert response.status_code == 401


def test_protected_endpoint_with_invalid_token_returns_401(client):
    response = client.get("/accounts/me/balance", headers={"Authorization": "Bearer token-falso"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Token inválido o expirado"


def test_protected_endpoint_with_expired_token_returns_401(client, make_account):
    account_id, _ = make_account("ana@mail.com")
    expired_token = jwt.encode(
        {"sub": account_id, "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = client.get("/accounts/me/balance", headers={"Authorization": f"Bearer {expired_token}"})

    assert response.status_code == 401


def test_protected_endpoint_with_token_signed_by_other_key_returns_401(client, make_account):
    account_id, _ = make_account("ana@mail.com")
    forged_token = jwt.encode({"sub": account_id}, "otra-llave-distinta-de-al-menos-32-bytes", algorithm=ALGORITHM)

    response = client.get("/accounts/me/balance", headers={"Authorization": f"Bearer {forged_token}"})

    assert response.status_code == 401


# Balance

def test_balance_of_new_account_is_zero(client, make_account):
    account_id, headers = make_account("ana@mail.com")

    response = client.get("/accounts/me/balance", headers=headers)

    assert response.status_code == 200
    assert response.json()["account_id"] == account_id
    assert Decimal(response.json()["balance"]) == Decimal("0")


def test_balance_reflects_reloads_and_transfers(client, make_account, balance_of):
    _, ana_headers = make_account("ana@mail.com", balance="100")
    beto_id, beto_headers = make_account("beto@mail.com")

    client.post("/transactions/transfers", json={"to_account_id": beto_id, "amount": "30"}, headers=ana_headers)

    assert Decimal(balance_of(ana_headers)) == Decimal("70")
    assert Decimal(balance_of(beto_headers)) == Decimal("30")


# Transaction history

def test_history_of_new_account_is_empty(client, make_account):
    _, headers = make_account("ana@mail.com")

    response = client.get("/accounts/me/transactions", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_history_includes_sent_and_received_newest_first(client, make_account):
    ana_id, ana_headers = make_account("ana@mail.com", balance="100")
    beto_id, beto_headers = make_account("beto@mail.com", balance="50")
    client.post("/transactions/transfers", json={"to_account_id": beto_id, "amount": "30"}, headers=ana_headers)
    client.post("/transactions/transfers", json={"to_account_id": ana_id, "amount": "10"}, headers=beto_headers)

    history = client.get("/accounts/me/transactions", headers=ana_headers).json()

    assert [(t["type"], Decimal(t["amount"])) for t in history] == [
        ("DIRECT_TRANSFER", Decimal("10")),
        ("DIRECT_TRANSFER", Decimal("30")),
        ("RELOAD", Decimal("100")),
    ]
    assert history[0]["to_account_id"] == ana_id
    assert history[1]["from_account_id"] == ana_id


def test_history_does_not_show_other_accounts_transactions(client, make_account):
    _, ana_headers = make_account("ana@mail.com", balance="100")
    beto_id, _ = make_account("beto@mail.com")
    _, carla_headers = make_account("carla@mail.com")
    client.post("/transactions/transfers", json={"to_account_id": beto_id, "amount": "30"}, headers=ana_headers)

    history = client.get("/accounts/me/transactions", headers=carla_headers).json()

    assert history == []


def test_history_pagination(client, make_account):
    _, headers = make_account("ana@mail.com")
    for amount in ["1", "2", "3"]:
        client.post("/transactions/reloads", json={"amount": amount}, headers=headers)

    first_page = client.get("/accounts/me/transactions?limit=2", headers=headers).json()
    second_page = client.get("/accounts/me/transactions?limit=2&offset=2", headers=headers).json()

    assert [Decimal(t["amount"]) for t in first_page] == [Decimal("3"), Decimal("2")]
    assert [Decimal(t["amount"]) for t in second_page] == [Decimal("1")]


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
def test_history_with_invalid_pagination_returns_422(client, make_account, query):
    _, headers = make_account("ana@mail.com")

    response = client.get(f"/accounts/me/transactions?{query}", headers=headers)

    assert response.status_code == 422
