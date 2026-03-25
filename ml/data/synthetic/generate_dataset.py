"""
Generate a realistic synthetic dataset of ~10,000 African student records.

Usage:
    python generate_dataset.py
    python generate_dataset.py --n-students 5000 --output student_dataset.csv
"""

import argparse
import os
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Country / region configuration
# ---------------------------------------------------------------------------

COUNTRY_CONFIG = {
    "Kenya": {
        "weight": 0.16,
        "regions": ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret"],
        "score_mean_shift": 2.0,
    },
    "Uganda": {
        "weight": 0.12,
        "regions": ["Kampala", "Entebbe", "Gulu", "Mbarara", "Jinja"],
        "score_mean_shift": -1.0,
    },
    "Tanzania": {
        "weight": 0.14,
        "regions": ["Dar es Salaam", "Dodoma", "Mwanza", "Arusha", "Zanzibar"],
        "score_mean_shift": 0.5,
    },
    "Ethiopia": {
        "weight": 0.14,
        "regions": ["Addis Ababa", "Dire Dawa", "Bahir Dar", "Hawassa", "Mekelle"],
        "score_mean_shift": -2.0,
    },
    "Rwanda": {
        "weight": 0.08,
        "regions": ["Kigali", "Butare", "Gitarama", "Ruhengeri", "Gisenyi"],
        "score_mean_shift": 3.0,
    },
    "Ghana": {
        "weight": 0.10,
        "regions": ["Accra", "Kumasi", "Tamale", "Sekondi", "Cape Coast"],
        "score_mean_shift": 1.5,
    },
    "Nigeria": {
        "weight": 0.12,
        "regions": ["Lagos", "Abuja", "Kano", "Ibadan", "Port Harcourt"],
        "score_mean_shift": 0.0,
    },
    "Senegal": {
        "weight": 0.06,
        "regions": ["Dakar", "Touba", "Thies", "Saint-Louis", "Kaolack"],
        "score_mean_shift": -0.5,
    },
    "Morocco": {
        "weight": 0.05,
        "regions": ["Casablanca", "Rabat", "Fes", "Marrakech", "Agadir"],
        "score_mean_shift": 4.0,
    },
    "South Africa": {
        "weight": 0.03,
        "regions": ["Johannesburg", "Cape Town", "Durban", "Pretoria", "Port Elizabeth"],
        "score_mean_shift": 5.0,
    },
}

COUNTRIES = list(COUNTRY_CONFIG.keys())
COUNTRY_WEIGHTS = [COUNTRY_CONFIG[c]["weight"] for c in COUNTRIES]

# Normalize weights
total_w = sum(COUNTRY_WEIGHTS)
COUNTRY_WEIGHTS = [w / total_w for w in COUNTRY_WEIGHTS]

# ---------------------------------------------------------------------------
# Grade distribution — peak at grades 4-8
# ---------------------------------------------------------------------------

GRADE_WEIGHTS_RAW = {
    1: 1.0, 2: 1.2, 3: 1.4, 4: 1.8, 5: 2.0,
    6: 2.0, 7: 1.9, 8: 1.7, 9: 1.3, 10: 1.0,
    11: 0.8, 12: 0.6,
}
GRADES = list(GRADE_WEIGHTS_RAW.keys())
_gw = list(GRADE_WEIGHTS_RAW.values())
GRADE_WEIGHTS = [w / sum(_gw) for w in _gw]


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------

def _clamp(arr: np.ndarray, lo: float, hi: float) -> np.ndarray:
    return np.clip(arr, lo, hi)


def generate_dataset(n_students: int = 10_000, random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)

    # --- demographic columns ------------------------------------------------
    countries = rng.choice(COUNTRIES, size=n_students, p=COUNTRY_WEIGHTS)
    regions = np.array([
        rng.choice(COUNTRY_CONFIG[c]["regions"]) for c in countries
    ])
    school_types = rng.choice(
        ["public", "private", "community"],
        size=n_students,
        p=[0.70, 0.20, 0.10],
    )
    grade_levels = rng.choice(GRADES, size=n_students, p=GRADE_WEIGHTS)
    genders = rng.choice(["male", "female"], size=n_students, p=[0.502, 0.498])
    ages = grade_levels + 5 + rng.integers(-1, 3, size=n_students)
    ages = _clamp(ages.astype(float), 5, 22).astype(int)

    # --- country mean shifts ------------------------------------------------
    score_shifts = np.array([COUNTRY_CONFIG[c]["score_mean_shift"] for c in countries])

    # School-type bonus (private slightly better on average)
    school_bonus = np.where(school_types == "private", 3.0,
                   np.where(school_types == "community", -3.0, 0.0))

    # --- correlated academic scores ----------------------------------------
    base_ability = rng.normal(60, 12, size=n_students)  # latent ability
    math_score = _clamp(
        base_ability + score_shifts + school_bonus + rng.normal(0, 8, n_students),
        0, 100,
    )
    reading_score = _clamp(
        base_ability + score_shifts + school_bonus + rng.normal(0, 8, n_students),
        0, 100,
    )
    writing_score = _clamp(
        base_ability + score_shifts + school_bonus + rng.normal(0, 9, n_students),
        0, 100,
    )

    # --- attendance: left-skewed for at-risk --------------------------------
    # Mix of two populations: regular attenders and irregular attenders
    at_risk_mask = rng.random(n_students) < 0.25
    attendance_pct = np.where(
        at_risk_mask,
        _clamp(rng.normal(55, 15, n_students), 0, 100),
        _clamp(rng.normal(82, 10, n_students), 0, 100),
    )

    # --- behavior rating (1-5, correlated with ability) --------------------
    raw_behavior = (base_ability - 60) / 12.0 * 0.8 + rng.normal(3.0, 0.6, n_students)
    behavior_rating = _clamp(np.round(raw_behavior), 1, 5)

    # --- literacy level (1-10) --------------------------------------------
    raw_literacy = (reading_score / 10.0) + rng.normal(0, 0.5, n_students)
    literacy_level = _clamp(np.round(raw_literacy), 1, 10)

    # --- home engagement composite (0-1) ----------------------------------
    # Proxy: homework completion, books at home, adequate sleep
    homework_proxy = _clamp(rng.beta(2.5, 1.5, n_students), 0, 1)
    reading_proxy = _clamp(rng.beta(2.0, 2.5, n_students), 0, 1)
    sleep_proxy = _clamp(rng.beta(3.0, 1.5, n_students), 0, 1)
    home_engagement_composite = (homework_proxy * 0.5 + reading_proxy * 0.3 + sleep_proxy * 0.2)

    # --- score trend: -1 (declining) to +1 (improving) -------------------
    # Loosely correlated with attendance and home engagement
    trend_base = (attendance_pct - 75) / 50.0 + (home_engagement_composite - 0.5)
    score_trend = _clamp(
        trend_base * 0.4 + rng.normal(0, 0.3, n_students), -1.0, 1.0
    )

    # --- risk label: 0=low, 1=medium, 2=high, 3=critical -----------------
    avg_academic = (math_score + reading_score + writing_score) / 3.0
    risk_score = (
        (100 - avg_academic) / 100.0 * 0.35
        + (100 - attendance_pct) / 100.0 * 0.30
        + (5 - behavior_rating) / 4.0 * 0.15
        + (10 - literacy_level) / 9.0 * 0.10
        + (1 - home_engagement_composite) * 0.10
        + rng.normal(0, 0.05, n_students)  # noise
    )
    risk_score = _clamp(risk_score, 0, 1)

    # Thresholds calibrated so roughly: 40% low, 30% medium, 20% high, 10% critical
    risk_label = np.select(
        [risk_score < 0.30, risk_score < 0.52, risk_score < 0.72],
        [0, 1, 2],
        default=3,
    )

    # --- assemble dataframe ------------------------------------------------
    student_ids = [str(uuid.uuid4()) for _ in range(n_students)]

    df = pd.DataFrame({
        "student_id": student_ids,
        "country": countries,
        "region": regions,
        "school_type": school_types,
        "grade_level": grade_levels,
        "gender": genders,
        "age": ages,
        "math_score": np.round(math_score, 2),
        "reading_score": np.round(reading_score, 2),
        "writing_score": np.round(writing_score, 2),
        "attendance_pct": np.round(attendance_pct, 2),
        "behavior_rating": behavior_rating.astype(int),
        "literacy_level": literacy_level.astype(int),
        "home_engagement_composite": np.round(home_engagement_composite, 4),
        "score_trend": np.round(score_trend, 4),
        "risk_label": risk_label.astype(int),
    })

    return df


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic African student dataset")
    parser.add_argument("--n-students", type=int, default=10_000, help="Number of records")
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path(__file__).parent / "student_dataset.csv"),
        help="Output CSV path",
    )
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    print(f"Generating {args.n_students:,} student records...")
    df = generate_dataset(n_students=args.n_students, random_state=args.random_state)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"Dataset saved to: {out_path}")
    print(f"\nShape: {df.shape}")
    print(f"\nRisk label distribution:\n{df['risk_label'].value_counts().sort_index()}")
    print(f"\nCountry distribution:\n{df['country'].value_counts()}")
    print(f"\nSample rows:\n{df.head(3).to_string()}")


if __name__ == "__main__":
    main()
