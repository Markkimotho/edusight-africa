"""
Feature engineering for EduSight Africa ML pipeline.

Provides two public functions:
  - engineer_features(df)          — batch DataFrame transformation
  - prepare_prediction_features()  — single-record dict → numpy array
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Ordered list of numeric feature columns that the model expects.
# The scaler and classifier were trained on exactly these columns in this order.
# ---------------------------------------------------------------------------

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
    # Engineered
    "score_gap",
    "avg_academic",
    "academic_behavior_mismatch",
    # One-hot encoded categoricals
    "school_type_community",
    "school_type_private",
    "school_type_public",
    "gender_female",
    "gender_male",
]

# Categorical columns and their expected categories (for consistent encoding)
_SCHOOL_TYPE_CATS = ["community", "private", "public"]
_GENDER_CATS = ["female", "male"]


# ---------------------------------------------------------------------------
# Batch feature engineering
# ---------------------------------------------------------------------------


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived numeric features and one-hot encode categoricals.

    Parameters
    ----------
    df : pd.DataFrame
        Raw student records. Must contain at minimum:
        math_score, reading_score, writing_score, behavior_rating,
        home_engagement_composite, school_type, gender, grade_level, age,
        attendance_pct, literacy_level, score_trend.

    Returns
    -------
    pd.DataFrame
        Original columns plus engineered features; categorical columns are
        replaced by one-hot dummies.
    """
    df = df.copy()

    # --- Core derived features -------------------------------------------
    df["score_gap"] = (
        df[["math_score", "reading_score", "writing_score"]].max(axis=1)
        - df[["math_score", "reading_score", "writing_score"]].min(axis=1)
    )

    df["avg_academic"] = (
        df[["math_score", "reading_score", "writing_score"]].mean(axis=1)
    )

    # academic_behavior_mismatch: how far the normalised academic average
    # is from the behaviour rating on the same 1-5 scale.
    df["academic_behavior_mismatch"] = abs(
        df["avg_academic"] / 20.0 - df["behavior_rating"]
    )

    # --- One-hot encode school_type ---------------------------------------
    school_dummies = pd.get_dummies(
        pd.Categorical(df["school_type"], categories=_SCHOOL_TYPE_CATS),
        prefix="school_type",
    )
    df = pd.concat([df.drop(columns=["school_type"]), school_dummies], axis=1)

    # --- One-hot encode gender -------------------------------------------
    gender_dummies = pd.get_dummies(
        pd.Categorical(df["gender"], categories=_GENDER_CATS),
        prefix="gender",
    )
    df = pd.concat([df.drop(columns=["gender"]), gender_dummies], axis=1)

    return df


# ---------------------------------------------------------------------------
# Single-record prediction helper
# ---------------------------------------------------------------------------

_REQUIRED_RAW_FIELDS = [
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
    "school_type",
    "gender",
]


def prepare_prediction_features(assessment_data: dict) -> np.ndarray:
    """
    Convert a single student assessment dict to a model input array.

    Parameters
    ----------
    assessment_data : dict
        Must contain keys: math_score, reading_score, writing_score,
        attendance_pct, behavior_rating, literacy_level,
        home_engagement_composite, score_trend, grade_level, age,
        school_type ('public'|'private'|'community'), gender ('male'|'female').

    Returns
    -------
    np.ndarray, shape (1, n_features)
        Feature array in the order defined by MODEL_FEATURE_COLUMNS, ready
        for StandardScaler → classifier.

    Raises
    ------
    ValueError
        If required fields are missing or values are out of expected range.
    """
    # --- Validate required fields ----------------------------------------
    missing = [f for f in _REQUIRED_RAW_FIELDS if f not in assessment_data]
    if missing:
        raise ValueError(f"Missing required assessment fields: {missing}")

    data = dict(assessment_data)

    # --- Derive engineered features --------------------------------------
    scores = [data["math_score"], data["reading_score"], data["writing_score"]]
    data["score_gap"] = max(scores) - min(scores)
    data["avg_academic"] = sum(scores) / 3.0
    data["academic_behavior_mismatch"] = abs(
        data["avg_academic"] / 20.0 - data["behavior_rating"]
    )

    # --- One-hot encode school_type --------------------------------------
    school_type = str(data.get("school_type", "public")).lower()
    if school_type not in _SCHOOL_TYPE_CATS:
        raise ValueError(
            f"school_type must be one of {_SCHOOL_TYPE_CATS}, got '{school_type}'"
        )
    for cat in _SCHOOL_TYPE_CATS:
        data[f"school_type_{cat}"] = int(school_type == cat)

    # --- One-hot encode gender ------------------------------------------
    gender = str(data.get("gender", "male")).lower()
    if gender not in _GENDER_CATS:
        raise ValueError(
            f"gender must be one of {_GENDER_CATS}, got '{gender}'"
        )
    for cat in _GENDER_CATS:
        data[f"gender_{cat}"] = int(gender == cat)

    # --- Assemble in the canonical column order --------------------------
    try:
        feature_vector = np.array(
            [float(data[col]) for col in MODEL_FEATURE_COLUMNS],
            dtype=np.float64,
        ).reshape(1, -1)
    except KeyError as exc:
        raise ValueError(f"Engineered feature key not found: {exc}") from exc

    return feature_vector


# ---------------------------------------------------------------------------
# Convenience: select only model columns from an engineered DataFrame
# ---------------------------------------------------------------------------


def select_model_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return only the columns that the trained model expects, in the correct order.

    Parameters
    ----------
    df : pd.DataFrame
        An already-engineered DataFrame (output of engineer_features).

    Returns
    -------
    pd.DataFrame
        Subset of df with exactly MODEL_FEATURE_COLUMNS, in order.
    """
    missing = [c for c in MODEL_FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Engineered DataFrame is missing expected model columns: {missing}"
        )
    return df[MODEL_FEATURE_COLUMNS]
