import uuid
from datetime import datetime, date
from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict


class AssessmentBase(BaseModel):
    student_id: uuid.UUID
    assessment_date: date = Field(default_factory=date.today)
    math_score: float | None = Field(default=None, ge=0, le=100)
    reading_score: float | None = Field(default=None, ge=0, le=100)
    writing_score: float | None = Field(default=None, ge=0, le=100)
    attendance_pct: float | None = Field(default=None, ge=0, le=100)
    behavior_rating: int | None = Field(default=None, ge=1, le=5)
    literacy_level: int | None = Field(default=None, ge=1, le=10)
    additional_context: dict[str, Any] | None = None
    notes: str | None = None


class AssessmentCreate(AssessmentBase):
    pass


class AssessmentRead(AssessmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessed_by_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class AssessmentDetail(AssessmentRead):
    """Assessment with its prediction, resolved after PredictionRead is defined."""
    # Use Optional[Any] initially; model_rebuild() below resolves the real type.
    prediction: Optional[Any] = None


# Resolve the forward reference now that both modules are importable.
# This import must happen after the class definition to avoid circular imports.
def _rebuild() -> None:
    from app.schemas.prediction import PredictionRead  # noqa: F401
    AssessmentDetail.model_rebuild()


_rebuild()
