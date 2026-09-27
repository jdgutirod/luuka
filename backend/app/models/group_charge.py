import uuid
from datetime import datetime, timezone
from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, ForeignKey, String, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.enums import ChargeState

class GroupCharge(Base):
    __tablename__ = "group_charges"
    __table_args__ = (
        CheckConstraint("total_amount > 0", name="ck_group_charges_total_amount_positive"),
        UniqueConstraint("creator_id", "idempotency_key", name="uq_group_charges_creator_idempotency_key"),
    )

    # Attributes
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    total_amount = Column(BigInteger, nullable=False)
    idempotency_key = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Enums
    state = Column(SQLEnum(ChargeState, name="group_charge_state_enum"), default=ChargeState.PENDING, nullable=False)

    # Foreign Keys
    creator_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), index=True, nullable=False)

    # Relationships
    creator = relationship("Account", back_populates="created_group_charges")
    member_charges = relationship("MemberCharge", back_populates="group_charge")

    @property
    def creator_share(self) -> int:
        """What the creator puts in because they also played: the part of the total no member is charged for."""
        return self.total_amount - sum(member_charge.assigned_amount for member_charge in self.member_charges)
