# AgentLens — Design Decisions

This document explains every significant technical choice made on Day 1,
written so you can defend each one in a technical interview.

---

## 1. FastAPI (not Flask, not Django)

**What**: FastAPI is a Python web framework built on Starlette (ASGI) and
Pydantic.

**Why we chose it**:
- **Automatic OpenAPI docs** — `/docs` and `/redoc` are generated from
  type annotations at zero extra cost. During development this replaces
  Postman.
- **Pydantic validation** — request bodies are validated and typed
  automatically; you get a 422 with a clear error message if the client
  sends a bad payload.
- **Performance** — FastAPI is among the fastest Python frameworks
  (comparable to Node/Go in async scenarios) because it's built on
  Starlette, not WSGI.
- **Modern Python** — uses `async/await`, `Annotated`, and type hints
  throughout; this reduces runtime bugs and improves IDE support.

**Why not Flask?** Flask is synchronous by default, lacks built-in validation,
and requires many plugins for what FastAPI provides out of the box.

**Why not Django?** Django is a full-stack framework oriented around
server-rendered HTML. Its ORM and admin are powerful but add unnecessary
complexity for a JSON API; the coupling between models, views, and templates
is a burden in a pure-API project.

---

## 2. SQLAlchemy 2.0 (synchronous, not async)

**What**: SQLAlchemy is the most widely used Python ORM.
Version 2.0 (released 2023) introduced a cleaner `Mapped[T]` column API and
better type inference.

**Why synchronous?**
- Async SQLAlchemy (`asyncpg` + `create_async_engine`) adds significant
  boilerplate: every function becomes `async def`, every `db.execute()` needs
  `await`, and testing requires `AsyncClient` instead of `TestClient`.
- On Day 1 with a single backend process and modest load, synchronous I/O is
  not a bottleneck. We can migrate to async when profiling shows it's
  necessary.
- The FastAPI docs themselves recommend sync SQLAlchemy as the entry point.

**Why SQLAlchemy over raw SQL or another ORM?**
- Pairs directly with Alembic for migrations (same metadata object).
- Industry-standard; almost every Python backend developer knows it.
- The unit-of-work session pattern (`db.add()`, `db.commit()`,
  `db.refresh()`) makes transactions explicit and safe.

---

## 3. Alembic (database migrations)

**What**: Alembic is the official migration tool for SQLAlchemy, maintained by
the same author (Mike Bayer).

**Why**:
- **Versioned migrations** — every schema change is a numbered Python file
  committed to git. You know exactly what state any environment's database is in.
- **Reversible** — every migration has an `upgrade()` and a `downgrade()`,
  so you can roll back a bad deployment.
- **Autogenerate** — Alembic can diff `Base.metadata` against the live schema
  and produce migration files automatically (useful from Day 2 onwards).
- **Alternative (manual SQL)**: fine for prototypes but becomes unmanageable
  as the team grows; there's no audit trail and no easy rollback.

**Key design decision**: `alembic upgrade head` runs in the Docker `CMD`
*before* Uvicorn starts, so the schema is always current when the API
accepts requests.

---

## 4. PostgreSQL

**Why**:
- **ACID compliance** — transactions are atomic; partial writes don't corrupt
  data.
- **Battle-tested** — runs at scale at every major tech company.
- **Rich feature set** — JSONB, full-text search, row-level security (all
  useful for later days).
- **Free & open-source** — no licensing cost.
- **Alternative (SQLite)**: fine for local testing (we use it in the test
  suite) but not suitable for production: no concurrent writes, no network
  access, limited data types.
- **Alternative (MySQL)**: also solid, but Postgres has better standards
  compliance and a richer type system (e.g. `JSONB`).

---

## 5. Pydantic Settings

**What**: `pydantic-settings` reads configuration from environment variables
(and optionally a `.env` file) and validates them against a typed Python class.

**Why**:
- **Fail-fast** — if `DATABASE_URL` is missing or malformed, the process
  raises a clear `ValidationError` at startup, not a confusing
  `AttributeError` somewhere in the middle of a request.
- **Type safety** — `jwt_expire_minutes: int` means Pydantic coerces the
  string env var to an integer and raises if it isn't parseable.
- **12-Factor App** — this pattern is recommended by the
  [12-Factor App methodology](https://12factor.net/config): store config in
  the environment, never in code.
- **Alternative (`os.getenv`)**: works but scatters `os.getenv("X", default)`
  calls across the codebase with no central validation.

---

## 6. JWT Authentication

**What**: JSON Web Tokens (RFC 7519). We use the `python-jose` library with
the HS256 algorithm (HMAC-SHA256).

**Why JWT (not sessions)?**
- **Stateless** — the server doesn't need to store session data in a database
  or cache. Any backend instance can verify a token using just the secret key.
  This simplifies horizontal scaling.
- **Standard** — JWT is widely understood; every frontend library knows how
  to attach a Bearer token to a request.

**Why HS256 (not RS256)?**
- HS256 uses a single shared secret — simpler for Day 1.
- RS256 uses a public/private key pair and is better when multiple services
  need to *verify* tokens without sharing a secret. We'll switch when we add
  more services.

**Security decisions**:
- Tokens expire after 60 minutes (configurable via `JWT_EXPIRE_MINUTES`).
- The login endpoint returns the same `"Invalid credentials"` message for
  both wrong email and wrong password, preventing **user enumeration** (an
  attacker can't tell whether the email exists).

---

## 7. bcrypt Password Hashing (passlib)

**What**: bcrypt is an adaptive hashing algorithm. `passlib` wraps it in a
safe, high-level API.

**Why bcrypt?**
- **Intentionally slow** — bcrypt has a configurable work factor. This makes
  brute-force attacks expensive even if an attacker steals the hash database.
  MD5 or SHA-256 are orders of magnitude faster and unsuitable for passwords.
- **Adaptive** — you can increase the work factor over time as hardware
  improves, without breaking existing hashes.
- **Industry standard** — OWASP recommends bcrypt (along with Argon2 and
  scrypt) for password storage.

---

## 8. Monorepo Layout

**What**: Backend and frontend live in the same git repository under `/backend`
and `/frontend`.

**Why**:
- **Atomic changes** — an API change and the matching frontend update can be
  in a single pull request and a single commit.
- **Single source of truth** — one place to find all issues, PRs, and history.
- **Simpler CI** — one workflow file runs all checks.
- **Trade-offs**: as the project scales, monorepos require tooling like
  `nx` or `Turborepo` to avoid rebuilding everything on every change. For
  Day 1 this overhead isn't justified.

---

## 9. Docker Compose

**What**: A YAML file that declaratively describes how to build and run all
three services (Postgres, backend, frontend) together.

**Why**:
- **One-command setup** — `docker compose up --build` is all any developer
  needs; no manual Postgres installation, no "works on my machine".
- **Healthcheck on Postgres** — the backend service has
  `condition: service_healthy`, which means Docker waits until `pg_isready`
  succeeds before starting the backend. This prevents `connection refused`
  errors on a cold start.
- **Environment variable injection** — secrets never appear in the
  `Dockerfile` or image layers; they're passed in at runtime.

---

## 10. SQLite in Tests (not Postgres)

**Why use SQLite for tests?**
- **No external dependency** — the test suite runs with just `pip install`;
  no Docker or Postgres process needed. This keeps CI fast and simple.
- **In-process** — SQLite is a file-based database that the same process
  can create and destroy between tests.
- **Compatible** — SQLAlchemy abstracts the dialect; most ORM-level code
  runs identically on SQLite and Postgres.

**Risk**: SQLite has quirks (e.g. less strict typing, no `now()` function in
the same way). The first Alembic migration uses `sa.text("now()")` which is
Postgres-specific, but Alembic migrations aren't run in the test suite
(we call `Base.metadata.create_all()` directly instead).

---

## 11. React + TypeScript + Vite

**React**: The most widely used UI library; large ecosystem, familiar to most
frontend developers.

**TypeScript**: Catches type errors at compile time. When we refactor or
add new API fields, TypeScript tells us immediately which call sites need
updating.

**Vite**: Significantly faster than Webpack or Create-React-App in development
because it uses native ES modules in the browser (no bundling during dev) and
esbuild for transforms. Cold-start time is under 1 second.

---

## 12. Tailwind CSS

**What**: A utility-first CSS framework — instead of writing `.card { ... }`,
you compose utilities directly in the JSX: `className="rounded-2xl bg-gray-900 p-6"`.

**Why**:
- **No naming things** — naming CSS classes is surprisingly hard.
  Utility classes eliminate that cognitive overhead.
- **No CSS growth** — the bundle only contains classes that are actually
  used (PurgeCSS / content scanning is built in).
- **Consistency** — the design token system (spacing, colours, type scale)
  is predefined and consistent across the app.
- **Alternative (plain CSS)**: fine for small projects; becomes hard to
  maintain as the team and component count grow.
- **Alternative (CSS Modules)**: good scoping story, but still requires
  naming things and writing separate files.

---

## 13. GitHub Actions CI

**Why GitHub Actions over alternatives (CircleCI, Jenkins, etc.)?**
- **Native integration** — no third-party OAuth; runs in the same platform
  as the repo.
- **Free for public repos** — no cost for open-source or small teams.
- **YAML in the repo** — the workflow lives next to the code, so it's
  versioned, reviewable, and easy to change.

**Two parallel jobs**:
1. `backend-tests` — installs Python 3.12, runs `pytest`. No Postgres needed
   because tests use SQLite.
2. `frontend-build` — installs Node 20, runs `npm ci && npm run build`.
   Verifies that TypeScript compiles and Vite can produce a production bundle.
---

## 14. Task ownership (Day 2)

**Rule:** a user can only see and change their own tasks.

**Why 404, not 403:** another user's task returns the same 404 as a task that does not exist. A 403 would confirm that the id exists, which leaks information.

**Why a task with runs cannot be deleted:** runs hold the recorded step traces, which are the whole point of the product. Deleting the task would either fail on the database foreign key or destroy that history, so the API returns 409 instead.

**Why PUT replaces the whole task:** it avoids the ambiguity of partial updates (does "null" mean "clear this field" or "leave it alone?").

---

## 15. Mock agent and background runs (Day 2)

**Why a mock agent:** real LLM calls cost money, are slow, and give different answers each time. The product is the evaluation and diagnosis layer, so the mock agent produces traces with known failure patterns. The runner is the only place that changes when a real model is added later.

**Why the trace is seeded:** the same task and agent version always give the same trace. That keeps tests stable and makes comparing agent versions fair.

**Why the failure type is not stored:** the Day 4 diagnosis must work out the cause from the steps alone. Storing the label would make the diagnosis fake.

**Why BackgroundTasks, not a job queue:** the mock agent finishes in milliseconds, so a queue (Redis, a worker) would add moving parts for no benefit. The limit: if the server restarts in the middle of a run, that run stays "running". A real agent would need a proper queue.

**Why the runner opens its own database session:** the request's session is closed once the response is sent, so background work cannot reuse it.

**Why 202 Accepted:** the run is created and queued, but not finished when the response is sent. The client reads the result with GET /runs/{id}.

**Known limitation:** if the runner itself crashes, the run is marked "failed" and the error is logged. That mixes up a system crash with an agent failure. A later version should add a separate "error" status.

---

## 16. Frontend sign-in (Day 3)

**Where the token lives:** `localStorage`. It is simple, and it survives a page reload. The trade-off is that any script running on the page can read it, so a cross-site scripting (XSS) bug would leak the token. The safer alternative is an httpOnly cookie, which JavaScript cannot read, but that needs backend changes and protection against CSRF. React escapes text by default and this app never injects raw HTML, which reduces the XSS risk. Tokens also expire, so a stolen one stops working after a limited time (check the exact lifetime in the backend config before quoting a number).

**Why the saved token is checked on load:** the app calls `/auth/me` before showing the signed-in screen. An expired token is cleared and the user lands on the sign-in form instead of seeing a broken page. A network error does not clear the token, so a refresh can recover.

**Why no router and no chart library:** the app has only a few screens, and every new dependency changes `package-lock.json` and can break the CI install. Navigation uses plain state, and charts are drawn with CSS.

**Known gap:** the 8-character minimum password is enforced only in the browser. Anyone calling the API directly can still register a shorter one. The backend should enforce it too.