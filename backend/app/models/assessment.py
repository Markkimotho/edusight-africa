import uuid
from datetime import datetime, date

from sqlalchemy import Float, Integer, Date, ForeignKey, DateTime, Text, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import UUIDType


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessed_by_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assessment_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today, index=True)

    # Scores
    math_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reading_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    writing_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    attendance_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    behavior_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5
    literacy_level: Mapped[int | None] = mapped_column(Integer, nullable=True)   # 1-10

    # JSON works on both PostgreSQL (as JSONB via alembic) and SQLite
    additional_context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="assessments", lazy="select")  # type: ignore[name-defined]
    assessor: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[assessed_by_id], back_populates="assessments", lazy="select"
    )
    prediction: Mapped["Prediction | None"] = relationship(  # type: ignore[name-defined]
        "Prediction", back_populates="assessment", uselist=False, lazy="select"
    )
