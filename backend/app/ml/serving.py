"""Model serving layer with trained-model support and a rule-based fallback."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.config import settings
from app.ml.features import (
    FeatureVector,
    compute_features,
    compute_weighted_score,
    from_assessment_dict,
)

logger = logging.getLogger(__name__)

# Version string that will be stored with every Prediction row produced by
# the rule-based predictor.
RULE_BASED_VERSION = "rule-based-v1.0"
TRAINED_MODEL_VERSION_PREFIX = "student-risk"

RISK_LABEL_MAP = {0: "low", 1: "medium", 2: "high", 3: "critical"}
MODEL_FEATURE_COLUMNS: list[str] = [
    "math_score",
    "reading_score",
    "writing_score",
    "attendance_pct",
    "behavior_rating",
    "literacy_level",
    "home_engagement_composite",
    "score_trend",
    "grade_level",
    "age",
    "score_gap",
    "avg_academic",
    "academic_behavior_mismatch",
    "school_type_community",
    "school_type_private",
    "school_type_public",
    "gender_female",
    "gender_male",
]


def _risk_level_from_probability(prob: float) -> str:
    """
    Map a scalar probability to a categorical risk level.

      0.00 – 0.25 → low
      0.25 – 0.50 → medium
      0.50 – 0.75 → high
      0.75 – 1.00 → critical
    """
    if prob < 0.25:
        return "low"
    elif prob < 0.50:
        return "medium"
    elif prob < 0.75:
        return "high"
    else:
        return "critical"


class PredictionResult:
    """Value object returned by the serving layer."""

    def __init__(
        self,
        risk_level: str,
        risk_probability: float,
        feature_contributions: dict[str, Any],
        model_version: str,
        confidence: str | None = None,
        data_completeness: float | None = None,
        feature_snapshot: dict[str, Any] | None = None,
    ) -> None:
        self.risk_level = risk_level
        self.risk_probability = risk_probability
        self.feature_contributions = feature_contributions
        self.model_version = model_version
        self.confidence = confidence or confidence_from_probability(risk_probability)
        self.data_completeness = data_completeness
        self.feature_snapshot = feature_snapshot or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_level": self.risk_level,
            "risk_probability": self.risk_probability,
            "feature_contributions": self.feature_contributions,
            "model_version": self.model_version,
            "confidence": self.confidence,
            "data_completeness": self.data_completeness,
            "feature_snapshot": self.feature_snapshot,
        }


class RuleBasedPredictor:
    """
    Deterministic rule-based predictor used when no trained model is present.

    The predictor computes a weighted linear combination of normalised
    assessment features, then maps the result to a risk level.
    """

    version: str = RULE_BASED_VERSION

    def predict(self, assessment_data: dict[str, Any]) -> PredictionResult:
        fv: FeatureVector = from_assessment_dict(assessment_data)
        normalised = compute_features(fv)
        risk_prob, contributions = compute_weighted_score(normalised)
        risk_level = _risk_level_from_probability(risk_prob)
        explanation = build_practical_guidance(assessment_data, risk_level, risk_prob)
        completeness = estimate_data_completeness(assessment_data)

        logger.debug(
            "Rule-based prediction: probability=%.4f level=%s",
            risk_prob,
            risk_level,
        )

        return PredictionResult(
            risk_level=risk_level,
            risk_probability=risk_prob,
            feature_contributions={
                "method": "rule_based_fallback",
                "weighted_contributions": contributions,
                **explanation,
            },
            model_version=self.version,
            confidence=confidence_from_probability(risk_prob, completeness),
            data_completeness=completeness,
            feature_snapshot={key: assessment_data.get(key) for key in sorted(assessment_data)},
        )


class TrainedModelPredictor:
    """Predictor backed by the trained sklearn pipeline artifacts."""

    def __init__(self, model: Any, scaler: Any, metadata: dict[str, Any]) -> None:
        self.model = model
        self.scaler = scaler
        self.metadata = metadata
        model_name = str(metadata.get("model_name", "model")).lower().replace(" ", "-")
        metric = metadata.get("test_metrics", {}).get("macro_f1")
        metric_suffix = f"-f1-{metric}" if metric is not None else ""
        self.version = f"{TRAINED_MODEL_VERSION_PREFIX}-{model_name}{metric_suffix}"

    def predict(self, assessment_data: dict[str, Any]) -> PredictionResult:
        feature_vector, engineered = prepare_trained_model_features(assessment_data)
        scaled = self.scaler.transform(feature_vector)
        probabilities = self.model.predict_proba(scaled)[0]
        predicted_class = max(
            range(len(probabilities)),
            key=lambda index: float(probabilities[index]),
        )
        risk_level = RISK_LABEL_MAP.get(predicted_class, "medium")
        risk_probability = float(probabilities[predicted_class])
        explanation = build_practical_guidance(assessment_data, risk_level, risk_probability)
        completeness = estimate_data_completeness(assessment_data)

        logger.debug(
            "Trained-model prediction: probability=%.4f level=%s version=%s",
            risk_probability,
            risk_level,
            self.version,
        )

        return PredictionResult(
            risk_level=risk_level,
            risk_probability=round(risk_probability, 4),
            feature_contributions={
                "method": "trained_model",
                "class_probabilities": {
                    RISK_LABEL_MAP[i]: round(float(prob), 4)
                    for i, prob in enumerate(probabilities)
                },
                "model_name": self.metadata.get("model_name"),
                "test_metrics": self.metadata.get("test_metrics"),
                "engineered_features": engineered,
                **explanation,
            },
            model_version=self.version,
            confidence=confidence_from_probability(risk_probability, completeness),
            data_completeness=completeness,
            feature_snapshot=engineered,
        )


def _resolve_project_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return (Path(__file__).resolve().parents[3] / path).resolve()


def _load_trained_predictor() -> TrainedModelPredictor | None:
    if not settings.ML_ENABLE_TRAINED_MODEL:
        return None

    model_path = _resolve_project_path(settings.ML_MODEL_PATH)
    scaler_path = _resolve_project_path(settings.ML_SCALER_PATH)
    metadata_path = _resolve_project_path(settings.ML_METADATA_PATH)

    if not model_path.exists() or not scaler_path.exists():
        logger.info("Trained ML artifacts not found; using rule-based fallback")
        return None

    try:
        import joblib

        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        metadata = {}
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        logger.info("Loaded trained risk model from %s", model_path)
        return TrainedModelPredictor(model=model, scaler=scaler, metadata=metadata)
    except Exception as exc:
        logger.warning("Could not load trained risk model; using fallback: %s", exc)
        return None


def estimate_data_completeness(data: dict[str, Any]) -> float:
    expected = [
        "math_score",
        "reading_score",
        "writing_score",
        "attendance_pct",
        "behavior_rating",
        "literacy_level",
        "grade_level",
        "age",
    ]
    present = sum(1 for key in expected if data.get(key) is not None)
    return round(present / len(expected), 4)


def missing_data_warnings(data: dict[str, Any]) -> list[dict[str, str]]:
    required = {
        "grade_level": "Add the learner's grade/class.",
        "age": "Add age or date-of-birth-derived age.",
        "gender": "Add gender only where policy and consent allow it.",
        "attendance_pct": "Add recent attendance or attendance percentage.",
        "behavior_rating": "Add at least one teacher observation or behavior rating.",
    }
    academic_present = any(data.get(key) is not None for key in ("math_score", "reading_score", "writing_score"))
    warnings = [
        {"feature": key, "recommendation": recommendation}
        for key, recommendation in required.items()
        if data.get(key) is None
    ]
    if not academic_present:
        warnings.append(
            {
                "feature": "academic_score",
                "recommendation": "Add at least one recent academic score or curriculum competency result.",
            }
        )
    return warnings


def confidence_from_probability(probability: float, data_completeness: float | None = None) -> str:
    completeness = 1.0 if data_completeness is None else data_completeness
    distance_from_boundary = abs((probability % 0.25) - 0.125) / 0.125
    score = (0.65 * completeness) + (0.35 * distance_from_boundary)
    if score >= 0.72:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _num(data: dict[str, Any], key: str, default: float) -> float:
    value = data.get(key)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def prepare_trained_model_features(assessment_data: dict[str, Any]) -> tuple[list[list[float]], dict[str, float]]:
    """Build the exact numeric feature vector expected by the trained model."""
    math_score = _num(assessment_data, "math_score", 50.0)
    reading_score = _num(assessment_data, "reading_score", 50.0)
    writing_score = _num(assessment_data, "writing_score", 50.0)
    attendance_pct = _num(assessment_data, "attendance_pct", 75.0)
    behavior_rating = _num(assessment_data, "behavior_rating", 3.0)
    literacy_level = _num(assessment_data, "literacy_level", 5.0)
    home_engagement = _num(assessment_data, "home_engagement_composite", 0.5)
    score_trend = _num(assessment_data, "score_trend", 0.0)
    grade_level = _num(assessment_data, "grade_level", 5.0)
    age = _num(assessment_data, "age", 11.0)

    scores = [math_score, reading_score, writing_score]
    avg_academic = sum(scores) / 3.0
    engineered: dict[str, float] = {
        "math_score": math_score,
        "reading_score": reading_score,
        "writing_score": writing_score,
        "attendance_pct": attendance_pct,
        "behavior_rating": behavior_rating,
        "literacy_level": literacy_level,
        "home_engagement_composite": home_engagement,
        "score_trend": score_trend,
        "grade_level": grade_level,
        "age": age,
        "score_gap": max(scores) - min(scores),
        "avg_academic": avg_academic,
        "academic_behavior_mismatch": abs(avg_academic / 20.0 - behavior_rating),
    }

    school_type = str(assessment_data.get("school_type") or "public").lower()
    if school_type not in {"community", "private", "public"}:
        school_type = "public"
    for option in ("community", "private", "public"):
        engineered[f"school_type_{option}"] = float(school_type == option)

    gender = str(assessment_data.get("gender") or "").lower()
    if gender not in {"female", "male"}:
        gender = "female"
    for option in ("female", "male"):
        engineered[f"gender_{option}"] = float(gender == option)

    feature_vector = [[float(engineered[column]) for column in MODEL_FEATURE_COLUMNS]]
    return feature_vector, {key: round(value, 4) for key, value in engineered.items()}


def build_practical_guidance(
    assessment_data: dict[str, Any],
    risk_level: str,
    risk_probability: float,
) -> dict[str, Any]:
    """Return teacher-facing risk drivers and next-best interventions."""
    drivers: list[dict[str, Any]] = []

    def add_driver(feature: str, label: str, severity: str, value: Any, recommendation: str) -> None:
        drivers.append(
            {
                "feature": feature,
                "label": label,
                "severity": severity,
                "value": value,
                "recommendation": recommendation,
            }
        )

    attendance = assessment_data.get("attendance_pct")
    if attendance is not None and float(attendance) < 85:
        severity = "high" if float(attendance) < 70 else "medium"
        add_driver(
            "attendance_pct",
            "Attendance below target",
            severity,
            round(float(attendance), 1),
            "Follow up with the guardian and agree on a weekly attendance target.",
        )

    literacy = assessment_data.get("literacy_level")
    if literacy is not None and float(literacy) <= 4:
        add_driver(
            "literacy_level",
            "Foundational literacy support needed",
            "high",
            literacy,
            "Schedule short daily reading practice and pair the learner with targeted phonics or comprehension work.",
        )

    scores = {
        "math_score": assessment_data.get("math_score"),
        "reading_score": assessment_data.get("reading_score"),
        "writing_score": assessment_data.get("writing_score"),
    }
    low_subjects = [
        key.replace("_score", "")
        for key, value in scores.items()
        if value is not None and float(value) < 50
    ]
    if low_subjects:
        add_driver(
            "academic_scores",
            "Low subject performance",
            "high" if len(low_subjects) >= 2 else "medium",
            low_subjects,
            "Create a two-week remediation plan focused on the lowest subject areas, then reassess.",
        )

    behavior = assessment_data.get("behavior_rating")
    if behavior is not None and int(behavior) <= 2:
        add_driver(
            "behavior_rating",
            "Classroom engagement concern",
            "medium",
            behavior,
            "Use a teacher check-in and positive behavior goal before escalating to disciplinary action.",
        )

    if not drivers:
        drivers.append(
            {
                "feature": "overall_profile",
                "label": "No single severe driver detected",
                "severity": "low",
                "value": risk_level,
                "recommendation": "Continue routine monitoring and compare against the learner's next assessment.",
            }
        )

    priority = "routine"
    if risk_level in {"high", "critical"} or risk_probability >= 0.65:
        priority = "urgent"
    elif risk_level == "medium" or risk_probability >= 0.4:
        priority = "watch"

    return {
        "risk_drivers": drivers[:4],
        "recommended_actions": [driver["recommendation"] for driver in drivers[:3]],
        "intervention_priority": priority,
        "missing_data_warnings": missing_data_warnings(assessment_data),
        "fairness_caution": (
            "Review local context and avoid using sensitive characteristics as the reason "
            "for intervention. This signal is for support planning only."
        ),
        "explanation": (
            "This is a decision-support signal for educators, not a final judgment "
            "about the learner. Review local context before acting."
        ),
    }


# Module-level singleton predictor.
_predictor: TrainedModelPredictor | RuleBasedPredictor | None = None


def get_predictor() -> TrainedModelPredictor | RuleBasedPredictor:
    """Return the shared predictor instance (lazy init)."""
    global _predictor
    if _predictor is None:
        _predictor = _load_trained_predictor() or RuleBasedPredictor()
    return _predictor


def predict_from_assessment(assessment_data: dict[str, Any]) -> PredictionResult:
    """
    Public entry-point used by PredictionService.

    Args:
        assessment_data: Dict with optional keys matching Assessment fields
                         (math_score, reading_score, etc.).

    Returns:
        A PredictionResult with risk level, probability, and per-feature
        contribution breakdown.
    """
    return get_predictor().predict(assessment_data)


def get_model_info() -> dict[str, Any]:
    predictor = get_predictor()
    metadata = getattr(predictor, "metadata", {}) or {}
    return {
        "version": predictor.version,
        "method": metadata.get("model_name", "rule_based_fallback"),
        "trained_model_enabled": isinstance(predictor, TrainedModelPredictor),
        "feature_names": metadata.get("feature_names", MODEL_FEATURE_COLUMNS),
        "metadata": metadata,
    }
