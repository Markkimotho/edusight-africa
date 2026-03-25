import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict
from app.models.prediction import RiskLevel


class PredictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_id: uuid.UUID
    model_version: str
    risk_level: RiskLevel
    risk_probability: float = Field(ge=0.0, le=1.0)
    feature_contributions: dict[str, Any]
    created_at: datetime


class DriftMetrics(BaseModel):
    """Model drift monitoring output."""
    current_model_version: str
    prediction_counts: dict[str, int]   # risk_level → count
    average_risk_probability: float
    drift_detected: bool
    drift_score: float | None
    last_evaluated_at: datetime
