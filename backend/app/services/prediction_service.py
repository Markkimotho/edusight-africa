"""
PredictionService: creates Prediction rows by calling the ML serving layer.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.assessment import Assessment
from app.models.prediction import Prediction, RiskLevel
from app.ml.serving import predict_from_assessment, PredictionResult

logger = logging.getLogger(__name__)


class PredictionService:
    """Orchestrates calling the predictor and persisting Prediction rows."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_for_assessment(self, assessment: Assessment) -> Prediction:
        """
        Run the predictor on assessment data and persist the result.

        If a Prediction for this assessment already exists it is returned
        unchanged (idempotent).
        """
        # Check for an existing prediction
        existing = await self.db.execute(
            select(Prediction).where(Prediction.assessment_id == assessment.id)
        )
        if pred := existing.scalar_one_or_none():
            logger.debug("Prediction already exists for assessment %s", assessment.id)
            return pred

        assessment_data: dict[str, Any] = {
            "math_score": assessment.math_score,
            "reading_score": assessment.reading_score,
            "writing_score": assessment.writing_score,
            "attendance_pct": assessment.attendance_pct,
            "behavior_rating": assessment.behavior_rating,
            "literacy_level": assessment.literacy_level,
        }

        result: PredictionResult = predict_from_assessment(assessment_data)

        prediction = Prediction(
            id=uuid.uuid4(),
            assessment_id=assessment.id,
            model_version=result.model_version,
            risk_level=result.risk_level,
            risk_probability=result.risk_probability,
            feature_contributions=result.feature_contributions,
        )
        self.db.add(prediction)
        await self.db.flush()
        await self.db.refresh(prediction)
        logger.info(
            "Created prediction %s for assessment %s: %s (%.2f)",
            prediction.id,
            assessment.id,
            prediction.risk_level,
            prediction.risk_probability,
        )
        return prediction

    async def get_drift_metrics(self) -> dict[str, Any]:
        """
        Return basic model drift metrics computed from stored predictions.

        In production this would compare prediction distributions over time.
        Here we return aggregate statistics.
        """
        from datetime import datetime
        from sqlalchemy import func

        # Count per risk level
        rows = await self.db.execute(
            select(Prediction.risk_level, func.count(Prediction.id).label("cnt"))
            .group_by(Prediction.risk_level)
        )
        counts = {row.risk_level: row.cnt for row in rows}

        # Average probability
        avg_row = await self.db.execute(
            select(func.avg(Prediction.risk_probability))
        )
        avg_prob: float = float(avg_row.scalar_one() or 0.0)

        total = sum(counts.values())
        high_risk_ratio = (
            (counts.get(RiskLevel.high, 0) + counts.get(RiskLevel.critical, 0)) / total
            if total > 0
            else 0.0
        )

        # Simple drift heuristic: flag if >60% of predictions are high/critical
        drift_detected = high_risk_ratio > 0.60
        drift_score = round(high_risk_ratio, 4)

        return {
            "current_model_version": "rule-based-v1.0",
            "prediction_counts": {k.value: v for k, v in counts.items()},
            "average_risk_probability": round(avg_prob, 4),
            "drift_detected": drift_detected,
            "drift_score": drift_score,
            "last_evaluated_at": datetime.utcnow().isoformat(),
        }
