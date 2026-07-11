"""
Tests for app.ml.features — rule-based feature engineering and scoring.
"""

from __future__ import annotations

import pytest

from app.ml.features import (
    FeatureVector,
    compute_features,
    compute_weighted_score,
    from_assessment_dict,
    FEATURE_WEIGHTS,
    BASE_SCORE,
)


# ---------------------------------------------------------------------------
# from_assessment_dict
# ---------------------------------------------------------------------------


def test_from_assessment_dict_all_fields():
    """Should create a FeatureVector from a complete assessment dict."""
    data = {
        "math_score": 80.0,
        "reading_score": 75.0,
        "writing_score": 70.0,
        "attendance_pct": 92.0,
        "behavior_rating": 4,
        "literacy_level": 8,
    }
    fv = from_assessment_dict(data)
    assert fv.math_score == 80.0
    assert fv.reading_score == 75.0
    assert fv.writing_score == 70.0
    assert fv.attendance_pct == 92.0
    assert fv.behavior_rating == 4
    assert fv.literacy_level == 8


def test_from_assessment_dict_missing_fields():
    """Missing keys should produce None values in the FeatureVector."""
    fv = from_assessment_dict({})
    assert fv.math_score is None
    assert fv.reading_score is None
    assert fv.writing_score is None
    assert fv.attendance_pct is None
    assert fv.behavior_rating is None
    assert fv.literacy_level is None


# ---------------------------------------------------------------------------
# compute_features
# ---------------------------------------------------------------------------


def test_compute_features_normalises_values():
    """Features should be normalised to [0, 1]."""
    fv = FeatureVector(
        math_score=100.0,  # max → 1.0
        reading_score=0.0,  # min → 0.0
        writing_score=50.0,  # mid → 0.5
        attendance_pct=75.0,  # 0.75
        behavior_rating=3,  # (3-1)/(5-1) = 0.5
        literacy_level=5,  # (5-1)/(10-1) ≈ 0.444
    )
    normalised = compute_features(fv)

    assert normalised["math_score"] == pytest.approx(1.0)
    assert normalised["reading_score"] == pytest.approx(0.0)
    assert normalised["writing_score"] == pytest.approx(0.5)
    assert normalised["attendance_pct"] == pytest.approx(0.75)
    assert normalised["behavior_rating"] == pytest.approx(0.5)
    assert normalised["literacy_level"] == pytest.approx(4 / 9, abs=0.01)


def test_compute_features_fills_missing_with_midpoints():
    """None values should be filled with domain midpoints before normalising."""
    fv = FeatureVector(
        math_score=None,
        reading_score=None,
        writing_score=None,
        attendance_pct=None,
        behavior_rating=None,
        literacy_level=None,
    )
    normalised = compute_features(fv)

    # All should be at their midpoint normalisation
    assert normalised["math_score"] == pytest.approx(0.5)  # 50/100
    assert normalised["reading_score"] == pytest.approx(0.5)
    assert normalised["writing_score"] == pytest.approx(0.5)
    assert normalised["attendance_pct"] == pytest.approx(0.75)  # 75/100
    assert normalised["behavior_rating"] == pytest.approx(0.5)  # (3-1)/(5-1)
    assert normalised["literacy_level"] == pytest.approx(4 / 9, abs=0.01)  # (5-1)/(10-1)


# ---------------------------------------------------------------------------
# compute_weighted_score
# ---------------------------------------------------------------------------


def test_compute_weighted_score_average_student():
    """An average student (all features at midpoint) should score around 0.5."""
    fv = FeatureVector(
        math_score=50.0,
        reading_score=50.0,
        writing_score=50.0,
        attendance_pct=75.0,
        behavior_rating=3,
        literacy_level=5,
    )
    normalised = compute_features(fv)
    risk_prob, contributions = compute_weighted_score(normalised)

    # Should be in the moderate range
    assert 0.3 <= risk_prob <= 0.7


def test_compute_weighted_score_high_achieving_student():
    """A student with perfect scores should have low risk."""
    fv = FeatureVector(
        math_score=100.0,
        reading_score=100.0,
        writing_score=100.0,
        attendance_pct=100.0,
        behavior_rating=5,
        literacy_level=10,
    )
    normalised = compute_features(fv)
    risk_prob, contributions = compute_weighted_score(normalised)

    # Low risk → probability near 0
    assert risk_prob == 0.0


def test_compute_weighted_score_struggling_student():
    """A student with very low scores should have high risk."""
    fv = FeatureVector(
        math_score=0.0,
        reading_score=0.0,
        writing_score=0.0,
        attendance_pct=0.0,
        behavior_rating=1,
        literacy_level=1,
    )
    normalised = compute_features(fv)
    risk_prob, contributions = compute_weighted_score(normalised)

    # High risk → probability near 1
    assert risk_prob == 1.0


def test_compute_weighted_score_contributions_are_returned():
    """Each feature should have a corresponding contribution value."""
    normalised = {
        "math_score": 0.7,
        "reading_score": 0.6,
        "writing_score": 0.5,
        "attendance_pct": 0.8,
        "behavior_rating": 0.5,
        "literacy_level": 0.4,
    }
    risk_prob, contributions = compute_weighted_score(normalised)

    assert set(contributions.keys()) == set(FEATURE_WEIGHTS.keys())
    # Each contribution = weight * normalised_value
    for feature, weight in FEATURE_WEIGHTS.items():
        expected = round(weight * normalised[feature], 4)
        assert contributions[feature] == expected


def test_compute_weighted_score_clamped_to_zero_one():
    """Risk probability should always be clamped to [0, 1]."""
    # Use extreme values that would push the score beyond bounds
    extreme_high = {k: 0.0 for k in FEATURE_WEIGHTS}  # All at zero → max risk
    risk_prob, _ = compute_weighted_score(extreme_high)
    assert 0.0 <= risk_prob <= 1.0

    extreme_low = {k: 1.0 for k in FEATURE_WEIGHTS}  # All at max → min risk
    risk_prob, _ = compute_weighted_score(extreme_low)
    assert 0.0 <= risk_prob <= 1.0
