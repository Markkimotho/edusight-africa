import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import UUIDType


class PartnerAPIKey(Base):
    __tablename__ = "partner_api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    organization_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType(), ForeignKey("schools.id", ondelete="SET NULL"), nullable=True, index=True
    )
    scopes: Mapped[str] = mapped_column(String(255), nullable=False, default="predict:write,predict:read")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    school: Mapped["School | None"] = relationship("School", lazy="select")  # type: ignore[name-defined]
