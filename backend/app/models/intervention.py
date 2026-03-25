import uuid
import enum
from datetime import datetime, date

from sqlalchemy import String, Date, Enum as SAEnum, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import UUIDType


class InterventionType(str, enum.Enum):
    academic = "academic"
    behavioral = "behavioral"
    attendance = "attendance"
    home = "home"


class InterventionStatus(str, enum.Enum):
    planned = "planned"
    active = "active"
    completed = "completed"
    discontinued = "discontinued"


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    type: Mapped[InterventionType] = mapped_column(
        SAEnum(InterventionType, name="intervention_type_enum"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[InterventionStatus] = mapped_column(
        SAEnum(InterventionStatus, name="intervention_status_enum"),
        nullable=False,
        default=InterventionStatus.planned,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    outcome_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="interventions", lazy="select")  # type: ignore[name-defined]
    creator: Mapped["User | None"] = relationship("User", back_populates="interventions", lazy="select")  # type: ignore[name-defined]
