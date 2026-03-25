"""
Parent observation endpoints.
"""

from __future__ import annotations

import uuid
import logging
from datetime import date

from fastapi import APIRouter, Query, Depends, status
from sqlalchemy import select, func

from app.api.deps import get_current_active_user, DBSession
from app.models.observation import ParentObservation
from app.models.user import User
from app.schemas.observation import ObservationCreate, ObservationRead
from app.schemas.common import PaginatedResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=ObservationRead, status_code=status.HTTP_201_CREATED)
async def create_observation(
    payload: ObservationCreate,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
) -> ObservationRead:
    """Log a parent observation for a student."""
    obs = ParentObservation(
        id=uuid.uuid4(),
        student_id=payload.student_id,
        observer_id=current_user.id,
        observation_date=payload.observation_date,
        homework_completion=payload.homework_completion,
        reading_minutes=payload.reading_minutes,
        focus_rating=payload.focus_rating,
        behavior_home=payload.behavior_home,
        mood=payload.mood,
        sleep_hours=payload.sleep_hours,
        screen_time_minutes=payload.screen_time_minutes,
        physical_activity_minutes=payload.physical_activity_minutes,
        notes=payload.notes,
    )
    db.add(obs)
    await db.flush()
    await db.refresh(obs)
    logger.info("Observation created: %s by user %s", obs.id, current_user.id)
    return ObservationRead.model_validate(obs)


@router.get("/", response_model=PaginatedResponse[ObservationRead])
async def list_observations(
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    student_id: uuid.UUID | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
) -> PaginatedResponse[ObservationRead]:
    """List parent observations with optional filters."""
    query = select(ParentObservation)

    if student_id:
        query = query.where(ParentObservation.student_id == student_id)
    if from_date:
        query = query.where(ParentObservation.observation_date >= from_date)
    if to_date:
        query = query.where(ParentObservation.observation_date <= to_date)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar_one()

    offset = (page - 1) * per_page
    result = await db.execute(
        query.offset(offset).limit(per_page).order_by(ParentObservation.observation_date.desc())
    )
    observations = result.scalars().all()

    return PaginatedResponse.create(
        items=[ObservationRead.model_validate(o) for o in observations],
        page=page,
        per_page=per_page,
        total=total,
    )
