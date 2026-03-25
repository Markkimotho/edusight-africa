"""
AssessmentService: creates assessments and triggers prediction generation.
"""

from __future__ import annotations

import uuid
import logging
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.assessment import Assessment
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.assessment import AssessmentCreate
from app.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)


class AssessmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: AssessmentCreate, assessed_by: User) -> tuple[Assessment, Prediction]:
        """
        Persist a new Assessment row and immediately generate a Prediction.

        Returns:
            (assessment, prediction) tuple.
        """
        assessment = Assessment(
            id=uuid.uuid4(),
            student_id=data.student_id,
            assessed_by_id=assessed_by.id,
            assessment_date=data.assessment_date,
            math_score=data.math_score,
            reading_score=data.reading_score,
            writing_score=data.writing_score,
            attendance_pct=data.attendance_pct,
            behavior_rating=data.behavior_rating,
            literacy_level=data.literacy_level,
            additional_context=data.additional_context,
            notes=data.notes,
        )
        self.db.add(assessment)
        await self.db.flush()
        await self.db.refresh(assessment)

        prediction_service = PredictionService(self.db)
        prediction = await prediction_service.create_for_assessment(assessment)

        logger.info("Assessment %s created with prediction %s", assessment.id, prediction.id)
        return assessment, prediction

    async def get_with_prediction(self, assessment_id: uuid.UUID) -> Assessment | None:
        """Fetch a single Assessment with its Prediction eagerly loaded."""
        result = await self.db.execute(
            select(Assessment)
            .options(selectinload(Assessment.prediction))
            .where(Assessment.id == assessment_id)
        )
        return result.scalar_one_or_none()

    async def list_for_student(
        self,
        student_id: uuid.UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[Assessment]:
        """List assessments filtered by student and optional date range."""
        query = (
            select(Assessment)
            .where(Assessment.student_id == student_id)
            .order_by(Assessment.assessment_date.desc())
        )
        if from_date:
            query = query.where(Assessment.assessment_date >= from_date)
        if to_date:
            query = query.where(Assessment.assessment_date <= to_date)

        result = await self.db.execute(query)
        return list(result.scalars().all())
