"""
Tests for app.services.report_service — ReportService.
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_school, create_test_user
from app.models.user import UserRole
from app.models.student import Student, StudentStatus
from app.models.assessment import Assessment
from app.models.prediction import Prediction, RiskLevel
from app.models.intervention import Intervention, InterventionType, InterventionStatus
from app.services.report_service import ReportService


async def create_test_student(
    db: AsyncSession,
    school_id: uuid.UUID,
    name: str = "Student One",
) -> Student:
    student = Student(
        id=uuid.uuid4(),
        full_name=name,
        grade_level=4,
        age=10,
        gender="female",
        school_id=school_id,
        enrollment_date=date(2023, 2, 1),
        status=StudentStatus.active,
    )
    db.add(student)
    await db.flush()
    await db.refresh(student)
    return student


# ---------------------------------------------------------------------------
# ReportService.school_analytics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_school_analytics_empty_school(db: AsyncSession):
    """Analytics for a school with no students should return zeroed values."""
    school = await create_test_school(db)
    service = ReportService(db)

    result = await service.school_analytics(school.id)

    assert result["school_id"] == str(school.id)
    assert result["total_active_students"] == 0
    assert result["risk_distribution"] == {}
    assert result["average_scores"]["math"] == 0.0
    assert result["average_scores"]["reading"] == 0.0
    assert result["active_interventions"] == 0


@pytest.mark.asyncio
async def test_school_analytics_with_students_and_assessments(db: AsyncSession):
    """Analytics should reflect student data, assessments, and interventions."""
    school = await create_test_school(db)
    teacher = await create_test_user(db, school=school)
    student_a = await create_test_student(db, school.id, name="Student A")
    student_b = await create_test_student(db, school.id, name="Student B")

    # Create assessments and predictions
    for student, math, reading in [(student_a, 80.0, 75.0), (student_b, 60.0, 55.0)]:
        assessment = Assessment(
            id=uuid.uuid4(),
            student_id=student.id,
            assessed_by_id=teacher.id,
            assessment_date=date.today(),
            math_score=math,
            reading_score=reading,
            writing_score=70.0,
            attendance_pct=85.0,
            behavior_rating=4,
            literacy_level=7,
        )
        db.add(assessment)
        await db.flush()

        prediction = Prediction(
            id=uuid.uuid4(),
            assessment_id=assessment.id,
            model_version="rule-based-v1.0",
            risk_level=RiskLevel.low,
            risk_probability=0.2,
            feature_contributions={},
        )
        db.add(prediction)
        await db.flush()

    # Create an active intervention
    intervention = Intervention(
        id=uuid.uuid4(),
        student_id=student_a.id,
        created_by_id=teacher.id,
        type=InterventionType.academic,
        description="Extra tutoring",
        status=InterventionStatus.active,
        start_date=date.today(),
    )
    db.add(intervention)
    await db.flush()

    service = ReportService(db)
    result = await service.school_analytics(school.id)

    assert result["total_active_students"] == 2
    assert result["active_interventions"] == 1
    assert result["average_scores"]["math"] == 70.0  # (80+60)/2
    assert result["average_scores"]["reading"] == 65.0  # (75+55)/2
    assert "generated_at" in result


# ---------------------------------------------------------------------------
# ReportService.generate_student_csv
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_student_csv_empty_school(db: AsyncSession):
    """CSV for a school with no students should have only headers."""
    school = await create_test_school(db)
    service = ReportService(db)

    csv_content = await service.generate_student_csv(school.id)

    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)
    assert len(rows) == 1  # header only
    assert rows[0] == ["student_id", "full_name", "grade_level", "age", "gender", "enrollment_date", "status"]


@pytest.mark.asyncio
async def test_generate_student_csv_with_students(db: AsyncSession):
    """CSV should contain one row per active student, sorted by name."""
    school = await create_test_school(db)
    await create_test_student(db, school.id, name="Zara Ahmed")
    await create_test_student(db, school.id, name="Alice Banda")

    service = ReportService(db)
    csv_content = await service.generate_student_csv(school.id)

    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)
    assert len(rows) == 3  # header + 2 students
    # Sorted alphabetically
    assert rows[1][1] == "Alice Banda"
    assert rows[2][1] == "Zara Ahmed"
    # Verify column values
    assert rows[1][2] == "4"  # grade_level
    assert rows[1][3] == "10"  # age
    assert rows[1][4] == "female"  # gender
    assert rows[1][6] == "active"  # status


@pytest.mark.asyncio
async def test_generate_student_csv_excludes_inactive(db: AsyncSession):
    """CSV should only include active students."""
    school = await create_test_school(db)
    active_student = await create_test_student(db, school.id, name="Active Student")

    # Create a transferred student
    transferred = Student(
        id=uuid.uuid4(),
        full_name="Transferred Student",
        grade_level=5,
        age=11,
        gender="male",
        school_id=school.id,
        enrollment_date=date(2023, 1, 1),
        status=StudentStatus.transferred,
    )
    db.add(transferred)
    await db.flush()

    service = ReportService(db)
    csv_content = await service.generate_student_csv(school.id)

    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)
    assert len(rows) == 2  # header + 1 active student
    assert rows[1][1] == "Active Student"
