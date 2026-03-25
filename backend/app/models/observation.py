import uuid
from datetime import datetime, date

from sqlalchemy import Float, Integer, Date, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import UUIDType


class ParentObservation(Base):
    __tablename__ = "parent_observations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    observer_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    observation_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today, index=True)

    # Observation metrics
    homework_completion: Mapped[float | None] = mapped_column(Float, nullable=True)   # 0-100
    reading_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    focus_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)          # 1-5
    behavior_home: Mapped[int | None] = mapped_column(Integer, nullable=True)         # 1-5
    mood: Mapped[int | None] = mapped_column(Integer, nullable=True)                  # 1-5
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    screen_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    physical_activity_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="observations", lazy="select")  # type: ignore[name-defined]
    observer: Mapped["User | None"] = relationship("User", back_populates="observations", lazy="select")  # type: ignore[name-defined]
