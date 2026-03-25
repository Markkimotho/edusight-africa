import uuid
import enum
from datetime import datetime, date

from sqlalchemy import String, Integer, Date, Enum as SAEnum, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import UUIDType


class StudentStatus(str, enum.Enum):
    active = "active"
    transferred = "transferred"
    graduated = "graduated"


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    guardian_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[StudentStatus] = mapped_column(
        SAEnum(StudentStatus, name="student_status_enum"),
        nullable=False,
        default=StudentStatus.active,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    school: Mapped["School"] = relationship("School", back_populates="students", lazy="select")  # type: ignore[name-defined]
    guardian: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[guardian_user_id], back_populates="ward_students", lazy="select"
    )
    assessments: Mapped[list["Assessment"]] = relationship(  # type: ignore[name-defined]
        "Assessment", back_populates="student", lazy="select", order_by="Assessment.assessment_date.desc()"
    )
    observations: Mapped[list["ParentObservation"]] = relationship(  # type: ignore[name-defined]
        "ParentObservation", back_populates="student", lazy="select"
    )
    interventions: Mapped[list["Intervention"]] = relationship(  # type: ignore[name-defined]
        "Intervention", back_populates="student", lazy="select"
    )
