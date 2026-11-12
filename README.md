# AgentLens

> Run AI agents on evaluation tasks and diagnose exactly why they fail.

[![CI](https://github.com/KavuriGreeshma2326/agentlens/actions/workflows/ci.yml/badge.svg)](https://github.com/KavuriGreeshma2326/agentlens/actions/workflows/ci.yml)

---

## Architecture

```
agentlens/
├── backend/    FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL
└── frontend/   React + TypeScript + Vite + Tailwind CSS
```

Both services are run together via Docker Compose.

---

## Quick Start (Docker — recommended)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Compose)

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/KavuriGreeshma2326/agentlens.git
cd agentlens

# 2. Create your .env from the example (never commit .env)
cp .env.example .env

# 3. Open .env and set a real JWT_SECRET:
#    python -c "import secrets; print(secrets.token_hex(32))"

# 4. Start everything (Postgres → Backend → Frontend)
docker compose up --build
```

| Service  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:5173      |
| Backend  | http://localhost:8000      |
| API Docs | http://localhost:8000/docs |

---

## Verifying It Works

### 1. Health endpoint
```bash
curl http://localhost:8000/health
# → {"status":"ok","service":"agentlens"}
```

### 2. Register a user
```bash
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"secret"}' | python -m json.tool
# → {"access_token": "eyJ...", "token_type": "bearer"}
```

### 3. Login
```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"secret"}' | python -m json.tool
```

### 4. Get current user (replace TOKEN below)
```bash
curl -s http://localhost:8000/auth/me \
  -H "Authorization: Bearer TOKEN" | python -m json.tool
# → {"id": 1, "email": "you@example.com"}
```

### 5. Swagger UI
Open http://localhost:8000/docs — click **Authorize**, paste your token, and try every endpoint interactively.

### 6. Frontend
Open http://localhost:5173 — you should see a green **Online** badge.

---

## API Endpoints

| Method | Path            | Auth | Description               |
|--------|-----------------|------|---------------------------|
| GET    | /health         | No   | Liveness check            |
| POST   | /auth/register  | No   | Register, returns JWT     |
| POST   | /auth/login     | No   | Login, returns JWT        |
| GET    | /auth/me        | Yes  | Current user profile      |

---

## Running Tests Locally

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

Tests use SQLite in memory — no running Postgres required.

---

## Running Migrations Manually

```bash
# From the backend/ directory
export DATABASE_URL=postgresql://agentlens:yourpassword@localhost:5432/agentlens
alembic upgrade head    # apply all pending migrations
alembic downgrade -1   # roll back one migration
alembic history         # list all migrations
```

---

## Local Development (without Docker)

**Backend**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://...
export JWT_SECRET=...
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
# Optionally create frontend/.env.local with VITE_API_URL=http://localhost:8000
npm run dev
```

---

## Project Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI app + CORS + router registration
│   ├── config.py        # Pydantic settings — reads env vars at startup
│   ├── database.py      # SQLAlchemy engine, session, Base
│   ├── dependencies.py  # get_current_user (JWT → User)
│   ├── models/          # ORM models: User, Task, Run, RunStep
│   ├── schemas/         # Pydantic I/O schemas
│   ├── auth/            # hashing.py (bcrypt), jwt.py (python-jose)
│   └── routers/         # health.py, auth.py
├── alembic/             # Migration environment + versions/
├── tests/               # pytest suite (SQLite, no external deps)
├── alembic.ini
├── pytest.ini
├── requirements.txt
└── Dockerfile

frontend/
├── src/
│   ├── App.tsx          # Health check UI (loading / success / error states)
│   ├── main.tsx
│   └── index.css        # Tailwind directives
├── index.html
├── package.json
├── vite.config.ts
└── Dockerfile
```
