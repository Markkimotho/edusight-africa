import uuid
import enum
from datetime import datetime

from sqlalchemy import String, Integer, Enum as SAEnum, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.user import UUIDType


class ModelStatus(str, enum.Enum):
    staging = "staging"
    production = "production"
    archived = "archived"


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    version_string: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    algorithm: Mapped[str] = mapped_column(String(100), nullable=False)
    hyperparameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    training_metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    fairness_metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    dataset_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    status: Mapped[ModelStatus] = mapped_column(
        SAEnum(ModelStatus, name="model_status_enum"),
        nullable=False,
        default=ModelStatus.staging,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
