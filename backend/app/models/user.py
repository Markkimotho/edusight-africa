import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    String, Boolean, Integer, Enum as SAEnum,
    ForeignKey, DateTime, func, text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.database import Base


# ---------------------------------------------------------------------------
# Cross-dialect UUID type: native UUID on PostgreSQL, CHAR(36) on SQLite
# ---------------------------------------------------------------------------
class UUIDType(TypeDecorator):
    """Store UUID as native UUID on Postgres, CHAR(36) elsewhere."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value) if isinstance(value, uuid.UUID) else str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(str(value))
        return value


class UserRole(str, enum.Enum):
    teacher = "teacher"
    parent = "parent"
    admin = "admin"
    superadmin = "superadmin"


class SchoolType(str, enum.Enum):
    public = "public"
    private = "private"
    community = "community"


class ConnectivityLevel(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"
    none = "none"


class School(Base):
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country_code: Mapped[str] = mapped_column(String(3), nullable=False)
    district: Mapped[str | None] = mapped_column(String(255), nullable=True)
    type: Mapped[SchoolType] = mapped_column(
        SAEnum(SchoolType, name="school_type_enum"), nullable=False, default=SchoolType.public
    )
    connectivity_level: Mapped[ConnectivityLevel] = mapped_column(
        SAEnum(ConnectivityLevel, name="connectivity_level_enum"),
        nullable=False,
        default=ConnectivityLevel.medium,
    )
    student_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="school", lazy="select")
    students: Mapped[list["Student"]] = relationship("Student", back_populates="school", lazy="select")  # type: ignore[name-defined]


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role_enum"), nullable=False, default=UserRole.teacher
    )
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType(), ForeignKey("schools.id", ondelete="SET NULL"), nullable=True, index=True
    )
    preferred_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    country_id: Mapped[str | None] = mapped_column(String(3), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    school: Mapped[School | None] = relationship("School", back_populates="users", lazy="select")
    assessments: Mapped[list["Assessment"]] = relationship(  # type: ignore[name-defined]
        "Assessment", foreign_keys="Assessment.assessed_by_id", back_populates="assessor", lazy="select"
    )
    observations: Mapped[list["ParentObservation"]] = relationship(  # type: ignore[name-defined]
        "ParentObservation", back_populates="observer", lazy="select"
    )
    interventions: Mapped[list["Intervention"]] = relationship(  # type: ignore[name-defined]
        "Intervention", back_populates="creator", lazy="select"
    )
    ward_students: Mapped[list["Student"]] = relationship(  # type: ignore[name-defined]
        "Student", foreign_keys="Student.guardian_user_id", back_populates="guardian", lazy="select"
    )
