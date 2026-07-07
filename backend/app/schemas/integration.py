from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


class PartnerAssessmentPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    external_student_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("external_student_id", "student_external_id", "learner_id"),
        max_length=120,
    )
    external_school_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("external_school_id", "school_external_id"),
        max_length=120,
    )
    student_id: uuid.UUID | None = None
    school_id: uuid.UUID | None = None
    grade_level: int | None = Field(default=None, ge=1, le=13)
    age: int | None = Field(default=None, ge=3, le=25)
    gender: str | None = Field(default=None, max_length=40)
    school_type: str | None = Field(default="public")
    math_score: float | None = Field(default=None, validation_alias=AliasChoices("math_score", "numeracy_score"), ge=0, le=100)
    reading_score: float | None = Field(default=None, validation_alias=AliasChoices("reading_score", "literacy_score"), ge=0, le=100)
    writing_score: float | None = Field(default=None, ge=0, le=100)
    attendance_pct: float | None = Field(default=None, validation_alias=AliasChoices("attendance_pct", "attendance_rate", "attendance_percentage"), ge=0, le=100)
    behavior_rating: int | None = Field(default=None, ge=1, le=5)
    literacy_level: int | None = Field(default=None, ge=1, le=10)
    home_engagement_composite: float | None = Field(default=None, validation_alias=AliasChoices("home_engagement_composite", "guardian_engagement_score"), ge=0, le=1)
    score_trend: float | None = Field(default=None, ge=-1, le=1)
    recent_absence_streak: int | None = Field(default=None, ge=0, le=365)
    context: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_partner_fields(cls, raw: Any) -> Any:
        if not isinstance(raw, dict):
            return raw

        data = dict(raw)

        def number(key: str) -> float | None:
            value = data.get(key)
            if value is None:
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        def pct(value: float | None) -> float | None:
            if value is None:
                return None
            return value * 100 if 0 <= value <= 1 else value

        if "attendance_pct" not in data:
            data["attendance_pct"] = pct(number("attendance_rate") or number("attendance_percentage"))

        if "home_engagement_composite" not in data:
            guardian = number("guardian_engagement_score")
            completion = number("assignment_completion_rate")
            values = [value for value in (guardian, completion) if value is not None]
            if values:
                normalized = [value / 100 if value > 1 else value for value in values]
                data["home_engagement_composite"] = round(sum(normalized) / len(normalized), 4)

        academic_average = number("academic_average")
        if academic_average is not None:
            data.setdefault("math_score", academic_average)
            data.setdefault("reading_score", academic_average)
            data.setdefault("writing_score", academic_average)

        previous_average = number("previous_term_average")
        if "score_trend" not in data and academic_average is not None and previous_average is not None:
            data["score_trend"] = max(-1, min(1, round((academic_average - previous_average) / 100, 4)))

        incidents = number("behavior_incidents")
        if "behavior_rating" not in data and incidents is not None:
            data["behavior_rating"] = max(1, min(5, int(round(5 - min(4, incidents)))))

        context = dict(data.get("context") or {})
        if "socioeconomic_risk_index" in data:
            context.setdefault("socioeconomic_risk_index", data["socioeconomic_risk_index"])
        if "assignment_completion_rate" in data:
            context.setdefault("assignment_completion_rate", data["assignment_completion_rate"])
        data["context"] = context
        return data


class PartnerPredictionResponse(BaseModel):
    external_student_id: str | None
    student_id: uuid.UUID | None
    model_version: str
    support_level: str
    risk_level: str
    risk_probability: float
    calibrated_probability: float
    confidence: str
    data_completeness: float
    missing_data_warnings: list[dict[str, Any]] = Field(default_factory=list)
    risk_drivers: list[dict[str, Any]]
    recommended_actions: list[str]
    suggested_intervention_plan: list[dict[str, Any]] = Field(default_factory=list)
    intervention_priority: str
    explanation: str
    teacher_explanation: str
    parent_explanation: str
    fairness_caution: str | None = None
    feature_snapshot: dict[str, Any]


class PartnerStudentPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    external_student_id: str = Field(validation_alias=AliasChoices("external_student_id", "student_external_id", "learner_id"), max_length=120)
    full_name: str = Field(min_length=1, max_length=255)
    grade_level: int = Field(ge=1, le=13)
    age: int = Field(ge=3, le=25)
    gender: str | None = Field(default=None, max_length=40)
    school_id: uuid.UUID | None = None
    external_school_id: str | None = Field(default=None, validation_alias=AliasChoices("external_school_id", "school_external_id"), max_length=120)
    school_name: str | None = Field(default=None, max_length=255)
    country_code: str = Field(default="KEN", min_length=2, max_length=3)
    enrollment_date: date = Field(default_factory=date.today)
    context: dict[str, Any] = Field(default_factory=dict)


class PartnerStudentResponse(BaseModel):
    id: uuid.UUID
    external_student_id: str
    full_name: str
    grade_level: int
    school_id: uuid.UUID
    status: str
    created: bool


class PartnerAssessmentIngestPayload(PartnerAssessmentPayload):
    student_id: uuid.UUID | None = None
    external_student_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("external_student_id", "student_external_id", "learner_id"),
        max_length=120,
    )
    assessment_date: date = Field(default_factory=date.today)
    notes: str | None = Field(default=None, max_length=4000)


class PartnerAssessmentResponse(BaseModel):
    assessment_id: uuid.UUID
    prediction: PartnerPredictionResponse


class PartnerEventPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_id: str | None = Field(default=None, max_length=160)
    event_type: str = Field(max_length=80)
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    external_student_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("external_student_id", "student_external_id", "learner_id"),
        max_length=120,
    )
    student_id: uuid.UUID | None = None
    school_id: uuid.UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class PartnerEventResponse(BaseModel):
    accepted: bool
    event_type: str
    normalized_assessment: bool
    prediction: PartnerPredictionResponse | None = None
    warnings: list[str] = Field(default_factory=list)


class StudentRiskResponse(BaseModel):
    student_id: uuid.UUID
    latest_assessment_id: uuid.UUID | None
    prediction: PartnerPredictionResponse | None
    message: str


class StudentRecommendationsResponse(BaseModel):
    student_id: uuid.UUID
    recommended_actions: list[str]
    parent_summary: str
    teacher_summary: str
    model_version: str | None


class WebhookTestPayload(BaseModel):
    target_url: str | None = None
    event_type: str = "edusight.webhook.test"
    payload: dict[str, Any] = Field(default_factory=dict)


class ModelVersionResponse(BaseModel):
    version: str
    method: str
    trained_model_enabled: bool
    feature_names: list[str]
    metadata: dict[str, Any]


class APIKeyCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    organization_name: str | None = Field(default=None, max_length=255)
    school_id: uuid.UUID | None = None
    scopes: str = "predict:write,predict:read,model:read"


class APIKeyCreated(BaseModel):
    id: uuid.UUID
    name: str
    api_key: str
    organization_name: str | None
    scopes: str
    created_at: datetime


class APIKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    organization_name: str | None
    school_id: uuid.UUID | None
    scopes: str
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime
