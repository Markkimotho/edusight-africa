import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.user import UUIDType


class PartnerStudentLink(Base):
    __tablename__ = "partner_student_links"
    __table_args__ = (
        UniqueConstraint("partner_name", "external_student_id", name="uq_partner_student_external_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    partner_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    external_student_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_school_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
