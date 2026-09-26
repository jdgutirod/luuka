import re
from datetime import datetime, timedelta, timezone
import jwt
import pytest
from sqlalchemy import select
from app.core.config import SECRET_KEY
from app.core.security import ALGORITHM
from app.models.account import Account
from app.services import accounts as accounts_service
from app.services.accounts import generate_plate, normalize_plate

NEW_ACCOUNT = {"owner_name": "Ana", "email": "ana@mail.com", "password": "secreta123"}
PLATE_FORMAT = re.compile(r"^[A-HJ-NP-Z]{3}[0-9]{3}$")  # 3 letters without I or O + 3 digits


# Create account

def test_create_account_returns_account_with_zero_balance(client):
    response = client.post("/accounts", json=NEW_ACCOUNT)

    assert response.status_code == 201
    body = response.json()
    assert body["owner_name"] == "Ana"
    assert body["email"] == "ana@mail.com"
    assert body["balance"] == 0
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
    assert response.json()["balance"] == 0


def test_balance_reflects_reloads_and_transfers(client, make_account, balance_of):
    _, ana_headers = make_account("ana@mail.com", balance=100_000)
    beto_id, beto_headers = make_account("beto@mail.com")

    client.post("/transactions/transfers", json={"to_account_id": beto_id, "amount": 30_000}, headers=ana_headers)

    assert balance_of(ana_headers) == 70_000
    assert balance_of(beto_headers) == 30_000


# Transaction history

def test_history_of_new_account_is_empty(client, make_account):
    _, headers = make_account("ana@mail.com")

    response = client.get("/accounts/me/transactions", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_history_includes_sent_and_received_newest_first(client, make_account):
    ana_id, ana_headers = make_account("ana@mail.com", balance=100_000)
    beto_id, beto_headers = make_account("beto@mail.com", balance=50_000)
    client.post("/transactions/transfers", json={"to_account_id": beto_id, "amount": 30_000}, headers=ana_headers)
    client.post("/transactions/transfers", json={"to_account_id": ana_id, "amount": 10_000}, headers=beto_headers)

    history = client.get("/accounts/me/transactions", headers=ana_headers).json()

    assert [(t["type"], t["amount"]) for t in history] == [
        ("DIRECT_TRANSFER", 10_000),
        ("DIRECT_TRANSFER", 30_000),
        ("RELOAD", 100_000),
    ]
    assert history[0]["to_account"]["id"] == ana_id
    assert history[1]["from_account"]["id"] == ana_id


def test_history_does_not_show_other_accounts_transactions(client, make_account):
    _, ana_headers = make_account("ana@mail.com", balance=100_000)
    beto_id, _ = make_account("beto@mail.com")
    _, carla_headers = make_account("carla@mail.com")
    client.post("/transactions/transfers", json={"to_account_id": beto_id, "amount": 30_000}, headers=ana_headers)

    history = client.get("/accounts/me/transactions", headers=carla_headers).json()

    assert history == []


def test_history_pagination(client, make_account):
    _, headers = make_account("ana@mail.com")
    for amount in [10_000, 20_000, 30_000]:
        client.post("/transactions/reloads", json={"amount": amount}, headers=headers)

    first_page = client.get("/accounts/me/transactions?limit=2", headers=headers).json()
    second_page = client.get("/accounts/me/transactions?limit=2&offset=2", headers=headers).json()

    assert [t["amount"] for t in first_page] == [30_000, 20_000]
    assert [t["amount"] for t in second_page] == [10_000]


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
def test_history_with_invalid_pagination_returns_422(client, make_account, query):
    _, headers = make_account("ana@mail.com")

    response = client.get(f"/accounts/me/transactions?{query}", headers=headers)

    assert response.status_code == 422


# Plate

def test_generated_plates_look_like_a_colombian_car_plate():
    plates = [generate_plate() for _ in range(500)]

    assert all(PLATE_FORMAT.match(plate) for plate in plates)


@pytest.mark.parametrize("written", ["KQX482", "kqx482", "kqx-482", "KQX 482", " kqx-482 "])
def test_normalize_plate_accepts_the_ways_people_write_it(written):
    assert normalize_plate(written) == "KQX482"


def test_create_account_assigns_a_unique_plate(client):
    plates = [
        client.post("/accounts", json={**NEW_ACCOUNT, "email": f"persona{i}@mail.com"}).json()["plate"]
        for i in range(5)
    ]

    assert all(PLATE_FORMAT.match(plate) for plate in plates)
    assert len(set(plates)) == len(plates)


def test_create_account_retries_when_the_generated_plate_is_taken(client, monkeypatch):
    taken_plate = client.post("/accounts", json=NEW_ACCOUNT).json()["plate"]
    generated = iter([taken_plate, "ZZZ999"])
    monkeypatch.setattr(accounts_service, "generate_plate", lambda: next(generated))

    response = client.post("/accounts", json={**NEW_ACCOUNT, "email": "beto@mail.com"})

    assert response.status_code == 201
    assert response.json()["plate"] == "ZZZ999"


def test_create_account_gives_up_after_several_taken_plates(client, monkeypatch):
    taken_plate = client.post("/accounts", json=NEW_ACCOUNT).json()["plate"]
    monkeypatch.setattr(accounts_service, "generate_plate", lambda: taken_plate)

    with pytest.raises(RuntimeError, match="No se pudo generar una placa única"):
        client.post("/accounts", json={**NEW_ACCOUNT, "email": "beto@mail.com"})


# Current account

def test_me_returns_the_current_account(client, make_account):
    account_id, headers = make_account("ana@mail.com", balance=50_000)

    response = client.get("/accounts/me", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == account_id
    assert body["owner_name"] == "ana"
    assert body["email"] == "ana@mail.com"
    assert PLATE_FORMAT.match(body["plate"])
    assert body["balance"] == 50_000
    assert "password_hash" not in body


def test_me_requires_authentication(client):
    assert client.get("/accounts/me").status_code == 401


# Lookup by plate

@pytest.mark.parametrize("format_plate", [str, str.lower, lambda plate: f"{plate[:3]}-{plate[3:]}".lower()])
def test_lookup_finds_an_account_by_plate_showing_only_public_data(client, make_account, plate_of, format_plate):
    beto_id, beto_headers = make_account("beto@mail.com", balance=50_000)
    _, ana_headers = make_account("ana@mail.com")
    beto_plate = plate_of(beto_headers)

    response = client.get("/accounts/lookup", params={"plate": format_plate(beto_plate)}, headers=ana_headers)

    assert response.status_code == 200
    assert response.json() == {"id": beto_id, "owner_name": "beto", "plate": beto_plate}


def test_lookup_unknown_plate_returns_404(client, make_account):
    _, headers = make_account("ana@mail.com")

    response = client.get("/accounts/lookup", params={"plate": "zzz-000"}, headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "No existe una cuenta con la placa ZZZ000"


@pytest.mark.parametrize("plate", ["ABC", "ABCD-12345"])
def test_lookup_with_invalid_plate_length_returns_422(client, make_account, plate):
    _, headers = make_account("ana@mail.com")

    response = client.get("/accounts/lookup", params={"plate": plate}, headers=headers)

    assert response.status_code == 422


def test_lookup_requires_authentication(client):
    assert client.get("/accounts/lookup", params={"plate": "KQX482"}).status_code == 401


def test_history_shows_who_sent_and_received(client, make_account):
    _, ana_headers = make_account("ana@mail.com", balance=100_000)
    beto_id, _ = make_account("beto@mail.com")
    client.post("/transactions/transfers", json={"to_account_id": beto_id, "amount": 30_000}, headers=ana_headers)

    transfer, reload = client.get("/accounts/me/transactions", headers=ana_headers).json()

    assert transfer["from_account"]["owner_name"] == "ana"
    assert transfer["to_account"]["owner_name"] == "beto"
    assert PLATE_FORMAT.match(transfer["to_account"]["plate"])
    assert "email" not in transfer["to_account"] and "balance" not in transfer["to_account"]
    assert reload["from_account"] is None
