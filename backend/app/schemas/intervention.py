import uuid
from datetime import datetime, date

from pydantic import BaseModel, Field, ConfigDict
from app.models.intervention import InterventionType, InterventionStatus


class InterventionBase(BaseModel):
    student_id: uuid.UUID
    type: InterventionType
    description: str = Field(min_length=1)
    status: InterventionStatus = InterventionStatus.planned
    start_date: date = Field(default_factory=date.today)
    end_date: date | None = None
    outcome_notes: str | None = None


class InterventionCreate(InterventionBase):
    pass


class InterventionUpdate(BaseModel):
    type: InterventionType | None = None
    description: str | None = None
    status: InterventionStatus | None = None
    end_date: date | None = None
    outcome_notes: str | None = None


class InterventionRead(InterventionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_by_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
