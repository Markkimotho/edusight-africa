"""
Shared pytest fixtures for the EduSight Africa backend test suite.

Uses an in-memory SQLite database via aiosqlite for fast, isolated tests.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base, get_db
from app.main import app
from app.core.security import hash_password, create_access_token
from app.models.user import User, UserRole, School

# ---------------------------------------------------------------------------
# Use SQLite in-memory for tests (no PostgreSQL required)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """Create tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean DB session for each test."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an HTTPX AsyncClient wired to the FastAPI app,
    with the DB dependency overridden to use the test session.
    """

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def create_test_school(db: AsyncSession) -> School:
    from app.models.user import SchoolType, ConnectivityLevel
    school = School(
        id=uuid.uuid4(),
        name="Test School",
        country_code="KE",
        district="Nairobi",
        type=SchoolType.public,
        connectivity_level=ConnectivityLevel.high,
        student_count=100,
    )
    db.add(school)
    await db.flush()
    await db.refresh(school)
    return school


async def create_test_user(
    db: AsyncSession,
    email: str = "teacher@test.com",
    role: UserRole = UserRole.teacher,
    school: School | None = None,
) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password("Password123!"),
        full_name="Test User",
        role=role,
        school_id=school.id if school else None,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


def auth_headers(user: User) -> dict[str, str]:
    """Return Authorization headers for the given user."""
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def school(db: AsyncSession) -> School:
    return await create_test_school(db)


@pytest_asyncio.fixture
async def teacher(db: AsyncSession, school: School) -> User:
    return await create_test_user(db, email="teacher@test.com", role=UserRole.teacher, school=school)


@pytest_asyncio.fixture
async def admin(db: AsyncSession, school: School) -> User:
    return await create_test_user(db, email="admin@test.com", role=UserRole.admin, school=school)


@pytest_asyncio.fixture
async def parent_user(db: AsyncSession, school: School) -> User:
    return await create_test_user(db, email="parent@test.com", role=UserRole.parent, school=school)
