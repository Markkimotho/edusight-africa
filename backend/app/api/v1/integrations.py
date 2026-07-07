"""Partner integration endpoints for embeddable edtech deployments."""

from __future__ import annotations

import secrets
from datetime import datetime
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession, PartnerAuth, hash_api_key, require_roles
from app.ml.serving import get_model_info, predict_from_assessment
from app.models.assessment import Assessment
from app.models.api_key import PartnerAPIKey
from app.models.integration import PartnerStudentLink
from app.models.prediction import Prediction, RiskLevel
from app.models.student import Student
from app.models.user import School, SchoolType
from app.models.user import User, UserRole
from app.schemas.integration import (
    APIKeyCreate,
    APIKeyCreated,
    APIKeyRead,
    ModelVersionResponse,
    PartnerAssessmentIngestPayload,
    PartnerAssessmentPayload,
    PartnerAssessmentResponse,
    PartnerEventPayload,
    PartnerEventResponse,
    PartnerPredictionResponse,
    PartnerStudentPayload,
    PartnerStudentResponse,
    StudentRecommendationsResponse,
    StudentRiskResponse,
)

router = APIRouter()


def _partner_school_id(partner: PartnerAPIKey | dict):
    if isinstance(partner, dict):
        return partner.get("school_id")
    return partner.school_id


def _partner_name(partner: PartnerAPIKey | dict) -> str:
    if isinstance(partner, dict):
        return str(partner.get("organization_name") or partner.get("name") or "configured")
    return partner.organization_name or partner.name


def _prediction_response(
    result,
    *,
    external_student_id: str | None = None,
    student_id: uuid.UUID | None = None,
) -> PartnerPredictionResponse:
    guidance = result.feature_contributions
    actions = guidance.get("recommended_actions", [])
    return PartnerPredictionResponse(
        external_student_id=external_student_id,
        student_id=student_id,
        model_version=result.model_version,
        support_level=guidance.get("intervention_priority", result.risk_level),
        risk_level=result.risk_level,
        risk_probability=result.risk_probability,
        calibrated_probability=result.risk_probability,
        confidence=result.confidence,
        data_completeness=result.data_completeness or 0.0,
        missing_data_warnings=guidance.get("missing_data_warnings", []),
        risk_drivers=guidance.get("risk_drivers", []),
        recommended_actions=actions,
        suggested_intervention_plan=[
            {"step": index + 1, "action": action, "owner": "teacher", "review_in_days": 14}
            for index, action in enumerate(actions[:3])
        ],
        intervention_priority=guidance.get("intervention_priority", "routine"),
        explanation=guidance.get("explanation", ""),
        teacher_explanation=guidance.get("explanation", ""),
        parent_explanation=(
            "The school has identified practical support steps to help the learner stay engaged. "
            "Please review teacher-approved recommendations rather than raw risk scores."
        ),
        fairness_caution=guidance.get("fairness_caution"),
        feature_snapshot=result.feature_snapshot,
    )


async def _ensure_partner_school(
    db: DBSession,
    partner: PartnerAPIKey | dict,
    payload: PartnerStudentPayload | PartnerAssessmentPayload | PartnerEventPayload,
) -> uuid.UUID:
    partner_school_id = _partner_school_id(partner)
    if partner_school_id:
        return partner_school_id

    provided_school_id = getattr(payload, "school_id", None)
    if provided_school_id:
        result = await db.execute(select(School.id).where(School.id == provided_school_id))
        if result.scalar_one_or_none():
            return provided_school_id

    school_name = getattr(payload, "school_name", None) or f"{_partner_name(partner)} Partner School"
    country_code = getattr(payload, "country_code", None) or "KEN"
    result = await db.execute(select(School).where(School.name == school_name))
    school = result.scalar_one_or_none()
    if school:
        return school.id

    school = School(
        id=uuid.uuid4(),
        name=school_name,
        country_code=str(country_code).upper()[:3],
        type=SchoolType.public,
    )
    db.add(school)
    await db.flush()
    return school.id


async def _find_student(
    db: DBSession,
    partner: PartnerAPIKey | dict,
    student_id: uuid.UUID | None = None,
    external_student_id: str | None = None,
) -> Student | None:
    if student_id:
        result = await db.execute(select(Student).where(Student.id == student_id))
        return result.scalar_one_or_none()

    if external_student_id:
        result = await db.execute(
            select(PartnerStudentLink)
            .where(
                PartnerStudentLink.partner_name == _partner_name(partner),
                PartnerStudentLink.external_student_id == external_student_id,
            )
        )
        link = result.scalar_one_or_none()
        if link:
            result = await db.execute(select(Student).where(Student.id == link.student_id))
            return result.scalar_one_or_none()
    return None


async def _create_assessment_prediction(
    db: DBSession,
    assessment_data: dict[str, Any],
    *,
    student_id: uuid.UUID | None = None,
    external_student_id: str | None = None,
    provenance: dict[str, Any] | None = None,
) -> tuple[Assessment | None, PartnerPredictionResponse]:
    result = predict_from_assessment(assessment_data)
    response = _prediction_response(
        result,
        external_student_id=external_student_id,
        student_id=student_id,
    )
    if not student_id:
        return None, response

    context = dict(assessment_data.get("context") or {})
    context.update(provenance or {})
    if external_student_id:
        context["external_student_id"] = external_student_id

    assessment = Assessment(
        id=uuid.uuid4(),
        student_id=student_id,
        assessed_by_id=None,
        assessment_date=assessment_data.get("assessment_date") or datetime.utcnow().date(),
        math_score=assessment_data.get("math_score"),
        reading_score=assessment_data.get("reading_score"),
        writing_score=assessment_data.get("writing_score"),
        attendance_pct=assessment_data.get("attendance_pct"),
        behavior_rating=assessment_data.get("behavior_rating"),
        literacy_level=assessment_data.get("literacy_level"),
        additional_context=context,
        notes=assessment_data.get("notes"),
    )
    db.add(assessment)
    await db.flush()

    prediction = Prediction(
        id=uuid.uuid4(),
        assessment_id=assessment.id,
        model_version=result.model_version,
        risk_level=RiskLevel(result.risk_level),
        risk_probability=result.risk_probability,
        feature_contributions=jsonable_encoder(
            {
                **result.feature_contributions,
                "confidence": result.confidence,
                "data_completeness": result.data_completeness,
                "feature_snapshot": result.feature_snapshot,
            }
        ),
    )
    db.add(prediction)
    await db.flush()
    return assessment, response


@router.get("/health")
async def integration_health(partner: PartnerAuth) -> dict:
    return {"status": "ok", "module": "edusight-risk-intelligence", "authenticated": True}


@router.get("/model-version", response_model=ModelVersionResponse)
async def model_version(partner: PartnerAuth) -> ModelVersionResponse:
    return ModelVersionResponse(**get_model_info())


@router.post("/predict", response_model=PartnerPredictionResponse)
async def predict(
    payload: PartnerAssessmentPayload,
    partner: PartnerAuth,
) -> PartnerPredictionResponse:
    partner_school_id = _partner_school_id(partner)
    assessment_data = payload.model_dump()
    if partner_school_id and (not payload.school_id or str(partner_school_id) != str(payload.school_id)):
        assessment_data["school_id"] = partner_school_id

    result = predict_from_assessment(assessment_data)
    return _prediction_response(
        result,
        external_student_id=payload.external_student_id,
        student_id=payload.student_id,
    )


@router.post("/students", response_model=PartnerStudentResponse, status_code=status.HTTP_201_CREATED)
async def upsert_student(
    payload: PartnerStudentPayload,
    db: DBSession,
    partner: PartnerAuth,
) -> PartnerStudentResponse:
    school_id = await _ensure_partner_school(db, partner, payload)
    existing = await _find_student(db, partner, external_student_id=payload.external_student_id)
    if existing:
        existing.full_name = payload.full_name
        existing.grade_level = payload.grade_level
        existing.age = payload.age
        existing.gender = payload.gender
        return PartnerStudentResponse(
            id=existing.id,
            external_student_id=payload.external_student_id,
            full_name=existing.full_name,
            grade_level=existing.grade_level,
            school_id=existing.school_id,
            status=existing.status.value,
            created=False,
        )

    student = Student(
        id=uuid.uuid4(),
        full_name=payload.full_name,
        grade_level=payload.grade_level,
        age=payload.age,
        gender=payload.gender,
        school_id=school_id,
        enrollment_date=payload.enrollment_date,
    )
    db.add(student)
    await db.flush()
    db.add(
        PartnerStudentLink(
            partner_name=_partner_name(partner),
            external_student_id=payload.external_student_id,
            student_id=student.id,
            external_school_id=payload.external_school_id,
        )
    )
    await db.flush()
    return PartnerStudentResponse(
        id=student.id,
        external_student_id=payload.external_student_id,
        full_name=student.full_name,
        grade_level=student.grade_level,
        school_id=student.school_id,
        status=student.status.value,
        created=True,
    )


@router.post("/assessments", response_model=PartnerAssessmentResponse, status_code=status.HTTP_201_CREATED)
async def ingest_assessment(
    payload: PartnerAssessmentIngestPayload,
    db: DBSession,
    partner: PartnerAuth,
) -> PartnerAssessmentResponse:
    student = await _find_student(db, partner, payload.student_id, payload.external_student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found. Create the partner student first or include a valid student_id.",
        )

    assessment_data = payload.model_dump()
    assessment_data["student_id"] = student.id
    if assessment_data.get("grade_level") is None:
        assessment_data["grade_level"] = student.grade_level
    if assessment_data.get("age") is None:
        assessment_data["age"] = student.age
    if assessment_data.get("gender") is None:
        assessment_data["gender"] = student.gender
    assessment, prediction = await _create_assessment_prediction(
        db,
        assessment_data,
        student_id=student.id,
        external_student_id=payload.external_student_id,
        provenance={"source": "partner_assessment", "partner": _partner_name(partner)},
    )
    assert assessment is not None
    return PartnerAssessmentResponse(assessment_id=assessment.id, prediction=prediction)


@router.post("/events", response_model=PartnerEventResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_event(
    payload: PartnerEventPayload,
    db: DBSession,
    partner: PartnerAuth,
) -> PartnerEventResponse:
    event_type = payload.event_type.lower().strip()
    supported = {"attendance", "assessment", "behavior", "lms.activity", "assignment"}
    if event_type not in supported:
        return PartnerEventResponse(
            accepted=True,
            event_type=payload.event_type,
            normalized_assessment=False,
            warnings=["Event accepted for audit/analytics but no support signal was generated."],
        )

    merged = {
        **payload.payload,
        "student_id": payload.student_id,
        "external_student_id": payload.external_student_id,
        "school_id": payload.school_id,
        "context": {
            "source_event_id": payload.event_id,
            "source_event_type": payload.event_type,
            "occurred_at": payload.occurred_at.isoformat(),
            **payload.payload.get("context", {}),
        },
    }
    assessment_payload = PartnerAssessmentPayload.model_validate(merged)
    student = await _find_student(db, partner, payload.student_id, payload.external_student_id)
    assessment, prediction = await _create_assessment_prediction(
        db,
        assessment_payload.model_dump(),
        student_id=student.id if student else None,
        external_student_id=payload.external_student_id,
        provenance={"source": "partner_event", "partner": _partner_name(partner)},
    )
    return PartnerEventResponse(
        accepted=True,
        event_type=payload.event_type,
        normalized_assessment=assessment is not None,
        prediction=prediction,
        warnings=[] if assessment else ["Prediction returned but not persisted because the student is not registered."],
    )


@router.get("/students/{student_id}/risk", response_model=StudentRiskResponse)
async def student_risk(student_id: uuid.UUID, db: DBSession, partner: PartnerAuth) -> StudentRiskResponse:
    result = await db.execute(
        select(Assessment)
        .options(selectinload(Assessment.prediction))
        .where(Assessment.student_id == student_id)
        .order_by(Assessment.assessment_date.desc(), Assessment.created_at.desc())
    )
    assessment = result.scalars().first()
    if not assessment or not assessment.prediction:
        return StudentRiskResponse(
            student_id=student_id,
            latest_assessment_id=None,
            prediction=None,
            message="No prediction is available yet. Submit an assessment or event first.",
        )
    prediction = assessment.prediction
    guidance = prediction.feature_contributions or {}
    actions = guidance.get("recommended_actions", [])
    response = PartnerPredictionResponse(
        external_student_id=(assessment.additional_context or {}).get("external_student_id"),
        student_id=student_id,
        model_version=prediction.model_version,
        support_level=guidance.get("intervention_priority", prediction.risk_level.value),
        risk_level=prediction.risk_level.value,
        risk_probability=prediction.risk_probability,
        calibrated_probability=prediction.risk_probability,
        confidence=guidance.get("confidence", "medium"),
        data_completeness=guidance.get("data_completeness", 0.0),
        missing_data_warnings=guidance.get("missing_data_warnings", []),
        risk_drivers=guidance.get("risk_drivers", []),
        recommended_actions=actions,
        suggested_intervention_plan=[
            {"step": index + 1, "action": action, "owner": "teacher", "review_in_days": 14}
            for index, action in enumerate(actions[:3])
        ],
        intervention_priority=guidance.get("intervention_priority", "routine"),
        explanation=guidance.get("explanation", ""),
        teacher_explanation=guidance.get("explanation", ""),
        parent_explanation=(
            "The school has identified practical support steps to help the learner stay engaged. "
            "Please review teacher-approved recommendations rather than raw risk scores."
        ),
        fairness_caution=guidance.get("fairness_caution"),
        feature_snapshot=guidance.get("feature_snapshot", assessment.additional_context or {}),
    )
    return StudentRiskResponse(
        student_id=student_id,
        latest_assessment_id=assessment.id,
        prediction=response,
        message="Latest support signal returned.",
    )


@router.get("/students/{student_id}/recommendations", response_model=StudentRecommendationsResponse)
async def student_recommendations(
    student_id: uuid.UUID,
    db: DBSession,
    partner: PartnerAuth,
) -> StudentRecommendationsResponse:
    risk = await student_risk(student_id, db, partner)
    if not risk.prediction:
        return StudentRecommendationsResponse(
            student_id=student_id,
            recommended_actions=["Collect attendance, assessment, and observation data before generating a plan."],
            parent_summary="The school is gathering more information before recommending home support steps.",
            teacher_summary="Insufficient data for a tailored recommendation. Add attendance and recent scores.",
            model_version=None,
        )
    actions = risk.prediction.recommended_actions
    return StudentRecommendationsResponse(
        student_id=student_id,
        recommended_actions=actions,
        parent_summary="Teacher-approved home support should focus on attendance consistency, encouragement, and short daily practice.",
        teacher_summary=risk.prediction.explanation,
        model_version=risk.prediction.model_version,
    )


@router.post(
    "/api-keys",
    response_model=APIKeyCreated,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    payload: APIKeyCreate,
    db: DBSession,
    current_user: User = Depends(require_roles(UserRole.admin, UserRole.superadmin)),
) -> APIKeyCreated:
    raw_key = f"esa_{secrets.token_urlsafe(32)}"
    record = PartnerAPIKey(
        name=payload.name,
        key_hash=hash_api_key(raw_key),
        organization_name=payload.organization_name,
        school_id=payload.school_id,
        scopes=payload.scopes,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return APIKeyCreated(
        id=record.id,
        name=record.name,
        api_key=raw_key,
        organization_name=record.organization_name,
        scopes=record.scopes,
        created_at=record.created_at or datetime.utcnow(),
    )


@router.get("/api-keys", response_model=list[APIKeyRead])
async def list_api_keys(
    db: DBSession,
    current_user: User = Depends(require_roles(UserRole.admin, UserRole.superadmin)),
) -> list[APIKeyRead]:
    result = await db.execute(select(PartnerAPIKey).order_by(PartnerAPIKey.created_at.desc()))
    return [APIKeyRead.model_validate(row) for row in result.scalars().all()]
