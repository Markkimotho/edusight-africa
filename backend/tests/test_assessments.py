"""
Tests for the /api/v1/assessments endpoints.

Creating an assessment also creates a prediction automatically.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers
from app.models.student import Student, StudentStatus


async def create_test_student(db: AsyncSession, school_id: uuid.UUID) -> Student:
    student = Student(
        id=uuid.uuid4(),
        full_name="Amara Diallo",
        grade_level=5,
        age=11,
        gender="female",
        school_id=school_id,
        enrollment_date=date(2022, 9, 1),
        status=StudentStatus.active,
    )
    db.add(student)
    await db.flush()
    await db.refresh(student)
    return student


@pytest.mark.asyncio
async def test_create_assessment_generates_prediction(
    client: AsyncClient, db: AsyncSession, teacher, school
):
    """Creating an assessment automatically generates a prediction."""
    student = await create_test_student(db, school.id)
    await db.commit()

    payload = {
        "student_id": str(student.id),
        "assessment_date": str(date.today()),
        "math_score": 72.0,
        "reading_score": 65.0,
        "writing_score": 58.0,
        "attendance_pct": 88.0,
        "behavior_rating": 4,
        "literacy_level": 6,
        "notes": "Doing well in math, struggles with writing.",
    }

    resp = await client.post("/api/v1/assessments/", json=payload, headers=auth_headers(teacher))
    assert resp.status_code == 201, resp.text
    body = resp.json()

    # Assessment fields
    assert body["student_id"] == str(student.id)
    assert body["math_score"] == 72.0

    # Prediction was auto-generated
    assert body["prediction"] is not None
    pred = body["prediction"]
    assert pred["risk_level"] in ("low", "medium", "high", "critical")
    assert 0.0 <= pred["risk_probability"] <= 1.0
    assert isinstance(pred["feature_contributions"], dict)
    assert pred["model_version"] == "rule-based-v1.0"


@pytest.mark.asyncio
async def test_create_assessment_low_scores_high_risk(
    client: AsyncClient, db: AsyncSession, teacher, school
):
    """Very low scores should produce a high or critical risk prediction."""
    student = await create_test_student(db, school.id)
    await db.commit()

    payload = {
        "student_id": str(student.id),
        "assessment_date": str(date.today()),
        "math_score": 10.0,
        "reading_score": 8.0,
        "writing_score": 5.0,
        "attendance_pct": 30.0,
        "behavior_rating": 1,
        "literacy_level": 1,
    }

    resp = await client.post("/api/v1/assessments/", json=payload, headers=auth_headers(teacher))
    assert resp.status_code == 201
    pred = resp.json()["prediction"]
    assert pred["risk_level"] in ("high", "critical")


@pytest.mark.asyncio
async def test_create_assessment_high_scores_low_risk(
    client: AsyncClient, db: AsyncSession, teacher, school
):
    """Very high scores should produce a low risk prediction."""
    student = await create_test_student(db, school.id)
    await db.commit()

    payload = {
        "student_id": str(student.id),
        "assessment_date": str(date.today()),
        "math_score": 98.0,
        "reading_score": 95.0,
        "writing_score": 97.0,
        "attendance_pct": 99.0,
        "behavior_rating": 5,
        "literacy_level": 10,
    }

    resp = await client.post("/api/v1/assessments/", json=payload, headers=auth_headers(teacher))
    assert resp.status_code == 201
    pred = resp.json()["prediction"]
    assert pred["risk_level"] in ("low", "medium")


@pytest.mark.asyncio
async def test_list_assessments(client: AsyncClient, db: AsyncSession, teacher, school):
    """Listing assessments returns paginated results."""
    student = await create_test_student(db, school.id)
    await db.commit()

    # Create two assessments
    for score in [60.0, 75.0]:
        await client.post(
            "/api/v1/assessments/",
            json={
                "student_id": str(student.id),
                "assessment_date": str(date.today()),
                "math_score": score,
            },
            headers=auth_headers(teacher),
        )

    resp = await client.get("/api/v1/assessments/", headers=auth_headers(teacher))
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] >= 2


@pytest.mark.asyncio
async def test_list_assessments_filter_by_student(
    client: AsyncClient, db: AsyncSession, teacher, school
):
    """Assessments can be filtered by student_id."""
    student_a = await create_test_student(db, school.id)
    student_b = Student(
        id=uuid.uuid4(),
        full_name="Other Student",
        grade_level=4,
        age=10,
        school_id=school.id,
        enrollment_date=date(2023, 1, 1),
        status=StudentStatus.active,
    )
    db.add(student_b)
    await db.flush()
    await db.commit()

    # Create assessment for each student
    for sid in [student_a.id, student_b.id]:
        await client.post(
            "/api/v1/assessments/",
            json={"student_id": str(sid), "assessment_date": str(date.today()), "math_score": 55.0},
            headers=auth_headers(teacher),
        )

    resp = await client.get(
        f"/api/v1/assessments/?student_id={student_a.id}",
        headers=auth_headers(teacher),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert all(a["student_id"] == str(student_a.id) for a in body["data"])


@pytest.mark.asyncio
async def test_get_assessment_detail(client: AsyncClient, db: AsyncSession, teacher, school):
    """GET /assessments/{id} returns assessment with its prediction."""
    student = await create_test_student(db, school.id)
    await db.commit()

    create_resp = await client.post(
        "/api/v1/assessments/",
        json={
            "student_id": str(student.id),
            "assessment_date": str(date.today()),
            "math_score": 70.0,
        },
        headers=auth_headers(teacher),
    )
    assessment_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/assessments/{assessment_id}", headers=auth_headers(teacher))
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == assessment_id
    assert body["prediction"] is not None


@pytest.mark.asyncio
async def test_get_assessment_not_found(client: AsyncClient, teacher):
    """Fetching a non-existent assessment returns 404."""
    resp = await client.get(f"/api/v1/assessments/{uuid.uuid4()}", headers=auth_headers(teacher))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_assessment_create(client: AsyncClient):
    """Creating an assessment without auth is rejected."""
    resp = await client.post(
        "/api/v1/assessments/",
        json={"student_id": str(uuid.uuid4()), "assessment_date": str(date.today())},
    )
    assert resp.status_code in (401, 403)
