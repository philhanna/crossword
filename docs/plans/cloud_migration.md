# Cloud Migration Plan

## Goal

Deploy the crossword application to a cloud environment accessible to multiple users,
with persistent storage and proper authentication.

Each phase below produces a **fully working application** — you can stop after any phase
and still have something that runs.

---

## Phase 1 — PostgreSQL Backend (local)

**Result:** Application runs locally, identical to today, but uses PostgreSQL instead of SQLite.

**Why do this first:**
The hexagonal architecture means swapping the storage adapter is self-contained and testable
without touching anything else. This is the foundation every later phase builds on.

**Tasks:**
- Add `psycopg2-binary` (or `psycopg[binary]`) to project dependencies
- Write `PostgresAdapter` implementing the same persistence port as `SQLiteAdapter`
- Write a schema creation script (`tools/dev/init_db.py`) that creates all tables and indexes
- Update config to accept `DATABASE_URL` environment variable (fall back to SQLite if absent,
  so existing local dev still works without Postgres)
- Migrate existing data from `examples/samples.db` to the new Postgres DB
- All existing tests pass

**Deliverable:** `DATABASE_URL=postgres://... python -m crossword.http_server` works fully.

---

## Phase 2 — Authentication (local)

**Result:** Application requires login. Multiple users can have their own puzzles and grids.

**Why do this before deploying:**
Deploying without authentication would expose all data to anyone with the URL. Auth must be
in place before the app goes public.

**Approach:** `httpOnly` cookie sessions stored in PostgreSQL.

- `httpOnly` cookies cannot be read by JavaScript — protected against XSS
- `Secure` + `SameSite=Strict` flags prevent CSRF
- Simpler than JWT for a browser-only web app (no refresh-token complexity)
- Sessions stored in the DB — no extra infrastructure needed

**How login works:**
1. User submits email + password to `POST /api/login`
2. Server verifies password (bcrypt), creates a session row, returns
   `Set-Cookie: session_id=<token>; HttpOnly; Secure; SameSite=Strict`
3. Browser sends the cookie automatically on every subsequent request
4. Middleware in the HTTP server looks up the session and rejects unauthenticated requests
   (except `POST /api/login` and static asset routes)
5. `POST /api/logout` deletes the session row and clears the cookie

**New DB tables:**
```sql
CREATE TABLE users (
    id       SERIAL PRIMARY KEY,
    email    TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL   -- bcrypt hash
);

CREATE TABLE sessions (
    id         TEXT PRIMARY KEY,  -- secrets.token_hex(32)
    user_id    INTEGER NOT NULL REFERENCES users(id),
    expires_at TIMESTAMPTZ NOT NULL
);
```

**Tasks:**
- Add `bcrypt` to project dependencies
- Add `users` and `sessions` tables to the schema script
- Write `POST /api/login` and `POST /api/logout` handlers
- Add session-check middleware to the HTTP request handler
- Add `GET /api/me` endpoint (frontend uses this to check login state on page load)
- Add a login page / login form to the frontend
- Write `tools/dev/create_user.py` for provisioning accounts (no self-signup for now)
- Update `tools/user/export_*.py` to accept a `--user <email>` argument instead of hardcoding `user_id=1`

**Deliverable:** App works locally with login. Each user sees only their own puzzles and grids.

---

## Phase 3 — Cloud Deployment (Fly.io + Neon)

**Result:** Application is live in the cloud, accessible to all users via a URL.

**Hosting:** [Fly.io](https://fly.io) — Dockerfile-based, does not sleep on free tier,
simple `fly.toml` config.

**Database:** [Neon](https://neon.tech) — managed PostgreSQL, generous free tier,
standard connection string.

**Tasks:**
- Write `Dockerfile` for the Python backend (serves frontend static files too)
- Write `fly.toml` (app name, port 5000, region, env var references)
- Provision a Neon database; run the schema creation script against it
- Set Fly.io secrets: `DATABASE_URL`, `SECRET_KEY`
- Create initial user accounts with `create_user.py` pointed at the Neon DB
- Deploy and smoke-test all major flows (login, create grid, create puzzle, export)
- Set up a custom domain (optional)

**Deliverable:** `https://<appname>.fly.dev` is live and fully functional.

---

## Open Questions

- **Session expiry:** How long should sessions last? (Suggestion: 30 days with sliding
  expiry reset on each request.)
- **User registration:** Self-serve signup vs. admin-provisioned accounts? For a small
  known group, provisioning via `create_user.py` is simpler and avoids spam accounts.
- **Multi-tenancy:** One shared DB, rows scoped by `user_id`. Fine for a small number
  of users.
