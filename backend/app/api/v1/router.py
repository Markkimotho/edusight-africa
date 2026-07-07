from fastapi import APIRouter

from app.api.v1 import auth, students, assessments, predictions, observations, interventions, reports, resources, integrations, webhooks, docs, support

api_router = APIRouter()

api_router.include_router(auth.router,          prefix="/auth",          tags=["auth"])
api_router.include_router(students.router,      prefix="/students",      tags=["students"])
api_router.include_router(assessments.router,   prefix="/assessments",   tags=["assessments"])
api_router.include_router(predictions.router,   prefix="/predictions",   tags=["predictions"])
api_router.include_router(observations.router,  prefix="/observations",  tags=["observations"])
api_router.include_router(interventions.router, prefix="/interventions", tags=["interventions"])
api_router.include_router(reports.router,       prefix="/reports",       tags=["reports"])
api_router.include_router(resources.router,     prefix="/resources",     tags=["resources"])
api_router.include_router(support.router,       prefix="/support",       tags=["support"])
api_router.include_router(integrations.router,  prefix="/integrations",  tags=["integrations"])
api_router.include_router(webhooks.router,      prefix="/webhooks",      tags=["webhooks"])
api_router.include_router(docs.router,          prefix="/docs",          tags=["docs"])
