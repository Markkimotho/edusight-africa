"""Support queue endpoints for teacher intervention workflows."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession, get_current_active_user
from app.models.assessment import Assessment
from app.models.intervention import Intervention, InterventionStatus, InterventionType
from app.models.prediction import Prediction
from app.models.student import Student
from app.models.user import User
from app.schemas.intervention import InterventionRead
from app.schemas.support import InterventionFromSignalRequest, SupportQueueItem, SupportSummary

router = APIRouter()


def _support_level(risk_level: str, probability: float, attendance_pct: float | None) -> str:
    if risk_level == "critical" or probability >= 0.75 or (attendance_pct is not None and attendance_pct < 70):
        return "urgent"
    if risk_level == "high" or probability >= 0.5 or (attendance_pct is not None and attendance_pct < 85):
        return "watch"
    return "routine"


def _academic_average(assessment: Assessment) -> float | None:
    scores = [
        score
        for score in (assessment.math_score, assessment.reading_score, assessment.writing_score)
        if score is not None
    ]
    if not scores:
        return None
    return round(sum(scores) / len(scores), 1)


async def _latest_assessments(db: DBSession) -> list[Assessment]:
    latest = (
        select(
            Assessment.student_id,
            func.max(Assessment.assessment_date).label("latest_date"),
        )
        .group_by(Assessment.student_id)
        .subquery()
    )
    result = await db.execute(
        select(Assessment)
        .options(
            selectinload(Assessment.prediction),
            selectinload(Assessment.student),
        )
        .join(
            latest,
            (Assessment.student_id == latest.c.student_id)
            & (Assessment.assessment_date == latest.c.latest_date),
        )
    )
    return list(result.scalars().all())


@router.get("/queue", response_model=list[SupportQueueItem])
async def support_queue(
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(default=25, ge=1, le=100),
    support_level: str | None = Query(default=None),
) -> list[SupportQueueItem]:
    assessments = await _latest_assessments(db)
    items: list[SupportQueueItem] = []

    intervention_counts = await db.execute(
        select(
            Intervention.student_id,
            func.count(Intervention.id).label("open_count"),
            func.max(Intervention.updated_at).label("last_update"),
        )
        .where(Intervention.status.in_([InterventionStatus.planned, InterventionStatus.active]))
        .group_by(Intervention.student_id)
    )
    open_by_student = {row.student_id: int(row.open_count) for row in intervention_counts}

    for assessment in assessments:
        prediction = assessment.prediction
        if prediction is None:
            continue
        student = assessment.student
        guidance = prediction.feature_contributions or {}
        level = _support_level(
            prediction.risk_level.value,
            prediction.risk_probability,
            assessment.attendance_pct,
        )
        if support_level and level != support_level:
            continue

        items.append(
            SupportQueueItem(
                student_id=student.id,
                student_name=student.full_name,
                grade_level=student.grade_level,
                school_id=student.school_id,
                latest_assessment_id=assessment.id,
                latest_assessment_date=assessment.assessment_date,
                risk_level=prediction.risk_level.value,
                risk_probability=prediction.risk_probability,
                support_level=level,
                confidence=str(guidance.get("confidence", "medium")),
                data_completeness=float(guidance.get("data_completeness", 0.0) or 0.0),
                attendance_pct=assessment.attendance_pct,
                academic_average=_academic_average(assessment),
                literacy_level=assessment.literacy_level,
                risk_drivers=guidance.get("risk_drivers", []),
                recommended_actions=guidance.get("recommended_actions", []),
                open_interventions=open_by_student.get(student.id, 0),
                updated_at=assessment.updated_at,
            )
        )

    rank = {"urgent": 0, "watch": 1, "routine": 2}
    items.sort(key=lambda item: (rank[item.support_level], -item.risk_probability, item.student_name))
    return items[:limit]


@router.get("/summary", response_model=SupportSummary)
async def support_summary(
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
) -> SupportSummary:
    items = await support_queue(db, current_user, limit=100, support_level=None)
    total_result = await db.execute(select(func.count(Student.id)))
    total_students = int(total_result.scalar_one() or 0)
    open_result = await db.execute(
        select(func.count(Intervention.id)).where(
            Intervention.status.in_([InterventionStatus.planned, InterventionStatus.active])
        )
    )
    completeness = [item.data_completeness for item in items]
    return SupportSummary(
        total_students=total_students,
        urgent=sum(1 for item in items if item.support_level == "urgent"),
        watch=sum(1 for item in items if item.support_level == "watch"),
        routine=sum(1 for item in items if item.support_level == "routine"),
        open_interventions=int(open_result.scalar_one() or 0),
        data_completeness_avg=round(sum(completeness) / len(completeness), 4) if completeness else 0.0,
    )


@router.post("/interventions/from-signal", response_model=InterventionRead, status_code=status.HTTP_201_CREATED)
async def create_intervention_from_signal(
    payload: InterventionFromSignalRequest,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
) -> InterventionRead:
    student = await db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    try:
        intervention_type = InterventionType(payload.intervention_type)
    except ValueError:
        intervention_type = InterventionType.academic

    description = payload.action
    if payload.owner_note:
        description = f"{description}\n\nContext: {payload.owner_note}"
    if payload.assessment_id:
        description = f"{description}\n\nCreated from assessment {payload.assessment_id}."

    intervention = Intervention(
        id=uuid.uuid4(),
        student_id=student.id,
        created_by_id=current_user.id,
        type=intervention_type,
        description=description,
        status=InterventionStatus.planned,
        start_date=payload.start_date,
    )
    db.add(intervention)
    await db.flush()
    await db.refresh(intervention)
    return InterventionRead.model_validate(intervention)
