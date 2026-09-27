from dataclasses import dataclass
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.account import Account
from app.models.enums import TransactionType
from app.models.transaction import Transaction


@dataclass(frozen=True)
class BalanceMismatch:
    """An account whose stored balance is not what its movements add up to."""
    account_id: UUID
    plate: str
    stored_balance: int
    expected_balance: int


@dataclass(frozen=True)
class BalanceReport:
    accounts_checked: int
    mismatches: list[BalanceMismatch]
    # Money only enters through reloads and never leaves the system, so both totals must be equal
    total_balances: int
    total_reloaded: int

    @property
    def is_consistent(self) -> bool:
        return not self.mismatches and self.total_balances == self.total_reloaded


def check_balances(db: Session) -> BalanceReport:
    """Recalculates every balance from its movements (what came in minus what went out) and compares it
    with the stored one.

    It only reads: it never fixes a balance, so a mismatch stays visible until someone looks into it.
    Everything is read in a single query, so it sees one consistent moment even while payments keep happening.
    """
    incoming = (
        select(Transaction.to_account_id.label("account_id"), func.sum(Transaction.amount).label("amount"))
        .where(Transaction.to_account_id.is_not(None))
        .group_by(Transaction.to_account_id)
        .subquery()
    )
    outgoing = (
        select(Transaction.from_account_id.label("account_id"), func.sum(Transaction.amount).label("amount"))
        .where(Transaction.from_account_id.is_not(None))
        .group_by(Transaction.from_account_id)
        .subquery()
    )
    total_reloaded = (
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.type == TransactionType.RELOAD)
        .scalar_subquery()
    )

    rows = db.execute(
        select(
            Account.id,
            Account.plate,
            Account.balance,
            (func.coalesce(incoming.c.amount, 0) - func.coalesce(outgoing.c.amount, 0)).label("expected_balance"),
            total_reloaded.label("total_reloaded"),
        )
        .outerjoin(incoming, incoming.c.account_id == Account.id)
        .outerjoin(outgoing, outgoing.c.account_id == Account.id)
        .order_by(Account.plate)
    ).all()

    mismatches = [
        BalanceMismatch(row.id, row.plate, row.balance, row.expected_balance)
        for row in rows
        if row.balance != row.expected_balance
    ]
    return BalanceReport(
        accounts_checked=len(rows),
        mismatches=mismatches,
        total_balances=sum(row.balance for row in rows),
        total_reloaded=rows[0].total_reloaded if rows else 0,
    )
