"""
ReportService: school-level analytics and CSV export helpers.
"""

from __future__ import annotations

import csv
import io
import uuid
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.student import Student, StudentStatus
from app.models.assessment import Assessment
from app.models.prediction import Prediction, RiskLevel
from app.models.intervention import Intervention, InterventionStatus

logger = logging.getLogger(__name__)


class ReportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def school_analytics(self, school_id: uuid.UUID) -> dict[str, Any]:
        """
        Compute aggregate analytics for a single school.

        Returns a dict suitable for JSON serialisation.
        """
        # Total students
        total_students_result = await self.db.execute(
            select(func.count(Student.id)).where(
                Student.school_id == school_id,
                Student.status == StudentStatus.active,
            )
        )
        total_students: int = total_students_result.scalar_one() or 0

        # Latest predictions per student (via subquery)
        latest_assessment_subq = (
            select(
                Assessment.student_id,
                func.max(Assessment.assessment_date).label("max_date"),
            )
            .where(Assessment.student_id.in_(
                select(Student.id).where(Student.school_id == school_id)
            ))
            .group_by(Assessment.student_id)
            .subquery()
        )

        latest_assessments_subq = (
            select(Assessment.id)
            .join(
                latest_assessment_subq,
                (Assessment.student_id == latest_assessment_subq.c.student_id)
                & (Assessment.assessment_date == latest_assessment_subq.c.max_date),
            )
            .subquery()
        )

        risk_dist_result = await self.db.execute(
            select(Prediction.risk_level, func.count(Prediction.id).label("cnt"))
            .where(Prediction.assessment_id.in_(select(latest_assessments_subq)))
            .group_by(Prediction.risk_level)
        )
        risk_distribution = {row.risk_level.value: row.cnt for row in risk_dist_result}

        # Average scores
        avg_result = await self.db.execute(
            select(
                func.avg(Assessment.math_score).label("avg_math"),
                func.avg(Assessment.reading_score).label("avg_reading"),
                func.avg(Assessment.attendance_pct).label("avg_attendance"),
            ).where(
                Assessment.student_id.in_(
                    select(Student.id).where(Student.school_id == school_id)
                )
            )
        )
        avg_row = avg_result.one()

        # Active interventions
        active_interventions_result = await self.db.execute(
            select(func.count(Intervention.id)).where(
                Intervention.student_id.in_(
                    select(Student.id).where(Student.school_id == school_id)
                ),
                Intervention.status == InterventionStatus.active,
            )
        )
        active_interventions: int = active_interventions_result.scalar_one() or 0

        return {
            "school_id": str(school_id),
            "generated_at": datetime.utcnow().isoformat(),
            "total_active_students": total_students,
            "risk_distribution": risk_distribution,
            "average_scores": {
                "math": round(float(avg_row.avg_math or 0), 2),
                "reading": round(float(avg_row.avg_reading or 0), 2),
                "attendance_pct": round(float(avg_row.avg_attendance or 0), 2),
            },
            "active_interventions": active_interventions,
        }

    async def generate_student_csv(self, school_id: uuid.UUID) -> str:
        """
        Generate a CSV string of all students in the school with their latest
        risk level.

        Returns the CSV content as a string.
        """
        result = await self.db.execute(
            select(Student).where(
                Student.school_id == school_id,
                Student.status == StudentStatus.active,
            ).order_by(Student.full_name)
        )
        students = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "student_id", "full_name", "grade_level", "age",
            "gender", "enrollment_date", "status",
        ])
        for s in students:
            writer.writerow([
                str(s.id), s.full_name, s.grade_level, s.age,
                s.gender or "", str(s.enrollment_date), s.status.value,
            ])

        return output.getvalue()
