# Implementation Plan for Issue #186

## Goal
Add authenticated multi-user support to the crossword application so that:
- all online access requires login
- only administrators can create users and issue replacement access codes
- each authenticated user can access only that user's own data
- passwords and one-time access codes are stored in hashed form

This plan covers the first implementation slice only. Self-service password changes, profile editing, one-time-use enforcement, and user deletion through the application are out of scope.

## Scope Summary
In scope:
- user table and supporting schema updates
- password hashing and verification
- login/logout and session management
- route protection for the existing application
- administrator-only user creation and password reset workflows
- wiring puzzle access to the authenticated user identity
- tests for auth, user creation, login failure, and data isolation

Out of scope:
- self-service password change
- self-service profile updates
- user deletion in the app
- admin web UI for browsing other users' puzzle data
- enforcement that an access code is consumed only once

## Assumptions
- The initial admin account will be created manually using a password-hashing helper provided by the new code.
- `username` and `email` are both required and unique.
- The application has only two roles: `admin` and `user`.
- Administrators may inspect or modify data directly in the database, but not through the online UI.
- Existing puzzle ownership by `userid` remains the basis for isolation.

## Proposed Architecture
### 1. Domain and Ports
Add a user/auth slice parallel to the existing puzzle slice.

New concepts:
- `User` domain model or lightweight record with `id`, `username`, `email`, `role`, timestamps, and profile fields already listed in the issue schema.
- `UserPort` or expanded persistence/auth ports for:
  - create user
  - fetch user by id
  - fetch user by username
  - update stored password hash
  - record last access timestamp
- `SessionStore` abstraction for:
  - create session for user id
  - resolve session token to user id and role
  - delete session
- `PasswordHasher` abstraction for:
  - hash secret
  - verify secret against stored hash

Keep auth concerns separate from `PuzzleUseCases` so puzzle logic remains user-agnostic beyond the existing `user_id` argument.

### 2. Use Cases
Add new use-case modules, likely under `crossword/use_cases/`:
- `AuthUseCases`
  - authenticate(username, password)
  - create_session(user)
  - logout(session_token)
  - get_authenticated_user(session_token)
- `UserUseCases`
  - create_user(admin_user, username, email, initial_code, ...profile_fields)
  - reset_user_code(admin_user, user_id or username, replacement_code)
  - get_user(user_id)

Important implementation detail:
- For this issue, the “one-time access code” is just a hashed password equivalent. The code path should not assume a distinct secret type yet.

### 3. Adapters
Add or extend SQLite-backed adapters.

Likely changes:
- extend `SQLitePersistenceAdapter` or split responsibilities so puzzle persistence and user persistence are both SQLite-backed but logically separated
- add session storage; simplest first version is in-memory session mapping in the server process
- add password hashing adapter using a strong password-hash algorithm

Recommended design choice:
- keep user records in SQLite
- keep sessions in memory for the first slice

That keeps the initial implementation smaller and avoids schema work for sessions. The tradeoff is that server restart invalidates sessions, which is acceptable for the first version unless you want persistence.

## Database Plan
### 1. Users Table
Create or migrate a `users` table based on the issue schema, with these practical additions:
- `username TEXT NOT NULL UNIQUE`
- `email TEXT NOT NULL UNIQUE`
- `password BLOB NOT NULL`
- `role TEXT NOT NULL CHECK (role IN ('admin', 'user'))`

Suggested initial schema:
```sql
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY,
    username        TEXT NOT NULL UNIQUE,
    password        BLOB NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('admin', 'user')),
    created         TEXT,
    last_access     TEXT,
    email           TEXT NOT NULL UNIQUE,
    confirmed       TEXT,
    author_name     TEXT,
    address_line_1  TEXT,
    address_line_2  TEXT,
    address_city    TEXT,
    address_state   TEXT,
    address_zip     TEXT
);
```

### 2. Puzzle Ownership Integrity
The `puzzles.userid` column already exists and is the core isolation mechanism.

Additions to consider:
- foreign key from `puzzles.userid` to `users.id`
- migration or validation for existing rows so puzzle records are assigned to a valid user

Open implementation question for migration:
- if existing databases already contain puzzles without a corresponding `users` row, decide whether to create a default migrated owner or require manual admin preparation before enabling auth

### 3. Migration Strategy
Update `_ensure_schema_compatibility()` in the SQLite adapter to:
- create `users` if missing
- add `role` and uniqueness constraints where possible
- preserve existing `puzzles` table behavior
- optionally validate puzzle owner references

Because SQLite has limited `ALTER TABLE` support, some schema changes may require table rebuild patterns if the repo starts supporting migration of older user tables later.

## HTTP/API Plan
### 1. Login and Logout Endpoints
Add auth endpoints such as:
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

Behavior:
- login validates username and password
- successful login creates session token and sets secure cookie
- logout deletes session and clears cookie
- `me` returns the authenticated user identity needed by the frontend

### 2. User Management Endpoints
For this issue, keep admin functionality minimal and task-focused.

Suggested endpoints:
- `POST /api/users` for admin user creation
- `POST /api/users/{username}/reset-code` for admin-issued replacement code

Do not add broad admin listing/browsing endpoints unless needed for the initial UI.

### 3. Route Protection
Introduce request-level auth gating in the HTTP layer.

Approach:
- allow unauthenticated access only to:
  - `/`
  - static assets required for login screen
  - login/logout/auth endpoints
- require a valid session for puzzle, export, import, and word endpoints
- resolve `user_id` from the session rather than trusting any client-provided identity

This is the most important behavioral change for the issue.

### 4. Request Context
Extend the request handling flow so handlers receive authenticated user context, not just `session_token`.

For example:
- parse session token from cookie
- resolve session to `{user_id, role, username}`
- pass `current_user` into handlers
- handlers reject access with `401` or `403` as appropriate

## Frontend Plan
### 1. Login Screen
There is already a `frontend/login.html`, but it appears disconnected from the current `frontend/static/` layout.

Tasks:
- decide whether to keep a standalone login page or integrate it into the existing frontend structure
- wire the login form to `POST /api/auth/login`
- display authentication errors clearly
- redirect authenticated users to the main app

### 2. Auth Bootstrapping in Main App
Update the frontend startup flow in `frontend/static/js/app.js`:
- check `GET /api/auth/me` on load
- if unauthenticated, redirect to login page
- if authenticated, load the existing app normally
- handle `401` responses globally by redirecting back to login

### 3. Minimal Admin UI
The first slice needs some way for admins to create users and reset codes.

Two viable approaches:
1. Add a very small admin dialog/page in the frontend for `create user` and `reset code`
2. Keep admin creation/reset as a developer/admin-only CLI or script for the first implementation slice

Given the issue wording, the cleaner interpretation is to provide online admin support for user creation and reset. A small admin page or modal is likely enough.

## CLI / Tooling Plan
Add a small helper script under `tools/user/` or `tools/dev/` to support:
- hashing a password/code for manual admin bootstrap
- optionally creating the initial admin account from the command line

This directly supports your stated workflow for initial admin creation.

Example responsibilities:
- `tools/user/hash_password.py` or similar
- optional `tools/user/create_admin.py`

## Testing Plan
### 1. Unit Tests
Add tests for:
- password hashing and verification
- user creation validation
- duplicate username rejection
- duplicate email rejection
- authentication success/failure
- session creation and logout

### 2. Adapter Tests
Add SQLite adapter tests for:
- users table creation
- create/fetch user
- update password hash
- record last access
- uniqueness constraint behavior

### 3. HTTP Integration Tests
Add end-to-end server tests for:
- login succeeds with valid credentials
- login fails with invalid credentials
- unauthenticated request to protected route returns `401`
- authenticated user can access own puzzle list
- authenticated user cannot access another user's puzzle data
- admin can create a user
- non-admin cannot create a user

### 4. Regression Tests
Preserve coverage that existing puzzle behavior still works once an authenticated user is established.

## Recommended Implementation Order
1. Add password hashing adapter and tests.
2. Add users table support in SQLite and adapter tests.
3. Add user/auth use cases.
4. Add in-memory session store.
5. Add login/logout/me endpoints.
6. Add request auth gating and pass authenticated user context into handlers.
7. Update existing puzzle handlers to rely on authenticated user identity.
8. Add minimal admin user-creation and reset-code endpoints.
9. Wire login page and frontend auth bootstrapping.
10. Add admin UI if included in the first slice.
11. Add bootstrap helper for manual admin creation.
12. Run full test suite and update docs.

## Risks and Watch Points
- Existing databases may not yet have valid user rows to match `puzzles.userid`.
- The current router and handlers are simple and may need a clean shared auth helper to avoid repetitive authorization checks.
- The existing `login.html` references assets/layout that may no longer match the current frontend structure.
- In-memory sessions are simple, but all sessions will be lost on restart.
- If the password hashing library introduces a new dependency, packaging and test setup may need updates.

## Suggested Deliverables
- database migration/schema update for users and role support
- auth and user use-case modules
- password hashing utility and bootstrap helper
- session handling in the HTTP server
- login/logout/auth endpoints
- admin-only endpoints for create-user and reset-code
- frontend login flow and minimal admin controls
- automated tests for auth and data isolation
- brief docs for admin bootstrap and daily operation

## Open Design Decisions That Do Not Block Planning
- Whether admin user management is exposed through a small web UI or only through scripts in the first implementation slice
- Whether sessions should eventually move from in-memory storage to SQLite
- Whether `confirmed` should be populated immediately for admin-created users or reserved for a later email-confirmation workflow

## Recommendation
Implement this issue in two internal phases:

Phase 1:
- schema
- password hashing
- manual admin bootstrap helper
- login/logout/session handling
- protect all existing puzzle routes
- prove per-user isolation in tests

Phase 2:
- admin-only create-user/reset-code endpoints
- minimal admin UI if desired
- docs and cleanup

This keeps the security-critical work first and reduces the risk of mixing account administration UI into the core authentication rollout.
