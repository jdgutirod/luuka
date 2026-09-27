import uuid
from sqlalchemy import update
from app.db.check_balances import run
from app.models.account import Account
from app.services.reconciliation import check_balances
from tests.conftest import member_charge_of


def _pay(client, group_charge: dict, account_id: str, headers: dict[str, str]):
    member_charge_id = member_charge_of(group_charge, account_id)["id"]
    return client.post(f"/group-charges/member-charges/{member_charge_id}/pay", headers=headers)


def test_balances_match_their_movements_after_every_kind_of_operation(client, make_account, create_group_charge, session_factory):
    _, creator_headers = make_account("organizador@mail.com", balance=50_000)
    ana_id, ana_headers = make_account("ana@mail.com", balance=80_000)
    beto_id, beto_headers = make_account("beto@mail.com", balance=10_000)
    make_account("sin-movimientos@mail.com")

    # Retries with the same idempotency key, and a transfer rejected for insufficient funds
    for _ in range(2):
        client.post("/transactions/reloads", json={"amount": 5_000}, headers={**beto_headers, "Idempotency-Key": "recarga-1"})
        client.post(
            "/transactions/transfers",
            json={"to_account_id": beto_id, "amount": 15_000},
            headers={**ana_headers, "Idempotency-Key": "transferencia-1"},
        )
    rejected = client.post("/transactions/transfers", json={"to_account_id": ana_id, "amount": 999_000}, headers=beto_headers)

    # Group charge where the creator also plays, with one member paying twice
    group_charge = create_group_charge(creator_headers, 60_000, [ana_id, beto_id], creator_plays=True).json()
    _pay(client, group_charge, ana_id, ana_headers)
    _pay(client, group_charge, ana_id, ana_headers)
    _pay(client, group_charge, beto_id, beto_headers)

    with session_factory() as db:
        report = check_balances(db)

    assert rejected.status_code == 400
    assert report.accounts_checked == 4
    assert report.mismatches == []
    assert report.total_balances == report.total_reloaded == 145_000
    assert report.is_consistent


def test_check_balances_finds_a_balance_that_does_not_match_its_movements(make_account, session_factory):
    ana_id, _ = make_account("ana@mail.com", balance=30_000)
    make_account("beto@mail.com", balance=10_000)

    with session_factory() as db:
        # Simulates a bug that changed a balance without saving a movement
        db.execute(update(Account).where(Account.id == uuid.UUID(ana_id)).values(balance=35_000))
        db.commit()
        report = check_balances(db)

    assert [(m.account_id, m.stored_balance, m.expected_balance) for m in report.mismatches] == [
        (uuid.UUID(ana_id), 35_000, 30_000)
    ]
    assert report.total_balances == 45_000
    assert report.total_reloaded == 40_000
    assert not report.is_consistent


def test_check_balances_with_no_accounts_is_consistent(session_factory):
    with session_factory() as db:
        report = check_balances(db)

    assert report.accounts_checked == 0
    assert report.total_balances == report.total_reloaded == 0
    assert report.is_consistent


def test_check_balances_command_fails_only_when_something_does_not_match(make_account, session_factory, capsys):
    ana_id, _ = make_account("ana@mail.com", balance=30_000)

    with session_factory() as db:
        ok_exit_code = run(db)
        db.execute(update(Account).where(Account.id == uuid.UUID(ana_id)).values(balance=0))
        db.commit()
        error_exit_code = run(db)
    output = capsys.readouterr().out

    assert ok_exit_code == 0
    assert error_exit_code == 1
    assert "Todo cuadra: 1 cuentas revisadas, $30.000 en saldos" in output
    assert "saldo guardado $0, según sus movimientos $30.000" in output
    assert "la suma de los saldos es $0 y lo recargado es $30.000" in output
