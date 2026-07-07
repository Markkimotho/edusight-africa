# EduSight Africa Partner Integration

EduSight can run as a full school-facing platform or as a risk-intelligence module embedded inside another edtech product.

The integration API is designed for early-warning support workflows. It must not be used to punish, exclude, rank, or stigmatize students.

## Authentication

Partner endpoints use an `X-API-Key` header.

```http
X-API-Key: esa_your_partner_key
```

For first deployments, bootstrap keys can be configured with:

```env
PARTNER_API_KEYS=esa_dev_key_one,esa_dev_key_two
```

Production keys should be created by an admin through:

```http
POST /api/v1/integrations/api-keys
Authorization: Bearer <admin-jwt>
```

Keys are stored as SHA-256 hashes and the raw key is only returned once.

## Health Check

```http
GET /api/v1/integrations/health
X-API-Key: esa_your_partner_key
```

Response:

```json
{
  "status": "ok",
  "module": "edusight-risk-intelligence",
  "authenticated": true
}
```

## Model Version

```http
GET /api/v1/integrations/model-version
X-API-Key: esa_your_partner_key
```

Use this endpoint to log which model produced each partner-side decision.

## Persisted Student Workflow

Use this flow when a partner wants EduSight to keep the student mapping and latest support signal.

```http
POST /api/v1/integrations/students
POST /api/v1/integrations/assessments
POST /api/v1/integrations/events
GET /api/v1/integrations/students/{student_id}/risk
GET /api/v1/integrations/students/{student_id}/recommendations
```

## Direct Prediction

```http
POST /api/v1/integrations/predict
X-API-Key: esa_your_partner_key
Content-Type: application/json
```

Example request:

```json
{
  "external_student_id": "sis-1042",
  "grade_level": 6,
  "age": 12,
  "gender": "female",
  "school_type": "public",
  "math_score": 44,
  "reading_score": 51,
  "writing_score": 47,
  "attendance_pct": 68,
  "behavior_rating": 3,
  "literacy_level": 5,
  "home_engagement_composite": 0.42,
  "score_trend": -0.3
}
```

Example response:

```json
{
  "external_student_id": "sis-1042",
  "student_id": null,
  "model_version": "rule-based-v1.0",
  "support_level": "urgent",
  "risk_level": "high",
  "risk_probability": 0.68,
  "calibrated_probability": 0.68,
  "confidence": "medium",
  "data_completeness": 1.0,
  "missing_data_warnings": [],
  "risk_drivers": [
    {
      "feature": "attendance_pct",
      "label": "Attendance below target",
      "severity": "high",
      "value": 68,
      "recommendation": "Follow up with the guardian and agree on a weekly attendance target."
    }
  ],
  "recommended_actions": [
    "Follow up with the guardian and agree on a weekly attendance target."
  ],
  "suggested_intervention_plan": [
    {
      "step": 1,
      "action": "Follow up with the guardian and agree on a weekly attendance target.",
      "owner": "teacher",
      "review_in_days": 14
    }
  ],
  "intervention_priority": "urgent",
  "explanation": "This is a decision-support signal for educators, not a final judgment about the learner. Review local context before acting.",
  "teacher_explanation": "This is a decision-support signal for educators, not a final judgment about the learner. Review local context before acting.",
  "parent_explanation": "The school has identified practical support steps to help the learner stay engaged. Please review teacher-approved recommendations rather than raw risk scores.",
  "fairness_caution": "Review local context and avoid using sensitive characteristics as the reason for intervention. This signal is for support planning only.",
  "feature_snapshot": {}
}
```

## SDKs

Early SDK stubs are available in:

- `sdk/typescript`
- `sdk/python`

They cover prediction, event ingestion, and model-version checks.

## Required Partner Behavior

- Store the returned `model_version` with any downstream action.
- Show support language instead of deterministic dropout labels.
- Keep a human review step before high-impact interventions.
- Do not expose raw probabilities to students or guardians unless the school has explicitly approved that workflow.
- Log which staff member viewed and acted on each recommendation.

## Recommended Integration Pattern

1. Send attendance, assessment, and behavior events to your own system of record.
2. Call EduSight when new information changes the learner profile.
3. Display `support_level`, `risk_drivers`, and `recommended_actions` in the teacher workflow.
4. Store teacher decisions and intervention outcomes.
5. Use outcome data to retrain and calibrate future models.
