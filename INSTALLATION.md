# EduSight Africa — Installation Guide

> Complete setup guide for the Next.js + FastAPI + PostgreSQL stack.

---

## Prerequisites

Install these before starting:

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://python.org) or `pyenv install 3.11` |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) or `nvm install 20` |
| Docker Desktop | Latest | [docker.com/get-started](https://www.docker.com/get-started) |
| Git | Any | `brew install git` / system package manager |

Verify:
```bash
python3 --version    # Python 3.11.x
node --version       # v18.x or v20.x
docker --version     # Docker 24+
docker compose version
```

---

## Quick Start (Docker — recommended)

The fastest way to run everything.

```bash
# 1. Clone the repo
git clone <your-repo-url> edusight-africa
cd edusight-africa

# 2. Create environment file
cp .env.example .env
# Edit .env — at minimum change the three secret keys (see below)

# 3. Build and start all services
docker compose up --build

# 4. In a separate terminal, run database migrations
docker compose exec backend alembic upgrade head
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs (Swagger)**: http://localhost:8001/docs

---

## Manual Setup (no Docker)

Use this if you want to run services directly on your machine for development.

### Step 1 — Start PostgreSQL and Redis

The easiest way is still Docker for just the databases:

```bash
docker compose up postgres redis -d
```

Or install locally:
- **macOS**: `brew install postgresql@15 redis` then `brew services start postgresql@15 redis`
- **Ubuntu**: `sudo apt install postgresql redis-server`

Then create the database:
```bash
# macOS/Linux (replace <your-system-user> with your username)
psql -U <your-system-user> -d postgres -c "CREATE USER edusight WITH PASSWORD 'edusight' CREATEDB;"
psql -U <your-system-user> -d postgres -c "CREATE DATABASE edusight OWNER edusight;"
```

### Step 2 — Backend (FastAPI)

```bash
# From the project root
cd backend

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (or create a .env in backend/)
export DATABASE_URL="postgresql+asyncpg://edusight:edusight@localhost:5432/edusight"
export REDIS_URL="redis://localhost:6379"
export SECRET_KEY="your-secret-key-min-32-chars-change-me"
export REFRESH_SECRET_KEY="your-refresh-key-min-32-chars-change-me"
export ALGORITHM="HS256"
export ENVIRONMENT="development"

# Run database migrations
alembic upgrade head

# Start the backend
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

The API is now at **http://localhost:8001**. Visit **http://localhost:8001/docs** for interactive Swagger docs.

### Step 3 — Frontend (Next.js)

Open a new terminal:

```bash
# From the project root
cd frontend

# Install dependencies
npm install

# Create local env file
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret-min-32-chars-change-me
EOF

# Start the dev server
npm run dev
```

The app is now at **http://localhost:3000**.

---

## Environment Variables Reference

Copy `.env.example` to `.env` and fill in the values below.

### Backend

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg driver) | `postgresql+asyncpg://edusight:edusight@localhost:5432/edusight` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `SECRET_KEY` | JWT signing secret — **min 32 chars, keep private** | `openssl rand -hex 32` |
| `REFRESH_SECRET_KEY` | JWT refresh token secret — **min 32 chars, keep private** | `openssl rand -hex 32` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `ENVIRONMENT` | Runtime mode | `development` or `production` |

### Frontend

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend base URL (visible in browser) | `http://localhost:8001` |
| `NEXTAUTH_URL` | Full URL of the frontend app | `http://localhost:3000` |
| `NEXTAUTH_SECRET` | NextAuth.js signing secret — **keep private** | `openssl rand -hex 32` |

> **Generate secure secrets:**
> ```bash
> openssl rand -hex 32
> ```

---

## First User

After the backend is running, register your first account via the API or the UI:

**Via UI**: go to http://localhost:3000/login → use any email/password you choose (first registration creates the account).

**Via API**:
```bash
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourschool.edu",
    "password": "SecurePassword123!",
    "full_name": "School Admin",
    "role": "admin"
  }'
```

Valid roles: `teacher`, `parent`, `admin`, `superadmin`

---

## ML Model (optional)

The backend uses a rule-based fallback by default. To train and use the full XGBoost model:

```bash
# Install ML dependencies
pip install -r ml/requirements.txt

# Generate synthetic training data and train the model
python ml/train_model.py
```

This creates `ml/models/xgb_model.pkl` and `ml/models/scaler.pkl`. The backend will pick these up automatically on next restart.

---

## Makefile Commands

From the project root (requires Docker):

```bash
make up            # Start all containers (postgres, redis, backend, frontend)
make down          # Stop all containers
make build         # Rebuild Docker images
make logs          # Stream logs from all containers
make migrate       # Run Alembic migrations inside the backend container
make test-backend  # Run pytest suite inside the backend container
make backend-shell # Open a shell in the backend container
make clean         # Stop containers and delete all data volumes (destructive)
```

---

## Project Structure

```
edusight-africa/
├── backend/               # FastAPI app
│   ├── app/
│   │   ├── api/v1/        # Route handlers (auth, students, assessments, ...)
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── services/      # Business logic
│   │   └── core/          # Security, caching
│   ├── alembic/           # Database migrations
│   ├── tests/             # pytest test suite
│   └── requirements.txt
│
├── frontend/              # Next.js 14 app
│   ├── app/               # App Router pages
│   │   ├── (auth)/        # Login / register
│   │   └── (app)/         # Protected pages (dashboard, students, assess, ...)
│   ├── components/        # UI components (charts, layout, shared)
│   ├── lib/               # API client, auth config, Zustand stores
│   └── package.json
│
├── ml/                    # ML training pipeline
│   ├── train_model.py     # XGBoost + RandomForest training script
│   ├── features.py        # Feature engineering
│   ├── serve.py           # ModelServer inference class
│   └── data/synthetic/    # Synthetic data generator
│
├── docker-compose.yml     # Full stack (postgres + redis + backend + frontend)
├── Makefile               # Developer shortcuts
├── .env.example           # Environment variable template
└── .github/workflows/     # CI (tests + lint) and CD (Docker build + push)
```

---

## Running Tests

```bash
# Backend tests (from project root, using the venv)
cd backend
source .venv/bin/activate
pytest tests/ -v

# Or via Docker
make test-backend
```

All 25 tests run against an in-memory SQLite database — no Postgres required for testing.

---

## Troubleshooting

**`role "edusight" does not exist`**
A local Postgres instance is intercepting the connection before Docker's. Create the role in your local Postgres:
```bash
psql postgres -c "CREATE USER edusight WITH PASSWORD 'edusight' CREATEDB;"
psql postgres -c "CREATE DATABASE edusight OWNER edusight;"
```

**Port 8000 already in use**
Another service is on port 8000. Run the backend on a different port:
```bash
uvicorn app.main:app --port 8001 --reload
# and update NEXT_PUBLIC_API_URL=http://localhost:8001 in frontend/.env.local
```

**Frontend login redirects back immediately**
Make sure `NEXTAUTH_SECRET` is set in `frontend/.env.local` and `NEXT_PUBLIC_API_URL` points to the running backend.

**`greenlet` or `aiosqlite` not found**
```bash
pip install greenlet aiosqlite
```

**npm install peer dependency errors**
```bash
npm install --legacy-peer-deps
```
