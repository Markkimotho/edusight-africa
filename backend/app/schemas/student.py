import uuid
from datetime import datetime, date

from pydantic import BaseModel, Field, ConfigDict
from app.models.student import StudentStatus
from app.schemas.assessment import AssessmentRead
from app.schemas.prediction import PredictionRead


class StudentBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    grade_level: int = Field(ge=1, le=13)
    age: int = Field(ge=3, le=25)
    gender: str | None = None
    school_id: uuid.UUID
    enrollment_date: date = Field(default_factory=date.today)
    guardian_user_id: uuid.UUID | None = None
    status: StudentStatus = StudentStatus.active


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    full_name: str | None = None
    grade_level: int | None = Field(default=None, ge=1, le=13)
    age: int | None = Field(default=None, ge=3, le=25)
    gender: str | None = None
    guardian_user_id: uuid.UUID | None = None
    status: StudentStatus | None = None


class StudentRead(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class StudentDetail(StudentRead):
    """Extended student info with latest assessment and prediction."""
    latest_assessment: AssessmentRead | None = None
    latest_prediction: PredictionRead | None = None


class StudentHistoryItem(BaseModel):
    """Single item in a student's history timeline."""
    event_type: str   # "assessment" | "observation"
    event_date: date
    data: dict
