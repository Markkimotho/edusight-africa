import uuid
from datetime import datetime, date

from pydantic import BaseModel, Field, ConfigDict


class ObservationBase(BaseModel):
    student_id: uuid.UUID
    observation_date: date = Field(default_factory=date.today)
    homework_completion: float | None = Field(default=None, ge=0, le=100)
    reading_minutes: int | None = Field(default=None, ge=0)
    focus_rating: int | None = Field(default=None, ge=1, le=5)
    behavior_home: int | None = Field(default=None, ge=1, le=5)
    mood: int | None = Field(default=None, ge=1, le=5)
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    screen_time_minutes: int | None = Field(default=None, ge=0)
    physical_activity_minutes: int | None = Field(default=None, ge=0)
    notes: str | None = None


class ObservationCreate(ObservationBase):
    pass


class ObservationRead(ObservationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    observer_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
