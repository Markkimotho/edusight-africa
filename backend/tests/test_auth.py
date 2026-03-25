"""
Tests for the /api/v1/auth endpoints.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_user, create_test_school, auth_headers
from app.models.user import UserRole


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient, db: AsyncSession):
    """A new user can register and receives tokens."""
    payload = {
        "email": "newuser@example.com",
        "password": "SecurePass1!",
        "full_name": "New User",
        "role": "teacher",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "tokens" in body
    assert "access_token" in body["tokens"]
    assert "refresh_token" in body["tokens"]
    assert body["data"]["email"] == "newuser@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, db: AsyncSession):
    """Registering with an existing email returns 409."""
    school = await create_test_school(db)
    await create_test_user(db, email="dup@example.com", school=school)
    await db.commit()

    payload = {
        "email": "dup@example.com",
        "password": "SecurePass1!",
        "full_name": "Dup User",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db: AsyncSession):
    """A registered user can log in and receive tokens."""
    school = await create_test_school(db)
    await create_test_user(db, email="login@example.com", school=school)
    await db.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "Password123!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body
    assert "refresh_token" in body


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db: AsyncSession):
    """Login with wrong password returns 401."""
    school = await create_test_school(db)
    await create_test_user(db, email="wrongpw@example.com", school=school)
    await db.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpw@example.com", "password": "WrongPassword!"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Login for non-existent user returns 401."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "Whatever123!"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, db: AsyncSession, teacher):
    """Authenticated user can fetch their own profile."""
    resp = await client.get("/api/v1/auth/me", headers=auth_headers(teacher))
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == teacher.email
    assert body["role"] == "teacher"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    """Unauthenticated request to /me returns 403 or 401."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, db: AsyncSession, teacher):
    """A valid refresh token returns a new access token."""
    from app.core.security import create_refresh_token

    refresh_tok = create_refresh_token({"sub": str(teacher.id)})
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_tok})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    """An invalid refresh token returns 401."""
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": "not.a.valid.token"})
    assert resp.status_code == 401
