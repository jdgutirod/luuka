import uuid
from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, ForeignKey, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.enums import ChargeState

class MemberCharge(Base):
    __tablename__ = "member_charges"
    __table_args__ = (
        CheckConstraint("assigned_amount > 0", name="ck_member_charges_assigned_amount_positive"),
        UniqueConstraint("group_charge_id", "account_id", name="uq_member_charges_group_charge_account"),
    )

    # Attributes
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assigned_amount = Column(BigInteger, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    # Enums
    state = Column(SQLEnum(ChargeState, name="member_charge_state_enum"), default=ChargeState.PENDING, nullable=False)

    # Foreign Keys
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), index=True, nullable=False)
    group_charge_id = Column(UUID(as_uuid=True), ForeignKey("group_charges.id"), nullable=False)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), unique=True, nullable=True)

    # Relationships
    account = relationship("Account", back_populates="member_charges")
    group_charge = relationship("GroupCharge", back_populates="member_charges")
    transaction = relationship("Transaction", back_populates="member_charge")
