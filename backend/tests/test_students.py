"""
Tests for the /api/v1/students endpoints.
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


@pytest.mark.asyncio
async def test_create_student(client: AsyncClient, db: AsyncSession, teacher, school):
    """A teacher can create a student."""
    payload = {
        "full_name": "Kofi Asante",
        "grade_level": 2,
        "age": 8,
        "gender": "male",
        "school_id": str(school.id),
        "enrollment_date": str(date.today()),
        "status": "active",
    }
    resp = await client.post("/api/v1/students/", json=payload, headers=auth_headers(teacher))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["full_name"] == "Kofi Asante"
    assert body["grade_level"] == 2
    assert "id" in body


@pytest.mark.asyncio
async def test_create_student_unauthenticated(client: AsyncClient, school):
    """Unauthenticated request cannot create a student."""
    payload = {
        "full_name": "Ghost Student",
        "grade_level": 1,
        "age": 7,
        "school_id": str(school.id),
        "enrollment_date": str(date.today()),
        "status": "active",
    }
    resp = await client.post("/api/v1/students/", json=payload)
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_list_students(client: AsyncClient, db: AsyncSession, teacher, school):
    """Listing students returns paginated results."""
    await create_test_student(db, school.id, "Student One")
    await create_test_student(db, school.id, "Student Two")
    await db.commit()

    resp = await client.get("/api/v1/students/", headers=auth_headers(teacher))
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert "meta" in body
    assert body["meta"]["total"] >= 2


@pytest.mark.asyncio
async def test_list_students_filter_by_school(client: AsyncClient, db: AsyncSession, teacher, school):
    """Filtering by school_id narrows the results."""
    other_school = await create_test_school(db)
    await create_test_student(db, school.id, "In School")
    await create_test_student(db, other_school.id, "Other School")
    await db.commit()

    resp = await client.get(
        f"/api/v1/students/?school_id={school.id}",
        headers=auth_headers(teacher),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert all(s["school_id"] == str(school.id) for s in body["data"])


@pytest.mark.asyncio
async def test_get_student_detail(client: AsyncClient, db: AsyncSession, teacher, school):
    """Fetching a specific student returns detail including latest_assessment."""
    student = await create_test_student(db, school.id)
    await db.commit()

    resp = await client.get(f"/api/v1/students/{student.id}", headers=auth_headers(teacher))
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(student.id)
    assert body["full_name"] == student.full_name
    # No assessments yet
    assert body["latest_assessment"] is None


@pytest.mark.asyncio
async def test_get_student_not_found(client: AsyncClient, teacher):
    """Fetching a non-existent student returns 404."""
    fake_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/students/{fake_id}", headers=auth_headers(teacher))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_student(client: AsyncClient, db: AsyncSession, teacher, school):
    """A teacher can update a student's grade level."""
    student = await create_test_student(db, school.id)
    await db.commit()

    resp = await client.put(
        f"/api/v1/students/{student.id}",
        json={"grade_level": 4},
        headers=auth_headers(teacher),
    )
    assert resp.status_code == 200
    assert resp.json()["grade_level"] == 4


@pytest.mark.asyncio
async def test_student_history_empty(client: AsyncClient, db: AsyncSession, teacher, school):
    """A student with no assessments or observations has an empty history."""
    student = await create_test_student(db, school.id)
    await db.commit()

    resp = await client.get(
        f"/api/v1/students/{student.id}/history",
        headers=auth_headers(teacher),
    )
    assert resp.status_code == 200
    assert resp.json() == []
