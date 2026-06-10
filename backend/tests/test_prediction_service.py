"""
Tests for app.services.prediction_service — PredictionService.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_school, create_test_user
from app.models.user import UserRole
from app.models.student import Student, StudentStatus
from app.models.assessment import Assessment
from app.models.prediction import Prediction, RiskLevel
from app.services.prediction_service import PredictionService
from app.ml.serving import PredictionResult


async def create_test_student(db: AsyncSession, school_id: uuid.UUID) -> Student:
    student = Student(
        id=uuid.uuid4(),
        full_name="Test Student",
        grade_level=5,
        age=11,
        gender="male",
        school_id=school_id,
        enrollment_date=date(2023, 1, 15),
        status=StudentStatus.active,
    )
    db.add(student)
    await db.flush()
    await db.refresh(student)
    return student


async def create_test_assessment(
    db: AsyncSession,
    student_id: uuid.UUID,
    assessed_by_id: uuid.UUID,
) -> Assessment:
    assessment = Assessment(
        id=uuid.uuid4(),
        student_id=student_id,
        assessed_by_id=assessed_by_id,
        assessment_date=date.today(),
        math_score=65.0,
        reading_score=70.0,
        writing_score=60.0,
        attendance_pct=80.0,
        behavior_rating=3,
        literacy_level=6,
        additional_context={"home_engagement_composite": 0.6, "score_trend": 0.1},
    )
    db.add(assessment)
    await db.flush()
    await db.refresh(assessment)
    return assessment


# ---------------------------------------------------------------------------
# PredictionService.create_for_assessment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_for_assessment_creates_prediction(db: AsyncSession):
    """create_for_assessment should create and persist a Prediction row."""
    school = await create_test_school(db)
    teacher = await create_test_user(db, school=school)
    student = await create_test_student(db, school.id)
    assessment = await create_test_assessment(db, student.id, teacher.id)

    mock_result = PredictionResult(
        risk_level="medium",
        risk_probability=0.45,
        feature_contributions={"attendance_pct": -0.12},
        model_version="rule-based-v1.0",
    )

    with patch("app.services.prediction_service.predict_from_assessment", return_value=mock_result):
        service = PredictionService(db)
        prediction = await service.create_for_assessment(assessment)

    assert prediction is not None
    assert prediction.assessment_id == assessment.id
    assert prediction.risk_level == RiskLevel.medium
    assert prediction.risk_probability == 0.45
    assert prediction.model_version == "rule-based-v1.0"
    assert prediction.feature_contributions == {"attendance_pct": -0.12}


@pytest.mark.asyncio
async def test_create_for_assessment_is_idempotent(db: AsyncSession):
    """Calling create_for_assessment twice should return the existing prediction."""
    school = await create_test_school(db)
    teacher = await create_test_user(db, school=school)
    student = await create_test_student(db, school.id)
    assessment = await create_test_assessment(db, student.id, teacher.id)

    mock_result = PredictionResult(
        risk_level="low",
        risk_probability=0.15,
        feature_contributions={},
        model_version="rule-based-v1.0",
    )

    with patch("app.services.prediction_service.predict_from_assessment", return_value=mock_result):
        service = PredictionService(db)
        pred1 = await service.create_for_assessment(assessment)
        pred2 = await service.create_for_assessment(assessment)

    assert pred1.id == pred2.id


@pytest.mark.asyncio
async def test_create_for_assessment_includes_student_context(db: AsyncSession):
    """The prediction should use student details (grade, age, gender) in assessment_data."""
    school = await create_test_school(db)
    teacher = await create_test_user(db, school=school)
    student = await create_test_student(db, school.id)
    assessment = await create_test_assessment(db, student.id, teacher.id)

    captured_data = {}

    def capture_predict(data):
        captured_data.update(data)
        return PredictionResult(
            risk_level="high",
            risk_probability=0.72,
            feature_contributions={},
            model_version="rule-based-v1.0",
        )

    with patch("app.services.prediction_service.predict_from_assessment", side_effect=capture_predict):
        service = PredictionService(db)
        await service.create_for_assessment(assessment)

    assert captured_data["grade_level"] == 5
    assert captured_data["age"] == 11
    assert captured_data["gender"] == "male"
    assert captured_data["math_score"] == 65.0


# ---------------------------------------------------------------------------
# PredictionService.get_drift_metrics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_drift_metrics_empty_db(db: AsyncSession):
    """get_drift_metrics should return sensible defaults on an empty database."""
    mock_predictor = MagicMock()
    mock_predictor.version = "rule-based-v1.0"

    with patch("app.ml.serving.get_predictor", return_value=mock_predictor):
        service = PredictionService(db)
        metrics = await service.get_drift_metrics()

    assert metrics["current_model_version"] == "rule-based-v1.0"
    assert metrics["drift_detected"] is False
    assert metrics["drift_score"] == 0.0
    assert metrics["average_risk_probability"] == 0.0


@pytest.mark.asyncio
async def test_get_drift_metrics_with_predictions(db: AsyncSession):
    """get_drift_metrics should compute aggregates from stored predictions."""
    school = await create_test_school(db)
    teacher = await create_test_user(db, school=school)
    student = await create_test_student(db, school.id)

    # Create assessments and predictions directly
    for risk, prob in [(RiskLevel.low, 0.15), (RiskLevel.medium, 0.4), (RiskLevel.high, 0.7)]:
        assessment = Assessment(
            id=uuid.uuid4(),
            student_id=student.id,
            assessed_by_id=teacher.id,
            assessment_date=date.today(),
            math_score=50.0,
            reading_score=50.0,
            writing_score=50.0,
            attendance_pct=75.0,
            behavior_rating=3,
            literacy_level=5,
        )
        db.add(assessment)
        await db.flush()

        prediction = Prediction(
            id=uuid.uuid4(),
            assessment_id=assessment.id,
            model_version="rule-based-v1.0",
            risk_level=risk,
            risk_probability=prob,
            feature_contributions={},
        )
        db.add(prediction)
        await db.flush()

    mock_predictor = MagicMock()
    mock_predictor.version = "rule-based-v1.0"

    with patch("app.ml.serving.get_predictor", return_value=mock_predictor):
        service = PredictionService(db)
        metrics = await service.get_drift_metrics()

    assert metrics["current_model_version"] == "rule-based-v1.0"
    # 1 high out of 3 total = ~0.33 ratio → no drift
    assert metrics["drift_detected"] is False
    assert "prediction_counts" in metrics
    assert "last_evaluated_at" in metrics
