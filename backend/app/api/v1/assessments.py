"""
Assessment endpoints.

POST / creates an assessment and auto-triggers prediction generation.
"""

from __future__ import annotations

import uuid
import logging
from datetime import date

from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user, DBSession
from app.models.assessment import Assessment
from app.models.user import User
from app.schemas.assessment import AssessmentCreate, AssessmentRead, AssessmentDetail
from app.schemas.prediction import PredictionRead
from app.schemas.common import PaginatedResponse
from app.services.assessment_service import AssessmentService

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_detail(assessment: Assessment, prediction_obj=None) -> AssessmentDetail:
    """
    Build an AssessmentDetail without triggering lazy relationship loads.
    Prediction is supplied explicitly so we never hit the lazy-load path.
    """
    base = AssessmentRead.model_validate(assessment)
    detail = AssessmentDetail(**base.model_dump())
    if prediction_obj is not None:
        detail.prediction = PredictionRead.model_validate(prediction_obj)
    return detail


@router.post("/", response_model=AssessmentDetail, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    payload: AssessmentCreate,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
) -> AssessmentDetail:
    """
    Create a new assessment and automatically generate a risk prediction.

    Returns the assessment together with its freshly computed prediction.
    """
    service = AssessmentService(db)
    assessment, prediction = await service.create(payload, current_user)
    return _build_detail(assessment, prediction)


@router.get("/", response_model=PaginatedResponse[AssessmentRead])
async def list_assessments(
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    student_id: uuid.UUID | None = Query(default=None),
    assessed_by: uuid.UUID | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
) -> PaginatedResponse[AssessmentRead]:
    """List assessments with optional filters."""
    query = select(Assessment)

    if student_id:
        query = query.where(Assessment.student_id == student_id)
    if assessed_by:
        query = query.where(Assessment.assessed_by_id == assessed_by)
    if from_date:
        query = query.where(Assessment.assessment_date >= from_date)
    if to_date:
        query = query.where(Assessment.assessment_date <= to_date)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar_one()

    offset = (page - 1) * per_page
    result = await db.execute(
        query.offset(offset).limit(per_page).order_by(Assessment.assessment_date.desc())
    )
    assessments = result.scalars().all()

    return PaginatedResponse.create(
        items=[AssessmentRead.model_validate(a) for a in assessments],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("/{assessment_id}", response_model=AssessmentDetail)
async def get_assessment(
    assessment_id: uuid.UUID,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
) -> AssessmentDetail:
    """Return a single assessment with its prediction."""
    service = AssessmentService(db)
    assessment = await service.get_with_prediction(assessment_id)
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    # assessment.prediction is eagerly loaded by get_with_prediction (selectinload)
    prediction_obj = assessment.prediction
    return _build_detail(assessment, prediction_obj)
