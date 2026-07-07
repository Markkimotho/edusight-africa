"""Webhook utilities for partner integration testing."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from app.api.deps import PartnerAuth
from app.schemas.integration import WebhookTestPayload

router = APIRouter()


@router.post("/test")
async def test_webhook(payload: WebhookTestPayload, partner: PartnerAuth) -> dict:
    return {
        "accepted": True,
        "event_type": payload.event_type,
        "target_url": payload.target_url,
        "delivered": False,
        "message": "Webhook test accepted. Outbound delivery is disabled in local mode.",
        "timestamp": datetime.utcnow().isoformat(),
    }
