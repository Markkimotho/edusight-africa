# EduSight Africa

AI-powered student risk assessment and educational analytics platform for African schools.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, Recharts |
| Backend | FastAPI, SQLAlchemy (async), Alembic, asyncpg |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| ML | XGBoost + RandomForest, scikit-learn, Pandas |
| Auth | NextAuth.js (JWT, credentials provider) |
| Infra | Docker Compose, GitHub Actions CI/CD |

---

## Features

- **Risk Assessment** — ML model scores students across attendance, academic, behavioral, and socioeconomic indicators; outputs low / medium / high / critical risk tiers
- **Student Management** — full CRUD with school-level scoping and paginated list views
- **Dashboard** — real-time stats, risk distribution charts, and trend history
- **Parent Portal** — structured observation forms flowing into assessment history
- **Multilingual** — EN, SW, FR, AR, AM, HA, YO, ZU, PT, RW (via next-intl)
- **Cultural Context** — regional weighting profiles for East, West, North, South Africa
- **Role-based Access** — teacher, parent, admin, superadmin

---

## Quick Start

See **[INSTALLATION.md](INSTALLATION.md)** for the full setup guide.

**TL;DR (Docker):**

```bash
git clone <your-repo-url> edusight-africa
cd edusight-africa

cp .env.example .env          # fill in the three secret keys

docker compose up --build     # starts postgres + redis + backend + frontend

# in a second terminal:
docker compose exec backend alembic upgrade head
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |

---

## Project Structure

```
edusight-africa/
├── backend/                   # FastAPI application
│   ├── app/
│   │   ├── api/v1/            # Route handlers
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic + ML inference
│   │   └── core/              # Security, caching, config
│   ├── alembic/               # Database migrations
│   ├── tests/                 # pytest suite (25 tests, SQLite in-memory)
│   └── requirements.txt
│
├── frontend/                  # Next.js 14 application
│   ├── app/
│   │   ├── (auth)/            # Login / register pages
│   │   └── (app)/             # Protected pages — dashboard, students, assess
│   ├── components/            # Charts, layout, shared UI
│   ├── lib/                   # API client, NextAuth config, Zustand stores
│   ├── messages/              # i18n JSON (10 languages)
│   └── package.json
│
├── ml/                        # ML pipeline
│   ├── train_model.py         # XGBoost + RF training script
│   ├── features.py            # Feature engineering
│   ├── serve.py               # ModelServer inference class
│   └── data/synthetic/        # Synthetic African student data generator
│
├── docker-compose.yml
├── Makefile                   # Developer shortcuts
├── .env.example
└── .github/workflows/         # ci.yml (tests + lint) · deploy.yml (build + push)
```

---

## Development

```bash
# Run backend tests
pytest backend/tests/ -v
# or
make test-backend

# Train the ML model
python ml/train_model.py
# outputs ml/models/xgb_model.pkl + ml/models/scaler.pkl

# Common Makefile commands
make up            # start all containers
make down          # stop all containers
make migrate       # run alembic migrations in container
make logs          # stream container logs
make clean         # stop + delete volumes (destructive)
```

---

## Roles

| Role | Access |
|------|--------|
| `teacher` | Assess students, view dashboard, manage students in their school |
| `parent` | Submit observations, view their child's history |
| `admin` | Full school-level access |
| `superadmin` | Platform-wide access |

Register the first account at http://localhost:3000/login or via the API — see [INSTALLATION.md](INSTALLATION.md#first-user).
