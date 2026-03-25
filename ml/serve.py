"""
EduSight Africa — Model Serving Module

Usage:
    from ml.serve import ModelServer

    server = ModelServer(
        model_path="ml/models/xgb_model.pkl",
        scaler_path="ml/models/scaler.pkl",
    )
    result = server.predict({
        "math_score": 45.0,
        "reading_score": 50.0,
        "writing_score": 48.0,
        "attendance_pct": 62.0,
        "behavior_rating": 2,
        "literacy_level": 4,
        "home_engagement_composite": 0.35,
        "score_trend": -0.2,
        "grade_level": 6,
        "age": 12,
        "school_type": "public",
        "gender": "female",
    })
    print(result)
    # {
    #   "risk_level": "high",
    #   "risk_probability": 0.72,
    #   "all_probabilities": {"low": 0.05, "medium": 0.23, "high": 0.72, "critical": 0.00},
    #   "feature_contributions": {"avg_academic": -0.31, "attendance_pct": -0.28, ...},
    # }
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RISK_LABEL_MAP: dict[int, str] = {
    0: "low",
    1: "medium",
    2: "high",
    3: "critical",
}

# Default paths (relative to project root)
_DEFAULT_MODEL_PATH = Path(__file__).parent / "models" / "xgb_model.pkl"
_DEFAULT_SCALER_PATH = Path(__file__).parent / "models" / "scaler.pkl"
_METADATA_PATH = Path(__file__).parent / "models" / "model_metadata.json"


# ---------------------------------------------------------------------------
# ModelServer
# ---------------------------------------------------------------------------


class ModelServer:
    """
    Wraps a trained, calibrated scikit-learn classifier and provides a
    high-level `predict` interface suitable for the EduSight Africa API.

    Parameters
    ----------
    model_path : str | Path
        Path to the pickled calibrated classifier (joblib format).
    scaler_path : str | Path
        Path to the pickled StandardScaler (joblib format).
    lazy_load : bool
        If True (default), delay loading until the first call to predict().
        Useful when the server module is imported at app startup.
    """

    def __init__(
        self,
        model_path: str | Path = _DEFAULT_MODEL_PATH,
        scaler_path: str | Path = _DEFAULT_SCALER_PATH,
        lazy_load: bool = True,
    ) -> None:
        self.model_path = Path(model_path)
        self.scaler_path = Path(scaler_path)
        self._model = None
        self._scaler = None
        self._feature_names: list[str] | None = None

        if not lazy_load:
            self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load model and scaler from disk."""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}\n"
                "Run 'python ml/train_model.py' to train and save the model."
            )
        if not self.scaler_path.exists():
            raise FileNotFoundError(
                f"Scaler file not found: {self.scaler_path}\n"
                "Run 'python ml/train_model.py' to train and save the scaler."
            )

        self._model = joblib.load(self.model_path)
        self._scaler = joblib.load(self.scaler_path)

        # Try to load feature names from metadata
        if _METADATA_PATH.exists():
            with open(_METADATA_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self._feature_names = meta.get("feature_names")

    def _ensure_loaded(self) -> None:
        if self._model is None or self._scaler is None:
            self._load()

    @property
    def feature_names(self) -> list[str]:
        self._ensure_loaded()
        if self._feature_names is None:
            # Fall back to importing from features module
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from features import MODEL_FEATURE_COLUMNS  # type: ignore[import]
            self._feature_names = MODEL_FEATURE_COLUMNS
        return self._feature_names  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Feature contribution via perturbation (model-agnostic)
    # ------------------------------------------------------------------

    def _compute_feature_contributions(
        self,
        X_scaled: np.ndarray,
        base_class: int,
    ) -> dict[str, float]:
        """
        Estimate per-feature contribution using leave-one-out perturbation.

        Each feature is zeroed out (set to 0 in the scaled space, i.e. mean
        in original space) one at a time, and the change in predicted
        probability for `base_class` is recorded as the contribution.

        Returns a dict {feature_name: contribution} sorted by absolute value.
        """
        assert self._model is not None

        base_proba = self._model.predict_proba(X_scaled)[0, base_class]
        n_features = X_scaled.shape[1]
        contributions: dict[str, float] = {}

        for i, feat_name in enumerate(self.feature_names):
            perturbed = X_scaled.copy()
            perturbed[0, i] = 0.0  # mean in scaled space
            perturbed_proba = self._model.predict_proba(perturbed)[0, base_class]
            contributions[feat_name] = round(float(base_proba - perturbed_proba), 5)

        # Sort by magnitude descending
        contributions = dict(
            sorted(contributions.items(), key=lambda kv: abs(kv[1]), reverse=True)
        )
        return contributions

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(self, assessment: dict[str, Any]) -> dict[str, Any]:
        """
        Predict student risk level from a single assessment dict.

        Parameters
        ----------
        assessment : dict
            Must contain:
                math_score, reading_score, writing_score (0-100),
                attendance_pct (0-100),
                behavior_rating (1-5, int),
                literacy_level (1-10, int),
                home_engagement_composite (0-1),
                score_trend (-1 to 1),
                grade_level (1-12),
                age (int),
                school_type ('public' | 'private' | 'community'),
                gender ('male' | 'female').

        Returns
        -------
        dict with keys:
            risk_level         : str  — 'low' | 'medium' | 'high' | 'critical'
            risk_probability   : float — probability of the predicted class
            all_probabilities  : dict  — {risk_level_name: probability}
            feature_contributions : dict — {feature_name: contribution_value}
                Positive value = feature pushes towards predicted class.
                Negative value = feature pulls away from predicted class.
        """
        self._ensure_loaded()

        # Import here to avoid circular import when serve.py is used standalone
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from features import prepare_prediction_features  # type: ignore[import]

        # 1. Build feature vector
        X_raw = prepare_prediction_features(assessment)  # shape (1, n_features)

        # 2. Scale
        X_scaled = self._scaler.transform(X_raw)  # type: ignore[union-attr]

        # 3. Predict
        predicted_class = int(self._model.predict(X_scaled)[0])  # type: ignore[union-attr]
        all_probas = self._model.predict_proba(X_scaled)[0]  # type: ignore[union-attr]

        risk_level = RISK_LABEL_MAP[predicted_class]
        risk_probability = round(float(all_probas[predicted_class]), 4)
        all_probabilities = {
            RISK_LABEL_MAP[i]: round(float(p), 4) for i, p in enumerate(all_probas)
        }

        # 4. Feature contributions
        feature_contributions = self._compute_feature_contributions(
            X_scaled, base_class=predicted_class
        )

        return {
            "risk_level": risk_level,
            "risk_probability": risk_probability,
            "all_probabilities": all_probabilities,
            "feature_contributions": feature_contributions,
        }

    def predict_batch(self, assessments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Run predict() for a list of assessments.

        Parameters
        ----------
        assessments : list of dict
            Each dict has the same schema as `predict()`.

        Returns
        -------
        list of dicts, one per input assessment, in the same order.
        """
        return [self.predict(a) for a in assessments]

    def health(self) -> dict[str, Any]:
        """Return server health/info payload."""
        try:
            self._ensure_loaded()
            loaded = True
            error = None
        except Exception as exc:  # noqa: BLE001
            loaded = False
            error = str(exc)

        return {
            "status": "ok" if loaded else "error",
            "model_loaded": loaded,
            "model_path": str(self.model_path),
            "scaler_path": str(self.scaler_path),
            "n_features": len(self.feature_names) if loaded else None,
            "error": error,
        }


# ---------------------------------------------------------------------------
# Module-level singleton (optional convenience)
# ---------------------------------------------------------------------------

_default_server: ModelServer | None = None


def get_default_server() -> ModelServer:
    """
    Return a lazily-initialised module-level ModelServer instance.

    Uses default model and scaler paths.  Suitable for import-time
    initialisation without triggering disk I/O.
    """
    global _default_server
    if _default_server is None:
        _default_server = ModelServer(lazy_load=True)
    return _default_server


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample = {
        "math_score": 42.0,
        "reading_score": 38.5,
        "writing_score": 44.0,
        "attendance_pct": 58.0,
        "behavior_rating": 2,
        "literacy_level": 3,
        "home_engagement_composite": 0.28,
        "score_trend": -0.35,
        "grade_level": 5,
        "age": 11,
        "school_type": "public",
        "gender": "male",
    }

    print("EduSight Africa — ModelServer smoke test")
    print("=" * 50)
    server = ModelServer()
    print("Health:", server.health())
    print("\nRunning prediction on sample assessment...")
    result = server.predict(sample)
    print(f"  Risk level      : {result['risk_level']}")
    print(f"  Risk probability: {result['risk_probability']}")
    print(f"  All probs       : {result['all_probabilities']}")
    print("\nTop feature contributions:")
    for feat, contrib in list(result["feature_contributions"].items())[:5]:
        direction = "+" if contrib >= 0 else ""
        print(f"  {feat:35s} {direction}{contrib:.5f}")
