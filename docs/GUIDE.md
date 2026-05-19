# EduSight Africa — Complete Guide

## 1. Starting the Application

**Prerequisites** (must be running first):
```bash
cd /Users/ktinega/Documents/Projects/edusight-africa
docker compose up -d   # starts Postgres + Redis
```

**Backend** (in one terminal):
```bash
cd backend
source venv/bin/activate
DATABASE_URL='postgresql+asyncpg://edusight:edusight@localhost:5432/edusight' \
REDIS_URL='redis://localhost:6379' \
ML_ENABLE_TRAINED_MODEL=true \
ML_MODEL_PATH=../ml/models/xgb_model.pkl \
ML_SCALER_PATH=../ml/models/scaler.pkl \
ML_METADATA_PATH=../ml/models/model_metadata.json \
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend** (in another terminal — after `npm install` finishes):
```bash
cd frontend
npm run dev
```

- Backend API: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs
- Frontend: http://localhost:3000

---

## 2. Dataset Collection

### Current State
The project already has a **10,000-record synthetic dataset** at `ml/data/synthetic/student_dataset.csv` covering 10 African countries.

Each record has these columns:

| Column | Description | Range |
|---|---|---|
| `country` | Kenya, Uganda, Tanzania, Ethiopia, Rwanda, Ghana, Nigeria, Senegal, Morocco, South Africa | — |
| `region` | City/region within country | — |
| `school_type` | public / private / community | — |
| `grade_level` | Grade 1–12 | 1–12 |
| `gender` | male / female | — |
| `age` | Student age | 5–22 |
| `math_score` | Math score | 0–100 |
| `reading_score` | Reading score | 0–100 |
| `writing_score` | Writing score | 0–100 |
| `attendance_pct` | % days attended | 0–100 |
| `behavior_rating` | Teacher behavior rating | 1–5 |
| `literacy_level` | Literacy assessment score | 1–10 |
| `home_engagement_composite` | Homework + books + sleep proxy | 0–1 |
| `score_trend` | Recent score direction | -1 to +1 |
| `risk_label` | **Target**: 0=low, 1=medium, 2=high, 3=critical | 0–3 |

### Generating More Synthetic Data
```bash
cd /Users/ktinega/Documents/Projects/edusight-africa
python ml/data/synthetic/generate_dataset.py --n-students 50000 --output ml/data/synthetic/student_dataset_50k.csv
```

### Collecting Real School Data
For real deployments, collect a CSV with the same columns from schools. The minimum viable fields you need are:
- `math_score`, `reading_score`, `writing_score`
- `attendance_pct`
- `behavior_rating` (teacher-rated 1–5)
- `literacy_level`
- `grade_level`, `age`, `gender`, `school_type`, `country`, `region`

Then attach a `risk_label` using the rule:
- **0 (low)**: attendance > 80%, avg scores > 65
- **1 (medium)**: attendance 60–80%, avg scores 50–65
- **2 (high)**: attendance 40–60%, avg scores 35–50
- **3 (critical)**: attendance < 40% or avg scores < 35

---

## 3. Training the Model

**Setup ML environment:**
```bash
cd /Users/ktinega/Documents/Projects/edusight-africa
pip install -r ml/requirements.txt
```

**Run training:**
```bash
python ml/train_model.py
```

This will:
1. Load `ml/data/synthetic/student_dataset.csv`
2. Engineer 18 features (scores, attendance, engineered ratios, one-hot categoricals)
3. Train XGBoost + RandomForest with 5-fold cross-validation
4. Pick the best model by macro-F1
5. Save artifacts to `ml/models/`:
   - `xgb_model.pkl` — the trained classifier
   - `scaler.pkl` — fitted StandardScaler
   - `model_metadata.json` — metrics, feature list, training config

**Current model performance** (from last training run):

| Metric | Score |
|---|---|
| Model | RandomForest |
| Accuracy | 81.4% |
| AUC-ROC | 0.94 |
| Macro F1 | 0.57 |

> AUC-ROC of 0.94 is excellent for risk ranking. Macro F1 is lower because the "critical" class is rare (~10% of data).

**To retrain on your own data:**
```bash
# Replace the dataset file, then retrain
cp your_school_data.csv ml/data/synthetic/student_dataset.csv
python ml/train_model.py
```

---

## 4. Enabling the Trained Model in the Backend

By default the backend uses rule-based predictions. To switch to the trained ML model, set these env vars when starting the backend:

```bash
ML_ENABLE_TRAINED_MODEL=true
ML_MODEL_PATH=../ml/models/xgb_model.pkl
ML_SCALER_PATH=../ml/models/scaler.pkl
ML_METADATA_PATH=../ml/models/model_metadata.json
```

Or add them to your `.env` file.

---

## 5. Using the Platform (API)

After the backend is running, open http://localhost:8000/docs for interactive API docs.

**Key flows:**

1. **Register a school** → `POST /api/v1/schools`
2. **Create users** (admin, teacher) → `POST /api/v1/auth/register`
3. **Add students** → `POST /api/v1/students`
4. **Submit an assessment** → `POST /api/v1/assessments` with math/reading/writing/attendance scores
5. **Get prediction** → `GET /api/v1/predictions/{student_id}` — returns risk level, risk drivers, and recommended interventions
6. **View dashboard** → `GET /api/v1/reports/school/{school_id}`

**Example prediction response:**
```json
{
  "risk_level": "high",
  "confidence": 0.82,
  "risk_drivers": ["Low attendance (52%)", "Declining score trend"],
  "recommended_actions": ["Assign a peer mentor", "Contact parents this week"],
  "intervention_priority": "urgent"
}
```

---

## 6. Next Steps to Improve Model Quality

| Action | Impact |
|---|---|
| Collect real school data (even 500 records) | Highest — removes synthetic bias |
| Add more features: homework submission rate, teacher notes | Medium |
| Retrain with class weights to fix the "critical" F1 | Medium |
| Add Masakhane NLP for local language teacher notes | High for Africa-context |
| Add model drift monitoring (compare prediction distributions weekly) | Important before scaling |
