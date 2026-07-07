import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class SupportQueueItem(BaseModel):
    student_id: uuid.UUID
    student_name: str
    grade_level: int
    school_id: uuid.UUID
    latest_assessment_id: uuid.UUID | None = None
    latest_assessment_date: date | None = None
    risk_level: str
    risk_probability: float
    support_level: str
    confidence: str
    data_completeness: float
    attendance_pct: float | None = None
    academic_average: float | None = None
    literacy_level: int | None = None
    risk_drivers: list[dict[str, Any]] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    open_interventions: int = 0
    last_intervention_status: str | None = None
    updated_at: datetime | None = None


class InterventionFromSignalRequest(BaseModel):
    student_id: uuid.UUID
    assessment_id: uuid.UUID | None = None
    action: str
    intervention_type: str = "academic"
    start_date: date = Field(default_factory=date.today)
    owner_note: str | None = None


class SupportSummary(BaseModel):
    total_students: int
    urgent: int
    watch: int
    routine: int
    open_interventions: int
    data_completeness_avg: float
