# Cloud Migration Plan

## Goal

Deploy the crossword application to a cloud environment accessible to multiple users,
with persistent storage and proper authentication.

---

## 1. Cloud Database — PostgreSQL on Neon

**Recommendation:** PostgreSQL hosted on [Neon](https://neon.tech) (free tier available).

**Why:**
- The existing hexagonal architecture makes adapter replacement straightforward
- Neon provides a standard PostgreSQL connection string, zero-config branching,
  and a generous free tier

**Migration tasks:**
- Add `psycopg2-binary` (or `psycopg[binary]`) to project dependencies
- Write a `PostgresAdapter` implementing the same persistence port as `SQLiteAdapter`
- Update config to read `DATABASE_URL` from an environment variable
- Write a schema migration script (create tables, indexes) for the new DB

---

## 2. Container Hosting — Fly.io

**Recommendation:** [Fly.io](https://fly.io)

**Why:**
- Dockerfile-based deployment with a simple `fly.toml` config
- Does not sleep on free tier (unlike Render)
- Supports persistent volumes if needed for temporary files
- Global edge deployment

**Migration tasks:**
- Write a `Dockerfile` for the Python backend
- Write `fly.toml` (app name, port, region, env vars)
- Set secrets on Fly.io: `DATABASE_URL`, `SECRET_KEY`
- Confirm static files (`frontend/`) are served correctly from the container

---

## 3. Authentication — Cookie-Based Sessions

**Recommendation:** `httpOnly` cookie sessions stored in PostgreSQL.

**Why cookie sessions over JWT:**
- This is a browser-only web app — cookies are the right fit
- `httpOnly` cookies cannot be read by JavaScript, protecting against XSS
- `Secure` + `SameSite=Strict` flags prevent CSRF
- Simpler to implement and reason about than JWT refresh-token flows
- JWT is better suited to mobile apps or third-party API consumers

**How it works:**
1. User submits email + password to `POST /api/login`
2. Server verifies password (bcrypt), creates a session row in the DB, returns
   a `Set-Cookie: session_id=<token>; HttpOnly; Secure; SameSite=Strict` header
3. Browser sends the cookie automatically on every subsequent request
4. A middleware layer in the HTTP server looks up the session, rejects requests
   with missing/expired sessions (except `/api/login` and static assets)
5. `POST /api/logout` deletes the session row and clears the cookie

**New DB tables needed:**
```sql
CREATE TABLE users (
    id       SERIAL PRIMARY KEY,
    email    TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL   -- bcrypt hash
);

CREATE TABLE sessions (
    id         TEXT PRIMARY KEY,  -- random token, e.g. secrets.token_hex(32)
    user_id    INTEGER NOT NULL REFERENCES users(id),
    expires_at TIMESTAMPTZ NOT NULL
);
```

**Migration tasks:**
- Add `bcrypt` to project dependencies
- Create `users` and `sessions` tables
- Write a `POST /api/login` handler
- Write a `POST /api/logout` handler
- Add session-check middleware to the HTTP request handler
- Add a `GET /api/me` endpoint (returns current user info; frontend uses to check login state)
- Write a `tools/dev/create_user.py` script for provisioning accounts
- Update `tools/user/export_*.py` CLI scripts (currently hardcode `user_id=1`)

---

## Migration Order

| Step | Task | Depends on |
|------|------|------------|
| 1 | Write `PostgresAdapter` | — |
| 2 | Add `users` + `sessions` tables to schema | Step 1 |
| 3 | Add login/logout endpoints + session middleware | Step 2 |
| 4 | Write `Dockerfile` | — |
| 5 | Write `fly.toml`, set secrets | Steps 1–3 |
| 6 | Deploy and smoke-test | Steps 1–5 |
| 7 | Update CLI export scripts to accept `--user` arg | Step 2 |

---

## Open Questions

- **Single tenant or multi-tenant?** Currently one DB shared by all users (rows scoped
  by `user_id`). This is fine for a small number of known users.
- **User registration:** Self-serve signup vs. admin-provisioned accounts?
  For a small group, provisioning via `create_user.py` is simpler.
- **Session expiry:** How long should sessions last? (Suggestion: 30 days with
  sliding expiry on each request.)
