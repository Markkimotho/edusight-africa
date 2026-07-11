"""
Tests for the /api/v1/observations endpoints.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers, create_test_school, create_test_user
from app.models.user import UserRole
from app.models.student import Student, StudentStatus
from app.models.observation import ParentObservation


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


async def create_test_observation(
    db: AsyncSession,
    student_id: uuid.UUID,
    observer_id: uuid.UUID,
    obs_date: date | None = None,
) -> ParentObservation:
    obs = ParentObservation(
        id=uuid.uuid4(),
        student_id=student_id,
        observer_id=observer_id,
        observation_date=obs_date or date.today(),
        homework_completion=85.0,
        reading_minutes=30,
        focus_rating=4,
        behavior_home=3,
        mood=4,
        sleep_hours=8.5,
        screen_time_minutes=60,
        physical_activity_minutes=45,
        notes="Good focus today",
    )
    db.add(obs)
    await db.flush()
    await db.refresh(obs)
    return obs


# ---------------------------------------------------------------------------
# POST /api/v1/observations/
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_observation(client: AsyncClient, db: AsyncSession, parent_user, school):
    """A parent can create an observation for a student."""
    student = await create_test_student(db, school.id)
    payload = {
        "student_id": str(student.id),
        "observation_date": str(date.today()),
        "homework_completion": 90.0,
        "reading_minutes": 45,
        "focus_rating": 5,
        "behavior_home": 4,
        "mood": 5,
        "sleep_hours": 9.0,
        "screen_time_minutes": 30,
        "physical_activity_minutes": 60,
        "notes": "Excellent day overall",
    }
    resp = await client.post("/api/v1/observations/", json=payload, headers=auth_headers(parent_user))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["student_id"] == str(student.id)
    assert body["homework_completion"] == 90.0
    assert body["reading_minutes"] == 45
    assert body["focus_rating"] == 5
    assert body["observer_id"] == str(parent_user.id)


@pytest.mark.asyncio
async def test_create_observation_minimal_fields(client: AsyncClient, db: AsyncSession, parent_user, school):
    """Creating an observation with only required fields should succeed."""
    student = await create_test_student(db, school.id)
    payload = {
        "student_id": str(student.id),
        "observation_date": str(date.today()),
    }
    resp = await client.post("/api/v1/observations/", json=payload, headers=auth_headers(parent_user))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["homework_completion"] is None
    assert body["reading_minutes"] is None


@pytest.mark.asyncio
async def test_create_observation_unauthenticated(client: AsyncClient):
    """Unauthenticated request should be rejected."""
    payload = {
        "student_id": str(uuid.uuid4()),
        "observation_date": str(date.today()),
    }
    resp = await client.post("/api/v1/observations/", json=payload)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/observations/
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_observations_empty(client: AsyncClient, parent_user):
    """Listing observations when none exist should return empty items."""
    resp = await client.get("/api/v1/observations/", headers=auth_headers(parent_user))
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_list_observations_with_data(client: AsyncClient, db: AsyncSession, parent_user, school):
    """Listing observations should return created records."""
    student = await create_test_student(db, school.id)
    await create_test_observation(db, student.id, parent_user.id)
    await create_test_observation(db, student.id, parent_user.id, obs_date=date.today() - timedelta(days=1))
    await db.commit()

    resp = await client.get("/api/v1/observations/", headers=auth_headers(parent_user))
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 2
    assert len(body["data"]) == 2


@pytest.mark.asyncio
async def test_list_observations_filter_by_student(client: AsyncClient, db: AsyncSession, parent_user, school):
    """Filtering by student_id should return only that student's observations."""
    student_a = await create_test_student(db, school.id, name="Child A")
    student_b = await create_test_student(db, school.id, name="Child B")
    await create_test_observation(db, student_a.id, parent_user.id)
    await create_test_observation(db, student_b.id, parent_user.id)
    await db.commit()

    resp = await client.get(
        f"/api/v1/observations/?student_id={student_a.id}",
        headers=auth_headers(parent_user),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["student_id"] == str(student_a.id)


@pytest.mark.asyncio
async def test_list_observations_filter_by_date_range(client: AsyncClient, db: AsyncSession, parent_user, school):
    """Filtering by from_date and to_date should narrow results."""
    student = await create_test_student(db, school.id)
    today = date.today()
    await create_test_observation(db, student.id, parent_user.id, obs_date=today - timedelta(days=10))
    await create_test_observation(db, student.id, parent_user.id, obs_date=today - timedelta(days=3))
    await create_test_observation(db, student.id, parent_user.id, obs_date=today)
    await db.commit()

    from_date = today - timedelta(days=5)
    resp = await client.get(
        f"/api/v1/observations/?from_date={from_date}&to_date={today}",
        headers=auth_headers(parent_user),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 2
