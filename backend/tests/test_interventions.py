"""
Tests for the /api/v1/interventions endpoints.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers, create_test_school, create_test_user
from app.models.user import UserRole
from app.models.student import Student, StudentStatus
from app.models.intervention import Intervention, InterventionType, InterventionStatus


async def create_test_student(db: AsyncSession, school_id: uuid.UUID, name: str = "Alice Mwangi") -> Student:
    student = Student(
        id=uuid.uuid4(),
        full_name=name,
        grade_level=3,
        age=9,
        gender="female",
        school_id=school_id,
        enrollment_date=date(2023, 1, 15),
        status=StudentStatus.active,
    )
    db.add(student)
    await db.flush()
    await db.refresh(student)
    return student


async def create_test_intervention(
    db: AsyncSession,
    student_id: uuid.UUID,
    created_by_id: uuid.UUID,
    intervention_type: InterventionType = InterventionType.academic,
    intervention_status: InterventionStatus = InterventionStatus.planned,
) -> Intervention:
    intervention = Intervention(
        id=uuid.uuid4(),
        student_id=student_id,
        created_by_id=created_by_id,
        type=intervention_type,
        description="Extra tutoring sessions",
        status=intervention_status,
        start_date=date.today(),
    )
    db.add(intervention)
    await db.flush()
    await db.refresh(intervention)
    return intervention


# ---------------------------------------------------------------------------
# POST /api/v1/interventions/
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_intervention(client: AsyncClient, db: AsyncSession, teacher, school):
    """A teacher can create an intervention for a student."""
    student = await create_test_student(db, school.id)
    payload = {
        "student_id": str(student.id),
        "type": "academic",
        "description": "After-school reading program",
        "status": "planned",
        "start_date": str(date.today()),
    }
    resp = await client.post("/api/v1/interventions/", json=payload, headers=auth_headers(teacher))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["type"] == "academic"
    assert body["description"] == "After-school reading program"
    assert body["status"] == "planned"
    assert body["student_id"] == str(student.id)
    assert body["created_by_id"] == str(teacher.id)


@pytest.mark.asyncio
async def test_create_intervention_unauthenticated(client: AsyncClient):
    """Unauthenticated request should be rejected."""
    payload = {
        "student_id": str(uuid.uuid4()),
        "type": "behavioral",
        "description": "Some intervention",
    }
    resp = await client.post("/api/v1/interventions/", json=payload)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/interventions/
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_interventions_empty(client: AsyncClient, teacher):
    """Listing interventions when none exist should return empty items."""
    resp = await client.get("/api/v1/interventions/", headers=auth_headers(teacher))
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_list_interventions_with_data(client: AsyncClient, db: AsyncSession, teacher, school):
    """Listing interventions should return created records."""
    student = await create_test_student(db, school.id)
    await create_test_intervention(db, student.id, teacher.id)
    await create_test_intervention(db, student.id, teacher.id, intervention_type=InterventionType.behavioral)
    await db.commit()

    resp = await client.get("/api/v1/interventions/", headers=auth_headers(teacher))
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 2
    assert len(body["data"]) == 2


@pytest.mark.asyncio
async def test_list_interventions_filter_by_student(client: AsyncClient, db: AsyncSession, teacher, school):
    """Filtering by student_id should return only that student's interventions."""
    student_a = await create_test_student(db, school.id, name="Student A")
    student_b = await create_test_student(db, school.id, name="Student B")
    await create_test_intervention(db, student_a.id, teacher.id)
    await create_test_intervention(db, student_b.id, teacher.id)
    await db.commit()

    resp = await client.get(
        f"/api/v1/interventions/?student_id={student_a.id}",
        headers=auth_headers(teacher),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["student_id"] == str(student_a.id)


@pytest.mark.asyncio
async def test_list_interventions_filter_by_status(client: AsyncClient, db: AsyncSession, teacher, school):
    """Filtering by status should return only matching interventions."""
    student = await create_test_student(db, school.id)
    await create_test_intervention(db, student.id, teacher.id, intervention_status=InterventionStatus.active)
    await create_test_intervention(db, student.id, teacher.id, intervention_status=InterventionStatus.completed)
    await db.commit()

    resp = await client.get(
        "/api/v1/interventions/?status=active",
        headers=auth_headers(teacher),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["status"] == "active"


@pytest.mark.asyncio
async def test_list_interventions_filter_by_type(client: AsyncClient, db: AsyncSession, teacher, school):
    """Filtering by type should return only matching interventions."""
    student = await create_test_student(db, school.id)
    await create_test_intervention(db, student.id, teacher.id, intervention_type=InterventionType.attendance)
    await create_test_intervention(db, student.id, teacher.id, intervention_type=InterventionType.home)
    await db.commit()

    resp = await client.get(
        "/api/v1/interventions/?type=attendance",
        headers=auth_headers(teacher),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["type"] == "attendance"


# ---------------------------------------------------------------------------
# PUT /api/v1/interventions/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_intervention(client: AsyncClient, db: AsyncSession, teacher, school):
    """Updating an intervention should persist changes."""
    student = await create_test_student(db, school.id)
    intervention = await create_test_intervention(db, student.id, teacher.id)
    await db.commit()

    payload = {
        "status": "active",
        "outcome_notes": "Student showing improvement",
    }
    resp = await client.put(
        f"/api/v1/interventions/{intervention.id}",
        json=payload,
        headers=auth_headers(teacher),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "active"
    assert body["outcome_notes"] == "Student showing improvement"


@pytest.mark.asyncio
async def test_update_intervention_not_found(client: AsyncClient, teacher):
    """Updating a nonexistent intervention should return 404."""
    payload = {"status": "completed"}
    resp = await client.put(
        f"/api/v1/interventions/{uuid.uuid4()}",
        json=payload,
        headers=auth_headers(teacher),
    )
    assert resp.status_code == 404
