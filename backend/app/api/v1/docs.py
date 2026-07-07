"""Partner documentation helpers."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/openapi.json", include_in_schema=False)
async def openapi_alias(request: Request) -> dict:
    return request.app.openapi()
