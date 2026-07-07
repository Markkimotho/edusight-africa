from __future__ import annotations

from typing import Any

import httpx


class EduSightClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 15.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/integrations/predict", json=payload)

    def ingest_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/integrations/events", json=payload)

    def model_version(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/integrations/model-version")

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        response = httpx.request(
            method,
            f"{self.base_url}{path}",
            headers={"X-API-Key": self.api_key, "Content-Type": "application/json"},
            timeout=self.timeout,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()
