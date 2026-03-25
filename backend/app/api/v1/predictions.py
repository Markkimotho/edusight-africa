"""
Prediction read-only endpoints.
"""

from __future__ import annotations

import uuid
import logging

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select

from app.api.deps import get_current_active_user, require_roles, DBSession
from app.models.prediction import Prediction
from app.models.user import User, UserRole
from app.schemas.prediction import PredictionRead, DriftMetrics
from app.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/drift", response_model=DriftMetrics)
async def get_drift_metrics(
    db: DBSession,
    current_user: User = Depends(require_roles(UserRole.admin, UserRole.superadmin)),
) -> DriftMetrics:
    """
    Return model drift metrics. Admin/superadmin only.

    Includes prediction distribution counts, average probability, and a
    simple drift-detected flag.
    """
    service = PredictionService(db)
    metrics = await service.get_drift_metrics()
    return DriftMetrics(**metrics)


@router.get("/{assessment_id}", response_model=PredictionRead)
async def get_prediction(
    assessment_id: uuid.UUID,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
) -> PredictionRead:
    """Return the prediction for a given assessment, including feature contributions."""
    result = await db.execute(
        select(Prediction).where(Prediction.assessment_id == assessment_id)
    )
    prediction = result.scalar_one_or_none()
    if not prediction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    return PredictionRead.model_validate(prediction)
