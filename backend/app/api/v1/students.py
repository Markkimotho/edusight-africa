"""
Student CRUD endpoints with pagination and risk-level filtering.
"""

from __future__ import annotations

import uuid
import logging
from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user, require_roles, DBSession
from app.models.student import Student, StudentStatus
from app.models.assessment import Assessment
from app.models.prediction import Prediction, RiskLevel
from app.models.user import User, UserRole
from app.models.observation import ParentObservation
from app.schemas.student import StudentCreate, StudentUpdate, StudentRead, StudentDetail, StudentHistoryItem
from app.schemas.assessment import AssessmentRead
from app.schemas.prediction import PredictionRead
from app.schemas.observation import ObservationRead
from app.schemas.common import PaginatedResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=PaginatedResponse[StudentRead])
async def list_students(
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    school_id: uuid.UUID | None = Query(default=None),
    grade_level: int | None = Query(default=None, ge=1, le=13),
    risk_level: RiskLevel | None = Query(default=None),
    status: StudentStatus | None = Query(default=None),
) -> PaginatedResponse[StudentRead]:
    """
    Return a paginated list of students.

    Optionally filter by school_id, grade_level, status, or the risk_level
    from the student's latest prediction.
    """
    query = select(Student)

    if school_id:
        query = query.where(Student.school_id == school_id)
    if grade_level is not None:
        query = query.where(Student.grade_level == grade_level)
    if status is not None:
        query = query.where(Student.status == status)

    if risk_level is not None:
        # Join to the most-recent assessment's prediction to filter by risk
        latest_assessment_subq = (
            select(
                Assessment.student_id,
                func.max(Assessment.assessment_date).label("max_date"),
            )
            .group_by(Assessment.student_id)
            .subquery()
        )
        latest_assessment_id_subq = (
            select(Assessment.id)
            .join(
                latest_assessment_subq,
                (Assessment.student_id == latest_assessment_subq.c.student_id)
                & (Assessment.assessment_date == latest_assessment_subq.c.max_date),
            )
            .subquery()
        )
        at_risk_student_ids_subq = (
            select(Assessment.student_id)
            .where(
                Assessment.id.in_(select(latest_assessment_id_subq)),
                Assessment.id.in_(
                    select(Prediction.assessment_id).where(Prediction.risk_level == risk_level)
                ),
            )
            .subquery()
        )
        query = query.where(Student.id.in_(select(at_risk_student_ids_subq)))

    # Total count
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar_one()

    # Paginated results
    offset = (page - 1) * per_page
    result = await db.execute(query.offset(offset).limit(per_page).order_by(Student.full_name))
    students = result.scalars().all()

    return PaginatedResponse.create(
        items=[StudentRead.model_validate(s) for s in students],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.post("/", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
async def create_student(
    payload: StudentCreate,
    db: DBSession,
    current_user: User = Depends(require_roles(UserRole.teacher, UserRole.admin, UserRole.superadmin)),
) -> StudentRead:
    """Create a new student record (teacher/admin only)."""
    student = Student(
        id=uuid.uuid4(),
        full_name=payload.full_name,
        grade_level=payload.grade_level,
        age=payload.age,
        gender=payload.gender,
        school_id=payload.school_id,
        enrollment_date=payload.enrollment_date,
        guardian_user_id=payload.guardian_user_id,
        status=payload.status,
    )
    db.add(student)
    await db.flush()
    await db.refresh(student)
    logger.info("Student created: %s by user %s", student.id, current_user.id)
    return StudentRead.model_validate(student)


@router.get("/{student_id}", response_model=StudentDetail)
async def get_student(
    student_id: uuid.UUID,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
) -> StudentDetail:
    """Return student detail with their latest assessment and prediction."""
    result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # Latest assessment
    latest_assessment_result = await db.execute(
        select(Assessment)
        .options(selectinload(Assessment.prediction))
        .where(Assessment.student_id == student_id)
        .order_by(Assessment.assessment_date.desc())
        .limit(1)
    )
    latest_assessment = latest_assessment_result.scalar_one_or_none()

    detail = StudentDetail.model_validate(student)
    if latest_assessment:
        detail.latest_assessment = AssessmentRead.model_validate(latest_assessment)
        if latest_assessment.prediction:
            detail.latest_prediction = PredictionRead.model_validate(latest_assessment.prediction)

    return detail


@router.put("/{student_id}", response_model=StudentRead)
async def update_student(
    student_id: uuid.UUID,
    payload: StudentUpdate,
    db: DBSession,
    current_user: User = Depends(require_roles(UserRole.teacher, UserRole.admin, UserRole.superadmin)),
) -> StudentRead:
    """Update a student's information."""
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)

    await db.flush()
    await db.refresh(student)
    return StudentRead.model_validate(student)


@router.get("/{student_id}/history", response_model=list[StudentHistoryItem])
async def get_student_history(
    student_id: uuid.UUID,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
) -> list[StudentHistoryItem]:
    """
    Return a unified timeline of assessments and parent observations for a student,
    ordered newest first.
    """
    result = await db.execute(select(Student).where(Student.id == student_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # Fetch assessments
    assessments_result = await db.execute(
        select(Assessment)
        .options(selectinload(Assessment.prediction))
        .where(Assessment.student_id == student_id)
        .order_by(Assessment.assessment_date.desc())
    )
    assessments = assessments_result.scalars().all()

    # Fetch observations
    obs_result = await db.execute(
        select(ParentObservation)
        .where(ParentObservation.student_id == student_id)
        .order_by(ParentObservation.observation_date.desc())
    )
    observations = obs_result.scalars().all()

    timeline: list[StudentHistoryItem] = []

    for a in assessments:
        item_data = AssessmentRead.model_validate(a).model_dump(mode="json")
        if a.prediction:
            item_data["prediction"] = PredictionRead.model_validate(a.prediction).model_dump(mode="json")
        timeline.append(StudentHistoryItem(
            event_type="assessment",
            event_date=a.assessment_date,
            data=item_data,
        ))

    for o in observations:
        timeline.append(StudentHistoryItem(
            event_type="observation",
            event_date=o.observation_date,
            data=ObservationRead.model_validate(o).model_dump(mode="json"),
        ))

    # Sort by date descending
    timeline.sort(key=lambda x: x.event_date, reverse=True)
    return timeline
