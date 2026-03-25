"""
EduSight Africa — Complete ML Training Pipeline

Trains an XGBoost (primary) and RandomForest (baseline) classifier for
student risk prediction.  Run from the project root:

    python ml/train_model.py

Outputs
-------
ml/models/xgb_model.pkl       — calibrated XGBoost pipeline (best model)
ml/models/scaler.pkl           — fitted StandardScaler
ml/models/model_metadata.json  — metrics, feature names, training config
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ML_DIR = Path(__file__).parent
DATA_PATH = ML_DIR / "data" / "synthetic" / "student_dataset.csv"
MODELS_DIR = ML_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

XGB_MODEL_PATH = MODELS_DIR / "xgb_model.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
METADATA_PATH = MODELS_DIR / "model_metadata.json"

# ---------------------------------------------------------------------------
# Ensure features module is importable regardless of cwd
# ---------------------------------------------------------------------------

sys.path.insert(0, str(ML_DIR))
from features import engineer_features, select_model_columns  # noqa: E402

RISK_LABEL_MAP = {0: "low", 1: "medium", 2: "high", 3: "critical"}
N_CLASSES = 4


# ---------------------------------------------------------------------------
# Data loading / generation
# ---------------------------------------------------------------------------

def load_or_generate_data() -> pd.DataFrame:
    if DATA_PATH.exists():
        print(f"Loading dataset from {DATA_PATH} ...")
        df = pd.read_csv(DATA_PATH)
    else:
        print("Dataset not found — generating synthetic data ...")
        gen_script = ML_DIR / "data" / "synthetic" / "generate_dataset.py"
        if gen_script.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("generate_dataset", gen_script)
            mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            df = mod.generate_dataset(n_students=10_000, random_state=42)
            DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(DATA_PATH, index=False)
            print(f"Saved generated dataset to {DATA_PATH}")
        else:
            raise FileNotFoundError(
                f"Neither dataset ({DATA_PATH}) nor generator ({gen_script}) found."
            )
    return df


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def build_feature_matrix(df: pd.DataFrame):
    """Return X (feature array), y (labels), and feature names."""
    df_eng = engineer_features(df)
    X_df = select_model_columns(df_eng)
    y = df["risk_label"].values
    return X_df.values, y, list(X_df.columns)


# ---------------------------------------------------------------------------
# Model builders
# ---------------------------------------------------------------------------

def build_xgb() -> XGBClassifier:
    return XGBClassifier(
        objective="multi:softprob",
        num_class=N_CLASSES,
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
    )


def build_rf() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> dict:
    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=list(range(N_CLASSES)))

    # AUC-ROC one-vs-rest
    try:
        auc = roc_auc_score(y_true, y_prob, multi_class="ovr", average="macro")
    except ValueError:
        auc = float("nan")

    return {
        "accuracy": round(float(acc), 4),
        "macro_f1": round(float(macro_f1), 4),
        "auc_roc_ovr": round(float(auc), 4),
        "confusion_matrix": cm.tolist(),
    }


def cross_validate_model(estimator, X_train: np.ndarray, y_train: np.ndarray) -> dict:
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(estimator, X_train, y_train, cv=cv, scoring="f1_macro", n_jobs=-1)
    return {
        "cv_macro_f1_mean": round(float(scores.mean()), 4),
        "cv_macro_f1_std": round(float(scores.std()), 4),
        "cv_scores": [round(float(s), 4) for s in scores],
    }


# ---------------------------------------------------------------------------
# Main training pipeline
# ---------------------------------------------------------------------------

def train() -> None:
    start_time = time.time()

    # 1. Load data
    df = load_or_generate_data()
    print(f"Dataset shape: {df.shape}")
    print(f"Risk label distribution:\n{df['risk_label'].value_counts().sort_index()}\n")

    # 2. Build feature matrix
    X, y, feature_names = build_feature_matrix(df)
    print(f"Feature matrix shape: {X.shape}")
    print(f"Features ({len(feature_names)}): {feature_names}\n")

    # 3. Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 4. Stratified train/test split 80/20
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.20, stratify=y, random_state=42
    )
    print(f"Train size: {len(X_train):,}  |  Test size: {len(X_test):,}\n")

    # -----------------------------------------------------------------------
    # 5a. XGBoost — 5-fold CV then calibrate
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("Training XGBoost classifier ...")
    xgb_base = build_xgb()
    xgb_cv_results = cross_validate_model(xgb_base, X_train, y_train)
    print(
        f"  XGB CV macro-F1: {xgb_cv_results['cv_macro_f1_mean']:.4f} "
        f"± {xgb_cv_results['cv_macro_f1_std']:.4f}"
    )

    # Calibrate with isotonic regression
    xgb_calibrated = CalibratedClassifierCV(
        build_xgb(), cv=3, method="isotonic"
    )
    xgb_calibrated.fit(X_train, y_train)

    y_pred_xgb = xgb_calibrated.predict(X_test)
    y_prob_xgb = xgb_calibrated.predict_proba(X_test)
    xgb_metrics = compute_metrics(y_test, y_pred_xgb, y_prob_xgb)
    print(f"  XGB Test  accuracy : {xgb_metrics['accuracy']:.4f}")
    print(f"  XGB Test  macro-F1 : {xgb_metrics['macro_f1']:.4f}")
    print(f"  XGB Test  AUC-ROC  : {xgb_metrics['auc_roc_ovr']:.4f}")

    # -----------------------------------------------------------------------
    # 5b. Random Forest baseline — 5-fold CV
    # -----------------------------------------------------------------------
    print("\nTraining RandomForest baseline ...")
    rf_base = build_rf()
    rf_cv_results = cross_validate_model(rf_base, X_train, y_train)
    print(
        f"  RF  CV macro-F1: {rf_cv_results['cv_macro_f1_mean']:.4f} "
        f"± {rf_cv_results['cv_macro_f1_std']:.4f}"
    )

    rf_calibrated = CalibratedClassifierCV(build_rf(), cv=3, method="isotonic")
    rf_calibrated.fit(X_train, y_train)

    y_pred_rf = rf_calibrated.predict(X_test)
    y_prob_rf = rf_calibrated.predict_proba(X_test)
    rf_metrics = compute_metrics(y_test, y_pred_rf, y_prob_rf)
    print(f"  RF  Test  accuracy : {rf_metrics['accuracy']:.4f}")
    print(f"  RF  Test  macro-F1 : {rf_metrics['macro_f1']:.4f}")
    print(f"  RF  Test  AUC-ROC  : {rf_metrics['auc_roc_ovr']:.4f}")

    # -----------------------------------------------------------------------
    # 6. Select best model (by test macro-F1)
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    if xgb_metrics["macro_f1"] >= rf_metrics["macro_f1"]:
        best_model = xgb_calibrated
        best_name = "XGBoost"
        best_metrics = xgb_metrics
        best_cv = xgb_cv_results
    else:
        best_model = rf_calibrated
        best_name = "RandomForest"
        best_metrics = rf_metrics
        best_cv = rf_cv_results

    print(f"Best model: {best_name} (macro-F1 = {best_metrics['macro_f1']:.4f})")

    # -----------------------------------------------------------------------
    # 7. Persist model + scaler
    # -----------------------------------------------------------------------
    joblib.dump(best_model, XGB_MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"\nModel saved  : {XGB_MODEL_PATH}")
    print(f"Scaler saved : {SCALER_PATH}")

    # -----------------------------------------------------------------------
    # 8. Save metadata
    # -----------------------------------------------------------------------
    elapsed = round(time.time() - start_time, 2)
    metadata = {
        "model_name": best_name,
        "model_path": str(XGB_MODEL_PATH),
        "scaler_path": str(SCALER_PATH),
        "feature_names": feature_names,
        "n_features": len(feature_names),
        "n_classes": N_CLASSES,
        "risk_label_map": RISK_LABEL_MAP,
        "training_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "test_metrics": best_metrics,
        "cv_results": best_cv,
        "xgb_metrics": xgb_metrics,
        "xgb_cv": xgb_cv_results,
        "rf_metrics": rf_metrics,
        "rf_cv": rf_cv_results,
        "training_duration_seconds": elapsed,
        "random_state": 42,
        "sklearn_version": __import__("sklearn").__version__,
        "xgboost_version": __import__("xgboost").__version__,
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved: {METADATA_PATH}")

    # -----------------------------------------------------------------------
    # 9. Training summary
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("TRAINING SUMMARY")
    print("=" * 60)
    print(f"Best model     : {best_name}")
    print(f"Accuracy       : {best_metrics['accuracy']:.4f}")
    print(f"Macro F1       : {best_metrics['macro_f1']:.4f}")
    print(f"AUC-ROC (OvR)  : {best_metrics['auc_roc_ovr']:.4f}")
    print(f"CV F1 (5-fold) : {best_cv['cv_macro_f1_mean']:.4f} ± {best_cv['cv_macro_f1_std']:.4f}")
    print(f"Training time  : {elapsed}s")
    print("\nConfusion matrix (rows=true, cols=pred):")
    cm = best_metrics["confusion_matrix"]
    labels = ["low", "medium", "high", "critical"]
    print(f"{'':>10}", "  ".join(f"{l:>8}" for l in labels))
    for i, row in enumerate(cm):
        print(f"{labels[i]:>10}", "  ".join(f"{v:>8}" for v in row))
    print("=" * 60)
    print("Training complete.")


if __name__ == "__main__":
    train()
