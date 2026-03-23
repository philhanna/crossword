# Multi-User Authentication Plan

## Overview

The application currently hardcodes `user_id = 1` in every HTTP handler. The database
schema and persistence layer are already multi-user–aware (all queries filter by `userid`).
Adding full authentication requires changes at every layer, but the backend domain/persistence
work is largely mechanical.

### Requirements

| # | Requirement |
|---|---|
| 1 | Application always requires login before use |
| 2 | New users can register — but must be approved by an administrator |
| 3 | Approved users receive a temporary password by email |
| 4 | Login screen authenticates users |
| 5 | Forgot password sends a reset link/token by email |
| 6 | Users can delete their own account |
| 7 | Users can change their password |

---

## Current State

| Layer | Multi-User Ready? | Notes |
|---|---|---|
| Database schema | Yes | `users`, `grids`, `puzzles` have `userid`; all queries use `WHERE userid = ?` |
| Persistence adapter | Yes | `SQLiteAdapter` accepts `user_id` in every method |
| Use cases | Yes | All use-case methods accept `user_id` as parameter |
| HTTP handlers | No | Every handler hardcodes `user_id = 1` |
| HTTP server | Partial | `session_token` is parsed from Cookie header but ignored by handlers |
| Frontend | No | No login UI, no user tracking, no auth headers |

The `users` table schema already exists and covers what we need:

```sql
CREATE TABLE users (
    id              INTEGER PRIMARY KEY,
    username        TEXT UNIQUE NOT NULL,
    password        BLOB,        -- bcrypt hash; NULL until account is activated
    created         TEXT,
    last_access     TEXT,
    email           TEXT UNIQUE NOT NULL,
    -- existing columns retained; new columns added by migration:
    is_admin        INTEGER NOT NULL DEFAULT 0,   -- 1 = administrator
    status          TEXT NOT NULL DEFAULT 'pending',
                                 -- 'pending' | 'active' | 'disabled'
    temp_token      TEXT,        -- reset/activation token (SHA-256 hex)
    temp_token_expires TEXT      -- ISO-8601 UTC expiry
);
```

---

## User Lifecycle

```
   [Visitor]
       │
       ▼
   Submits registration form (username, email)
       │
       ▼
   Account created with status='pending', no password
       │
       ▼
   Admin sees pending users in Admin panel
       │
       ├─ Approve ──► status='active'; temp password generated;
       │               email sent to user with temp password
       │
       └─ Reject  ──► account deleted (or status='disabled')
       │
       ▼ (user receives email)
   User logs in with username + temp password
       │
       ▼
   Forced password-change dialog (because temp_token is set)
       │
       ▼
   Normal app access
```

---

## Screens / Dialogs

All dialogs reuse W3.CSS classes consistent with the existing UI.

### 1. Login dialog (`#lgn`)

Shown on page load when no valid session exists. The main app container starts
`display:none` and is revealed only after a successful login.

```
┌──────────────────────────────┐
│           Login              │  ← blue-gray header
├──────────────────────────────┤
│ Username: [________________] │
│ Password: [________________] │
│                              │
│      [ Login ]               │
│                              │
│  Don't have an account?      │
│  Register                    │
│                              │
│  Forgot password?            │
│                              │
│  (error message if any)      │
└──────────────────────────────┘
```

- Autofocus on Username
- "Register" link → shows Registration dialog
- "Forgot password?" link → shows Forgot Password dialog

### 2. Registration dialog (`#reg`)

Collects enough info to create a pending account. Separate page or overlay.

```
┌──────────────────────────────┐
│         Register             │
├──────────────────────────────┤
│ Username: [________________] │
│ Email:    [________________] │
│                              │
│      [ Register ]            │
│                              │
│  Already have an account?    │
│  Login                       │
│                              │
│  (error / success message)   │
└──────────────────────────────┘
```

On submit: account is created with `status='pending'`. A success message is shown:
*"Your request has been submitted. You will receive an email when your account is approved."*

### 3. Forgot Password dialog (`#fgt`)

```
┌──────────────────────────────┐
│       Forgot Password        │
├──────────────────────────────┤
│ Email: [__________________]  │
│                              │
│      [ Send Reset Link ]     │
│                              │
│  (confirmation / error)      │
└──────────────────────────────┘
```

Regardless of whether the email exists, the response is always:
*"If that email is registered, a reset link has been sent."*
(prevents account enumeration)

### 4. Force Change Password dialog (`#fcp`)

Shown immediately after login when the user has a temporary password (i.e., `temp_token`
is set on their account). The user cannot access the main app until they set a real password.

```
┌──────────────────────────────┐
│     Set New Password         │
├──────────────────────────────┤
│ New password:    [_________] │
│ Confirm password:[_________] │
│                              │
│      [ Set Password ]        │
│                              │
│  (error if mismatch)         │
└──────────────────────────────┘
```

### 5. Account menu (in-app)

A small dropdown in the menu bar (top-right) with the logged-in username:

```
  [alice ▾]
    ├ Change Password
    ├ Delete Account
    └ Logout
```

### 6. Change Password dialog (`#chpw`)

```
┌──────────────────────────────┐
│       Change Password        │
├──────────────────────────────┤
│ Current password: [________] │
│ New password:     [________] │
│ Confirm new:      [________] │
│                              │
│      [ Change Password ]     │
└──────────────────────────────┘
```

### 7. Delete Account dialog (`#delacct`)

```
┌──────────────────────────────┐
│       Delete Account         │
├──────────────────────────────┤
│  This will permanently       │
│  delete all your grids and   │
│  puzzles.                    │
│                              │
│  Type your username to       │
│  confirm:                    │
│  [____________________]      │
│                              │
│      [ Delete Account ]      │
└──────────────────────────────┘
```

Requires typing the username as confirmation. On success: session cleared, redirect to
login dialog.

### 8. Admin panel (`/admin`)

Separate page (not the SPA). Shows a table of users with their status. Admin actions:

| User | Email | Status | Actions |
|---|---|---|---|
| alice | alice@example.com | active | Disable / Delete |
| bob | bob@example.com | pending | Approve / Reject |

- **Approve**: generates temp password → emails user → sets `status='active'`
- **Reject / Delete**: removes account and all associated grids/puzzles
- **Disable**: sets `status='disabled'` (blocks login without deleting data)

Admin page is a simple server-rendered HTML page (not the SPA) served at `/admin`.
Only accessible to users with `is_admin=1`; any other user gets a 403.

---

## Email

All outbound email is sent via SMTP. Configuration is added to `~/.crossword.ini`:

```ini
[email]
smtp_host     = smtp.example.com
smtp_port     = 587
smtp_user     = noreply@example.com
smtp_password = secret
from_address  = Crossword Composer <noreply@example.com>
app_base_url  = http://localhost:5000
```

A new `EmailAdapter` in `crossword/adapters/email_adapter.py` wraps `smtplib` and
provides three methods:

- `send_temp_password(to_email, username, temp_password)` — account approved
- `send_password_reset(to_email, username, reset_token)` — forgot password
- `send_welcome(to_email, username)` — after first real password is set (optional)

Email sending is synchronous (blocking). For this application's scale, a background thread
is not necessary.

**Temp password format:** 12-character random alphanumeric string (human-readable,
not a token). The bcrypt hash of this string is stored immediately; the plaintext is
emailed once and never stored.

**Reset token format:** `secrets.token_urlsafe(32)` — stored as SHA-256 hash in
`temp_token`; expires in 24 hours. The reset link in the email is:
`{app_base_url}/reset-password?token=<raw_token>`

The `/reset-password` route verifies the token and, if valid, shows the Force Change
Password dialog with the token pre-filled in a hidden field.

---

## Database Changes

### New columns on `users` (via migration)

```sql
ALTER TABLE users ADD COLUMN is_admin     INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN status       TEXT NOT NULL DEFAULT 'active';
ALTER TABLE users ADD COLUMN temp_token   TEXT;
ALTER TABLE users ADD COLUMN temp_token_expires TEXT;
```

Existing user (id=1) gets `is_admin=1, status='active'` so the app remains usable
immediately after migration.

### New `sessions` table

```sql
CREATE TABLE sessions (
    token    TEXT PRIMARY KEY,
    userid   INTEGER NOT NULL,
    created  TEXT NOT NULL,
    expires  TEXT NOT NULL
);
```

Sessions expire after a configurable period (default: 7 days). Expiry is checked on
every authenticated request; expired rows are deleted lazily.

---

## Backend Endpoints

### Unprotected (no session required)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/login` | Verify credentials; set session cookie |
| `POST` | `/api/register` | Create pending account |
| `POST` | `/api/forgot-password` | Send reset email |
| `GET`  | `/api/reset-password` | Validate reset token |
| `POST` | `/api/reset-password` | Set new password via token |
| `GET`  | `/api/me` | Return current user or 401 (used on page load) |
| `GET`  | `/reset-password` | Serve reset-password page |
| `GET`  | `/` | Serve main SPA |
| `GET`  | `/static/*` | Static files |

### Protected (session required)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/logout` | Delete session; clear cookie |
| `POST` | `/api/change-password` | Change password (requires current password) |
| `DELETE` | `/api/account` | Delete account + all data |
| All existing | `/api/grids/*`, `/api/puzzles/*`, etc. | Existing handlers, now using session user_id |

### Admin only (`is_admin=1` required)

| Method | Path | Description |
|---|---|---|
| `GET` | `/admin` | Admin panel page |
| `GET` | `/api/admin/users` | List all users and statuses |
| `POST` | `/api/admin/users/{id}/approve` | Approve pending user; send temp password |
| `POST` | `/api/admin/users/{id}/disable` | Disable active user |
| `DELETE` | `/api/admin/users/{id}` | Delete user and all their data |

### Key request/response shapes

**`POST /api/login`**
```json
// request
{ "username": "alice", "password": "s3cr3t" }

// 200 success — normal account
{ "user_id": 42, "username": "alice", "must_change_password": false }

// 200 success — temp password still set
{ "user_id": 42, "username": "alice", "must_change_password": true }

// 401 failure
{ "error": "Invalid username or password" }

// 403 — account pending or disabled
{ "error": "Account is pending approval" }
```

**`POST /api/register`**
```json
// request
{ "username": "bob", "email": "bob@example.com" }

// 200
{ "message": "Registration submitted. You will receive an email when approved." }

// 409 conflict
{ "error": "Username already taken" }
```

**`POST /api/change-password`**
```json
// request
{ "current_password": "old", "new_password": "new123" }

// 200
{ "message": "Password changed successfully" }

// 401
{ "error": "Current password is incorrect" }
```

**`DELETE /api/account`**
```json
// request
{ "username_confirm": "alice" }

// 200
{ "message": "Account deleted" }

// 400
{ "error": "Username does not match" }
```

---

## Auth Middleware

In `server.py`, after parsing the session token from the Cookie header:

1. If route is in the **unprotected** list → pass through with `user_id=None`
2. Call `resolve_session(token)` → returns `(user_id, is_admin)` or `None`
3. If `None` → respond HTTP 401
4. If route requires admin and `is_admin=0` → respond HTTP 403
5. Otherwise → call handler with `user_id` and `is_admin` in kwargs

---

## Replacing `user_id = 1` in Handlers

Every handler changes from:

```python
user_id = 1
```

to:

```python
user_id = kwargs["user_id"]
```

This is a mechanical change across `grid_handlers.py`, `puzzle_handlers.py`, and
`export_handlers.py` (~40 occurrences total).

---

## Persistence Changes

New methods added to `PersistencePort` (abstract) and `SQLiteAdapter` (concrete):

**User management:**
- `get_user_by_username(username) -> dict | None`
- `get_user_by_email(email) -> dict | None`
- `get_user_by_id(user_id) -> dict | None`
- `create_user(username, email) -> int` — status='pending', no password
- `set_password(user_id, password_hash)` — clears temp_token
- `set_temp_token(user_id, token_hash, expires)`
- `get_user_by_temp_token(token_hash) -> dict | None`
- `set_user_status(user_id, status)` — 'active' | 'disabled'
- `delete_user(user_id)` — cascades to grids, puzzles, sessions

**Session management:**
- `create_session(token, user_id, expires)`
- `resolve_session(token) -> dict | None` — returns `{user_id, is_admin}` or None
- `delete_session(token)`
- `delete_user_sessions(user_id)` — used on logout-all / account delete

**Admin:**
- `list_users() -> list[dict]` — all users with status info

---

## Frontend Changes

### `index.html`

- Add `#lgn` (login), `#reg` (register), `#fgt` (forgot password), `#fcp` (force change
  password), `#chpw` (change password), `#delacct` (delete account) dialogs
- Main app container starts `display:none`
- Add account dropdown in menu bar (username + Logout / Change Password / Delete Account)

### `app.js`

**Add to `AppState`:**
```javascript
currentUser: null,   // { user_id, username, is_admin } after login
```

**Page load:**
```javascript
window.addEventListener('DOMContentLoaded', async () => {
    const resp = await fetch('/api/me');
    if (resp.ok) {
        AppState.currentUser = await resp.json();
        if (AppState.currentUser.must_change_password) {
            show_force_change_password();
        } else {
            show_app();
        }
    }
    // else: show login dialog (default)
});
```

**New functions:** `do_login()`, `do_register()`, `do_forgot_password()`,
`do_force_change_password()`, `do_change_password()`, `do_delete_account()`, `do_logout()`

**`apiFetch()` unchanged** — session cookie sent automatically by browser.

---

## Configuration (`~/.crossword.ini`)

New `[email]` section (see Email section above). The app startup (`wiring/__init__.py`)
reads and validates this section; if missing, email features are disabled with a warning
logged but the app still starts (useful for development).

---

## Dependencies

- `bcrypt` — password hashing (new)
- `smtplib`, `email` — stdlib, no new dependency

---

## Migration (`tools/migrate_auth.py`)

1. Add new columns to `users`
2. Create `sessions` table
3. Prompt for admin username/email/password → insert or update existing user id=1
   with `is_admin=1, status='active'` and bcrypt hash

---

## Implementation Order

1. **Database migration script** (`tools/migrate_auth.py`)
2. **Persistence layer** — new user/session/token methods (`sqlite_adapter.py`, `persistence.py`)
3. **Email adapter** (`crossword/adapters/email_adapter.py`)
4. **Auth handlers** (`crossword/http_server/auth_handlers.py`) — login, logout, me, register,
   forgot-password, reset-password, change-password, delete-account
5. **Admin handlers** (`crossword/http_server/admin_handlers.py`) — list users, approve,
   disable, delete; serve `/admin` page
6. **Auth middleware** in `server.py`
7. **Route registration** in `main.py` — new routes + mark protected/admin routes
8. **Replace `user_id = 1`** in all existing handlers (mechanical)
9. **Frontend** — login/register/forgot/force-change dialogs in `index.html`; corresponding
   functions in `app.js`; account dropdown in menu bar
10. **Admin page** — simple server-rendered HTML at `/admin`
11. **Tests** — login, registration flow, session expiry, password reset, admin endpoints,
    delete account cascade

---

## Files Affected

| File | Change |
|---|---|
| `crossword/ports/persistence.py` | Add abstract user/session/token methods |
| `crossword/adapters/sqlite_adapter.py` | Implement all new persistence methods |
| `crossword/adapters/email_adapter.py` | **New** — SMTP email sending |
| `crossword/http_server/server.py` | Auth middleware in dispatch loop |
| `crossword/http_server/main.py` | Register all new routes; mark protected/admin |
| `crossword/http_server/auth_handlers.py` | **New** — login/logout/me/register/forgot/reset/change-pw/delete-acct |
| `crossword/http_server/admin_handlers.py` | **New** — admin user management |
| `crossword/http_server/grid_handlers.py` | Replace `user_id = 1` (~20 occurrences) |
| `crossword/http_server/puzzle_handlers.py` | Replace `user_id = 1` (~20 occurrences) |
| `crossword/http_server/export_handlers.py` | Replace `user_id = 1` if present |
| `crossword/wiring/__init__.py` | Wire `EmailAdapter`; pass to handlers |
| `frontend/index.html` | Add all auth dialogs; hide main container initially; account dropdown |
| `frontend/static/js/app.js` | Add all auth functions; `currentUser` in AppState; page-load check |
| `frontend/admin.html` | **New** — server-rendered admin panel |
| `tools/migrate_auth.py` | **New** — DB migration + seed admin user |
