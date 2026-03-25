import uuid
import enum
from datetime import datetime

from sqlalchemy import Float, String, Enum as SAEnum, ForeignKey, DateTime, func, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import UUIDType


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (UniqueConstraint("assessment_id", name="uq_predictions_assessment_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(
        SAEnum(RiskLevel, name="risk_level_enum"), nullable=False
    )
    risk_probability: Mapped[float] = mapped_column(Float, nullable=False)
    feature_contributions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="prediction", lazy="select")  # type: ignore[name-defined]
