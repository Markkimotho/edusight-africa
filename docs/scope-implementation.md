# Scope Implementation

This build turns `scope.md` into a practical V1 platform and integration module.

## V1 Included

- Full FastAPI and Next.js platform.
- Mobile-first teacher/admin dashboard and support queue.
- Partner API key authentication.
- Integration endpoints for students, events, assessments, prediction, model version, risk, recommendations, and webhook testing.
- Explainability-first prediction response with confidence, calibrated probability, missing-data warnings, teacher explanation, parent-safe explanation, suggested intervention plan, model version, and feature snapshot.
- PWA manifest, service worker, offline fallback, and mobile navigation.
- TypeScript and Python SDK stubs.
- ML pipeline with calibration, model metadata, deployment gates, fairness metrics, and evaluation reporting.

## V1 Guardrails

- Predictions are support signals, not discipline, exclusion, or ranking tools.
- Parent-facing language should show practical support recommendations, not raw probabilities.
- Sensitive attributes are restricted from direct prediction use and should only be used for aggregate fairness review where consent and law allow.
- Sparse-data cases return warnings and low-confidence guidance.
- Urgent/high cases require human review.

## Integration Endpoints

Use `X-API-Key` for partner requests.

- `POST /api/v1/integrations/students`
- `POST /api/v1/integrations/events`
- `POST /api/v1/integrations/assessments`
- `POST /api/v1/integrations/predict`
- `GET /api/v1/integrations/students/{student_id}/risk`
- `GET /api/v1/integrations/students/{student_id}/recommendations`
- `GET /api/v1/integrations/model-version`
- `GET /api/v1/integrations/health`
- `POST /api/v1/webhooks/test`
- `GET /api/v1/docs/openapi.json`

## Roadmap

- Real outbound webhook delivery with retry and signing.
- Import review workflow with persisted jobs.
- Tenant-configurable thresholds and branding stored in database.
- Full audit log viewer.
- Offline write queue with conflict resolution UI.
- Production model registry approval and rollback UI.
- LTI, OAuth/OIDC, and embeddable iframe packaging.
