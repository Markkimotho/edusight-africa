"""
Feature engineering for the EduSight Africa risk model.

All feature weights are calibrated so that an "average" student produces a
weighted_score near 0.5, and extreme values push it towards 0 (low risk)
or 1 (high risk).
"""

from dataclasses import dataclass
from typing import Any


# --- Feature weights ---------------------------------------------------------
# Each weight represents the contribution of that feature to the overall risk
# score.  Positive weight = higher value → higher risk.
FEATURE_WEIGHTS: dict[str, float] = {
    "math_score":        -0.20,   # higher score → lower risk
    "reading_score":     -0.20,
    "writing_score":     -0.15,
    "attendance_pct":    -0.20,   # higher attendance → lower risk
    "behavior_rating":   -0.10,   # higher rating → lower risk
    "literacy_level":    -0.15,   # higher literacy → lower risk
}

# Bias term so that a perfectly average student sits at ~0.5
BASE_SCORE: float = 1.0


@dataclass
class FeatureVector:
    math_score: float | None
    reading_score: float | None
    writing_score: float | None
    attendance_pct: float | None
    behavior_rating: int | None
    literacy_level: int | None


def _normalise(value: float, min_val: float, max_val: float) -> float:
    """Normalise a value to [0, 1]."""
    if max_val == min_val:
        return 0.5
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def _fill_missing(fv: FeatureVector) -> dict[str, float]:
    """
    Replace None values with domain-midpoints so that missing data does not
    heavily skew the prediction.
    """
    return {
        "math_score":      fv.math_score      if fv.math_score      is not None else 50.0,
        "reading_score":   fv.reading_score   if fv.reading_score   is not None else 50.0,
        "writing_score":   fv.writing_score   if fv.writing_score   is not None else 50.0,
        "attendance_pct":  fv.attendance_pct  if fv.attendance_pct  is not None else 75.0,
        "behavior_rating": float(fv.behavior_rating if fv.behavior_rating is not None else 3),
        "literacy_level":  float(fv.literacy_level  if fv.literacy_level  is not None else 5),
    }


def _normalise_features(raw: dict[str, float]) -> dict[str, float]:
    """Normalise each feature to [0, 1] using its known domain bounds."""
    bounds: dict[str, tuple[float, float]] = {
        "math_score":      (0,  100),
        "reading_score":   (0,  100),
        "writing_score":   (0,  100),
        "attendance_pct":  (0,  100),
        "behavior_rating": (1,    5),
        "literacy_level":  (1,   10),
    }
    return {k: _normalise(v, *bounds[k]) for k, v in raw.items()}


def compute_features(fv: FeatureVector) -> dict[str, float]:
    """Return the normalised feature dict for a given FeatureVector."""
    raw = _fill_missing(fv)
    return _normalise_features(raw)


def compute_weighted_score(normalised: dict[str, float]) -> tuple[float, dict[str, float]]:
    """
    Compute a scalar risk probability in [0, 1] and per-feature contributions.

    Returns:
        (risk_probability, contributions_dict)
    """
    contributions: dict[str, float] = {}
    score = BASE_SCORE

    for feature, weight in FEATURE_WEIGHTS.items():
        norm_val = normalised.get(feature, 0.5)
        contribution = weight * norm_val
        contributions[feature] = round(contribution, 4)
        score += contribution

    # Clamp to [0, 1]
    risk_probability = max(0.0, min(1.0, score))
    return round(risk_probability, 4), contributions


def from_assessment_dict(data: dict[str, Any]) -> FeatureVector:
    """Build a FeatureVector from a raw assessment data dict."""
    return FeatureVector(
        math_score=data.get("math_score"),
        reading_score=data.get("reading_score"),
        writing_score=data.get("writing_score"),
        attendance_pct=data.get("attendance_pct"),
        behavior_rating=data.get("behavior_rating"),
        literacy_level=data.get("literacy_level"),
    )
