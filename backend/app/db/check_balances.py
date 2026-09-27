import sys
from sqlalchemy.orm import Session
import app.models  # noqa: F401 (registers all models in Base.metadata)
from app.db.database import SessionLocal
from app.services.reconciliation import check_balances


def _cop(amount: int) -> str:
    return f"${amount:,}".replace(",", ".")


def run(db: Session) -> int:
    """Prints the result of the check. Returns the exit code: 0 if every peso is accounted for, 1 if not."""
    report = check_balances(db)

    for mismatch in report.mismatches:
        print(
            f"Descuadre en la cuenta {mismatch.plate} ({mismatch.account_id}): "
            f"saldo guardado {_cop(mismatch.stored_balance)}, según sus movimientos {_cop(mismatch.expected_balance)}"
        )
    if report.total_balances != report.total_reloaded:
        print(
            f"Descuadre total: la suma de los saldos es {_cop(report.total_balances)} "
            f"y lo recargado es {_cop(report.total_reloaded)}"
        )

    if report.is_consistent:
        print(
            f"Todo cuadra: {report.accounts_checked} cuentas revisadas, "
            f"{_cop(report.total_balances)} en saldos, igual a lo recargado"
        )
        return 0
    return 1


if __name__ == "__main__":
    with SessionLocal() as db:
        sys.exit(run(db))
