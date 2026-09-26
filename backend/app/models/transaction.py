import uuid
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.enums import TransactionType

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        CheckConstraint(
            "(type = 'RELOAD' AND from_account_id IS NULL AND to_account_id IS NOT NULL)"
            " OR (type = 'WITHDRAWAL' AND from_account_id IS NOT NULL AND to_account_id IS NULL)"
            " OR (type = 'DIRECT_TRANSFER' AND from_account_id IS NOT NULL AND to_account_id IS NOT NULL"
            " AND from_account_id <> to_account_id)"
            " OR (type IN ('COURT_PAYMENT', 'REFUND') AND (from_account_id IS NOT NULL OR to_account_id IS NOT NULL))",
            name="ck_transactions_accounts_match_type",
        ),
    )

    # Attributes
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount = Column(Numeric(precision=12, scale=2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Enums
    type = Column(SQLEnum(TransactionType, name="transaction_type_enum"), nullable=False)

    # Foreign Keys
    from_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    to_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)

    # Relationships
    from_account = relationship("Account", foreign_keys=[from_account_id], back_populates="sent_transactions")
    to_account = relationship("Account", foreign_keys=[to_account_id], back_populates="received_transactions")
    member_charge = relationship("MemberCharge", back_populates="transaction", uselist=False)
