"""
Model serving layer.

Currently uses a rule-based fallback predictor.  When a trained scikit-learn
model pickle is available it can be loaded here and used instead.
"""

from __future__ import annotations

import logging
from typing import Any

from app.ml.features import (
    FeatureVector,
    compute_features,
    compute_weighted_score,
    from_assessment_dict,
)
from app.models.prediction import RiskLevel

logger = logging.getLogger(__name__)

# Version string that will be stored with every Prediction row produced by
# the rule-based predictor.
RULE_BASED_VERSION = "rule-based-v1.0"


def _risk_level_from_probability(prob: float) -> RiskLevel:
    """
    Map a scalar probability to a categorical risk level.

      0.00 – 0.25 → low
      0.25 – 0.50 → medium
      0.50 – 0.75 → high
      0.75 – 1.00 → critical
    """
    if prob < 0.25:
        return RiskLevel.low
    elif prob < 0.50:
        return RiskLevel.medium
    elif prob < 0.75:
        return RiskLevel.high
    else:
        return RiskLevel.critical


class PredictionResult:
    """Value object returned by the serving layer."""

    def __init__(
        self,
        risk_level: RiskLevel,
        risk_probability: float,
        feature_contributions: dict[str, Any],
        model_version: str,
    ) -> None:
        self.risk_level = risk_level
        self.risk_probability = risk_probability
        self.feature_contributions = feature_contributions
        self.model_version = model_version

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_level": self.risk_level.value,
            "risk_probability": self.risk_probability,
            "feature_contributions": self.feature_contributions,
            "model_version": self.model_version,
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

        logger.debug(
            "Rule-based prediction: probability=%.4f level=%s",
            risk_prob,
            risk_level.value,
        )

        return PredictionResult(
            risk_level=risk_level,
            risk_probability=risk_prob,
            feature_contributions=contributions,
            model_version=self.version,
        )


# Module-level singleton predictor — swap for a real model loader when ready.
_predictor: RuleBasedPredictor | None = None


def get_predictor() -> RuleBasedPredictor:
    """Return the shared predictor instance (lazy init)."""
    global _predictor
    if _predictor is None:
        _predictor = RuleBasedPredictor()
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
