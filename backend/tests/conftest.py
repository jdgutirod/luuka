import os

# Must be set before importing the app, because the settings are read at import time
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import app.models  # noqa: F401 (registers all models in Base.metadata)
from app.db.database import Base, get_db
from app.main import app

# SQLite in memory by default. Set TEST_DATABASE_URL to run against PostgreSQL (the database is wiped).
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite://")
USING_POSTGRES = TEST_DATABASE_URL.startswith("postgresql")

PASSWORD = "secreta123"


@pytest.fixture(scope="session")
def engine():
    if USING_POSTGRES:
        test_engine = create_engine(TEST_DATABASE_URL)
    else:
        test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)

    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture
def session_factory(engine):
    yield sessionmaker(autoflush=False, bind=engine)

    # Clean every table after each test
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture
def client(session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_account(client):
    """Registers an account, logs in and optionally reloads a starting balance. Returns (account_id, headers)."""
    def _make_account(email: str, balance: int | None = None) -> tuple[str, dict[str, str]]:
        response = client.post("/accounts", json={"owner_name": email.split("@")[0], "email": email, "password": PASSWORD})
        assert response.status_code == 201, response.text
        account_id = response.json()["id"]

        response = client.post("/accounts/login", data={"username": email, "password": PASSWORD})
        assert response.status_code == 200, response.text
        headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

        if balance is not None:
            response = client.post("/transactions/reloads", json={"amount": balance}, headers=headers)
            assert response.status_code == 201, response.text

        return account_id, headers
    return _make_account


@pytest.fixture
def balance_of(client):
    """Returns the current balance, in whole pesos, of the account behind the given headers."""
    def _balance_of(headers: dict[str, str]) -> int:
        response = client.get("/accounts/me/balance", headers=headers)
        assert response.status_code == 200, response.text
        return response.json()["balance"]
    return _balance_of


@pytest.fixture
def create_group_charge(client):
    """Creates a group charge as the account behind the headers. Returns the response."""
    def _create_group_charge(headers: dict[str, str], total_amount: int, member_ids: list[str], creator_plays: bool = False):
        body = {"name": "Cancha sábado", "total_amount": total_amount, "member_account_ids": member_ids, "creator_plays": creator_plays}
        return client.post("/group-charges", json=body, headers=headers)
    return _create_group_charge


def member_charge_of(group_charge: dict, account_id: str) -> dict:
    """Finds the member charge of the given account inside a group charge response."""
    return next(m for m in group_charge["member_charges"] if m["account"]["id"] == account_id)


@pytest.fixture
def plate_of(client):
    """Returns the plate of the account behind the given headers."""
    def _plate_of(headers: dict[str, str]) -> str:
        response = client.get("/accounts/me", headers=headers)
        assert response.status_code == 200, response.text
        return response.json()["plate"]
    return _plate_of
