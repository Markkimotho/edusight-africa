from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import select
from fastapi.encoders import jsonable_encoder

from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.ml.serving import predict_from_assessment
from app.models.assessment import Assessment
from app.models.intervention import Intervention, InterventionStatus, InterventionType
from app.models.prediction import Prediction, RiskLevel
from app.models.student import Student
from app.models.user import ConnectivityLevel, School, SchoolType, User, UserRole


DEMO_STUDENTS = [
    ("Amina Kamau", 6, 12, "female", 62, 52, 4, 2),
    ("Kwame Mensah", 5, 11, "male", 88, 71, 7, 4),
    ("Fatima Hassan", 7, 13, "female", 73, 48, 5, 3),
    ("Chidi Okafor", 4, 10, "male", 91, 79, 8, 4),
    ("Naledi Dlamini", 6, 12, "female", 66, 58, 4, 3),
]


async def seed_demo_data() -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == "demo@edusight.africa"))
        demo_user = existing.scalar_one_or_none()

        school_result = await db.execute(select(School).where(School.name == "EduSight Demo School"))
        school = school_result.scalar_one_or_none()
        if school is None:
            school = School(
                id=uuid.uuid4(),
                name="EduSight Demo School",
                country_code="KEN",
                district="Nairobi",
                type=SchoolType.public,
                connectivity_level=ConnectivityLevel.low,
                student_count=len(DEMO_STUDENTS),
            )
            db.add(school)
            await db.flush()

        if demo_user is None:
            demo_user = User(
                id=uuid.uuid4(),
                email="demo@edusight.africa",
                password_hash=hash_password("password123"),
                full_name="Demo Educator",
                role=UserRole.admin,
                school_id=school.id,
                preferred_language="en",
                country_id="KEN",
                is_active=True,
            )
            db.add(demo_user)
            await db.flush()
        elif demo_user.school_id is None:
            demo_user.school_id = school.id

        for index, (name, grade, age, gender, attendance, academic, literacy, behavior) in enumerate(DEMO_STUDENTS):
            result = await db.execute(select(Student).where(Student.full_name == name, Student.school_id == school.id))
            student = result.scalar_one_or_none()
            if student is None:
                student = Student(
                    id=uuid.uuid4(),
                    full_name=name,
                    grade_level=grade,
                    age=age,
                    gender=gender,
                    school_id=school.id,
                    enrollment_date=date.today() - timedelta(days=220 + index * 20),
                )
                db.add(student)
                await db.flush()

            assessment_result = await db.execute(select(Assessment).where(Assessment.student_id == student.id))
            if assessment_result.scalars().first() is not None:
                continue

            assessment_data = {
                "student_id": student.id,
                "grade_level": grade,
                "age": age,
                "gender": gender,
                "school_type": school.type.value,
                "attendance_pct": attendance,
                "math_score": academic,
                "reading_score": academic + 3,
                "writing_score": max(0, academic - 2),
                "behavior_rating": behavior,
                "literacy_level": literacy,
                "home_engagement_composite": 0.45 if attendance < 75 else 0.7,
                "score_trend": -0.08 if academic < 60 else 0.04,
            }
            result = predict_from_assessment(assessment_data)
            assessment = Assessment(
                id=uuid.uuid4(),
                student_id=student.id,
                assessed_by_id=demo_user.id,
                assessment_date=date.today() - timedelta(days=index),
                math_score=assessment_data["math_score"],
                reading_score=assessment_data["reading_score"],
                writing_score=assessment_data["writing_score"],
                attendance_pct=attendance,
                behavior_rating=behavior,
                literacy_level=literacy,
                additional_context=jsonable_encoder(
                    {
                        "seeded": True,
                        "confidence": result.confidence,
                        "data_completeness": result.data_completeness,
                        "feature_snapshot": result.feature_snapshot,
                    }
                ),
                notes="Demo assessment generated for the end-to-end support workflow.",
            )
            db.add(assessment)
            await db.flush()
            db.add(
                Prediction(
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
            )

            if index == 0:
                db.add(
                    Intervention(
                        id=uuid.uuid4(),
                        student_id=student.id,
                        created_by_id=demo_user.id,
                        type=InterventionType.attendance,
                        description="Guardian follow-up and weekly attendance target.",
                        status=InterventionStatus.active,
                        start_date=date.today(),
                    )
                )

        await db.commit()
