"""
Reports endpoints: school analytics and CSV export.
"""

from __future__ import annotations

import uuid
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import io

from app.api.deps import get_current_active_user, require_roles, DBSession
from app.models.user import User, UserRole
from app.services.report_service import ReportService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/school/{school_id}")
async def school_analytics(
    school_id: uuid.UUID,
    db: DBSession,
    current_user: User = Depends(require_roles(UserRole.admin, UserRole.superadmin, UserRole.teacher)),
) -> dict[str, Any]:
    """
    Return aggregate analytics for a school: student counts, risk distribution,
    average scores, and active interventions count.
    """
    service = ReportService(db)
    data = await service.school_analytics(school_id)
    return {"data": data}


@router.get("/export")
async def export_csv(
    school_id: uuid.UUID,
    db: DBSession,
    current_user: User = Depends(require_roles(UserRole.admin, UserRole.superadmin)),
) -> StreamingResponse:
    """
    Generate and stream a CSV export of all active students for a school.

    Query param:
        school_id (UUID): the school to export
    """
    service = ReportService(db)
    csv_content = await service.generate_student_csv(school_id)

    stream = io.StringIO(csv_content)
    filename = f"students_school_{school_id}.csv"
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
