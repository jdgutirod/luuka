import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import CheckConstraint, Column, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base

class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_accounts_balance_non_negative"),
    )

    # Attributes
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    balance = Column(Numeric(precision=12, scale=2), default=Decimal("0.00"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    sent_transactions = relationship("Transaction", foreign_keys="[Transaction.from_account_id]", back_populates="from_account")
    received_transactions = relationship("Transaction", foreign_keys="[Transaction.to_account_id]", back_populates="to_account")
    created_group_charges = relationship("GroupCharge", back_populates="creator")
    member_charges = relationship("MemberCharge", back_populates="account")
