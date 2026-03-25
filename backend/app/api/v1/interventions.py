"""
Intervention CRUD endpoints.
"""

from __future__ import annotations

import uuid
import logging

from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy import select, func

from app.api.deps import get_current_active_user, DBSession
from app.models.intervention import Intervention, InterventionType, InterventionStatus
from app.models.user import User
from app.schemas.intervention import InterventionCreate, InterventionUpdate, InterventionRead
from app.schemas.common import PaginatedResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=InterventionRead, status_code=status.HTTP_201_CREATED)
async def create_intervention(
    payload: InterventionCreate,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
) -> InterventionRead:
    """Create a new intervention for a student."""
    intervention = Intervention(
        id=uuid.uuid4(),
        student_id=payload.student_id,
        created_by_id=current_user.id,
        type=payload.type,
        description=payload.description,
        status=payload.status,
        start_date=payload.start_date,
        end_date=payload.end_date,
        outcome_notes=payload.outcome_notes,
    )
    db.add(intervention)
    await db.flush()
    await db.refresh(intervention)
    logger.info("Intervention created: %s by user %s", intervention.id, current_user.id)
    return InterventionRead.model_validate(intervention)


@router.get("/", response_model=PaginatedResponse[InterventionRead])
async def list_interventions(
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    student_id: uuid.UUID | None = Query(default=None),
    intervention_status: InterventionStatus | None = Query(default=None, alias="status"),
    intervention_type: InterventionType | None = Query(default=None, alias="type"),
) -> PaginatedResponse[InterventionRead]:
    """List interventions with optional filters for student, status, and type."""
    query = select(Intervention)

    if student_id:
        query = query.where(Intervention.student_id == student_id)
    if intervention_status:
        query = query.where(Intervention.status == intervention_status)
    if intervention_type:
        query = query.where(Intervention.type == intervention_type)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar_one()

    offset = (page - 1) * per_page
    result = await db.execute(
        query.offset(offset).limit(per_page).order_by(Intervention.start_date.desc())
    )
    interventions = result.scalars().all()

    return PaginatedResponse.create(
        items=[InterventionRead.model_validate(i) for i in interventions],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.put("/{intervention_id}", response_model=InterventionRead)
async def update_intervention(
    intervention_id: uuid.UUID,
    payload: InterventionUpdate,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
) -> InterventionRead:
    """Update an intervention's status, end date, or outcome notes."""
    result = await db.execute(select(Intervention).where(Intervention.id == intervention_id))
    intervention = result.scalar_one_or_none()
    if not intervention:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intervention not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(intervention, field, value)

    await db.flush()
    await db.refresh(intervention)
    return InterventionRead.model_validate(intervention)
