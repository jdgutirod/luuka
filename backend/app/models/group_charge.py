import uuid
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Numeric, String, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.enums import ChargeState

class GroupCharge(Base):
    __tablename__ = "group_charges"
    __table_args__ = (
        CheckConstraint("total_amount > 0", name="ck_group_charges_total_amount_positive"),
    )

    # Attributes
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    total_amount = Column(Numeric(precision=12, scale=2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Enums
    state = Column(SQLEnum(ChargeState, name="group_charge_state_enum"), default=ChargeState.PENDING, nullable=False)

    # Foreign Keys
    creator_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)

    # Relationships
    creator = relationship("Account", back_populates="created_group_charges")
    member_charges = relationship("MemberCharge", back_populates="group_charge")
