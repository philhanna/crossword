# Authentication Implementation Plan

## Decisions

| Topic | Decision |
|---|---|
| Password hashing | `sha256()` from `crossword/__init__.py` |
| Admin account creation | CLI script only (`tools/create_user.py`) |
| `confirmed` field | Always `NULL` (reserved for future use) |
| Existing puzzle data | Admin already has `id=1` in DB; handlers stop hardcoding `user_id=1` |
| `login.html` | No changes in this phase |
| Foreign key enforcement | Not enforced |
| Session cookie | `HttpOnly; SameSite=Lax` — no `Secure` flag (HTTP only) |
| Session storage | In-memory dict (lost on restart; acceptable for first slice) |
| `role` column | Not in schema — no role distinction in this phase |
| Schema migration | None needed — `users` table already exists with admin row |

---

## New Files

### `crossword/domain/user.py`
`User` dataclass with fields matching the `users` table:
`id`, `username`, `password`, `email`, `created`, `last_access`,
`confirmed`, `author_name`, `address_line_1`, `address_line_2`,
`address_city`, `address_state`, `address_zip`.

No `role` field — the schema has no role column.

### `crossword/ports/auth_port.py`
Two items:

- `AuthError(Exception)` — raised by auth use cases on bad credentials.
- `UserNotFound(Exception)` — raised by adapter when lookup finds nothing.
- `UserPort(ABC)` — abstract interface with:
  - `create_user(username, email, password_hash, **profile) -> User`
  - `get_user_by_username(username) -> User`  raises `UserNotFound`
  - `get_user_by_id(user_id) -> User`  raises `UserNotFound`
  - `update_last_access(user_id, timestamp) -> None`

### `crossword/adapters/sqlite_user_adapter.py`
`SQLiteUserAdapter(UserPort)` — takes a shared `sqlite3.Connection` (the same
connection opened by `SQLitePersistenceAdapter`).

- `create_user` — checks for duplicate username/email with `SELECT` before
  inserting (schema has no `UNIQUE` constraint to rely on), then `INSERT INTO users ...`.
  Raises `ValueError("Username already taken")` or `ValueError("Email already registered")`.
- `get_user_by_username` / `get_user_by_id` — `SELECT * FROM users WHERE ...`
- `update_last_access` — `UPDATE users SET last_access = ? WHERE id = ?`
- Private `_row_to_user(row) -> User`

### `crossword/adapters/memory_session_store.py`
`MemorySessionStore` — no abstract base (single implementation):

- Internal `dict[str, dict]` mapping token → `{id, username}`
- `create_session(user_info) -> str` — generates `uuid.uuid4()` token, stores it
- `get_session(token) -> dict | None`
- `delete_session(token) -> None` — no-op if absent

### `crossword/use_cases/auth_use_cases.py`
`AuthUseCases(user_port, session_store)`:

- `login(username, password) -> (User, token)` — fetches user by username,
  compares `sha256(password)` to stored hash, raises `AuthError` on mismatch,
  calls `update_last_access`, creates and returns session token.
- `logout(token) -> None` — deletes session.
- `get_current_user(token) -> dict | None` — delegates to `session_store.get_session`.

### `crossword/use_cases/user_use_cases.py`
`UserUseCases(user_port)`:

- `create_user(username, email, password, **profile) -> User` —
  hashes password with `sha256`, delegates to `user_port.create_user`.
  Propagates `ValueError` on duplicate username/email.

### `crossword/http_server/auth_handlers.py`
Three handlers (all public — no auth required):

- `handle_login` — `POST /api/auth/login`  
  Body: `{username, password}`.  
  On success: responds with `{username}` and sets
  `Set-Cookie: session=<token>; HttpOnly; SameSite=Lax; Path=/`.  
  On failure: `401 {error: "Invalid username or password"}` (same message for
  both bad username and bad password — no info leak).

- `handle_logout` — `POST /api/auth/logout`  
  Calls `auth_uc.logout(session_token)`.  
  Clears cookie: `Set-Cookie: session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0`.  
  Returns `200 {}`.

- `handle_me` — `GET /api/auth/me`  
  Returns `{username}` if session valid, else `401 {error: "Not authenticated"}`.

### `tools/create_user.py`
CLI script for manual admin bootstrap:

```
python tools/create_user.py --username <u> --email <e> --password <p>
```

- Reads `dbfile` from `~/.config/crossword/config.yaml` (same as the app).
- Opens the SQLite DB directly, calls `UserUseCases.create_user`.
- Prints the new user's `id` on success.
- Exits with error message (non-zero) on duplicate username/email.

---

## Modified Files

### `crossword/adapters/sqlite_persistence_adapter.py`
No schema changes — the `users` table already exists.

`SQLiteUserAdapter` needs a `sqlite3.Connection`. The simplest approach is to
expose the existing connection via a `conn` property on `SQLitePersistenceAdapter`
so `make_app` can pass it to `SQLiteUserAdapter`.

### `crossword/wiring/__init__.py`
- Instantiate `SQLiteUserAdapter` (sharing `persistence.conn`).
- Instantiate `MemorySessionStore`.
- Instantiate `AuthUseCases(user_adapter, session_store)`.
- Instantiate `UserUseCases(user_adapter)`.
- Add `auth_uc` and `user_uc` to `AppContainer`.

### `crossword/http_server/server.py`
Two changes:

**1. `Route` gets a `requires_auth` flag** (default `True`):
```python
class Route:
    def __init__(self, method, path_pattern, handler, requires_auth=True):
        ...
        self.requires_auth = requires_auth
```

`Router.add_route` gains a matching `requires_auth=True` parameter.

**2. `_handle_request` performs auth gating** after finding the route:
```python
current_user = None
if session_token and self.app:
    current_user = self.app.auth_uc.get_current_user(session_token)

if route.requires_auth and current_user is None:
    self._send_error(401, "Authentication required")
    return
```

Pass `current_user` as a keyword argument to every handler call (handlers
that don't use it accept it silently via `**kwargs`).

### `crossword/http_server/main.py`
- Register auth routes as public (`requires_auth=False`):
  - `POST /api/auth/login`
  - `POST /api/auth/logout`
  - `GET /api/auth/me`
- Static routes (`GET /`, `GET /static/...`) already implicitly public — set
  `requires_auth=False` on them too.

### Puzzle, export, import, and word handlers
Replace every `user_id = 1` hardcode with `user_id = current_user["id"]`.

Affected locations:
| File | Occurrences |
|---|---|
| `puzzle_handlers.py` | All handlers that call `puzzle_uc` methods |
| `export_handlers.py` | `handle_export_puzzle_to_acrosslite`, `..._xml`, `..._nytimes`, `..._json` (literal `1` passed inline) |
| `import_handlers.py` | `handle_import_puzzle_from_acrosslite` |
| `word_handlers.py` | `handle_get_word_constraints`, `handle_get_ranked_suggestions` |

---

## Test Files

### `crossword/tests/test_auth_use_cases.py`
- `test_login_success` — valid credentials return `(user, token)`
- `test_login_wrong_password` — raises `AuthError`
- `test_login_unknown_user` — raises `AuthError` (same error, no info leak)
- `test_logout_removes_session`
- `test_get_current_user_valid_token`
- `test_get_current_user_invalid_token_returns_none`

### `crossword/tests/adapters/test_sqlite_user_adapter.py`
Uses an in-memory SQLite DB (`:memory:`) with the schema applied.

- `test_create_user_returns_user_with_id`
- `test_create_user_duplicate_username_raises_value_error`
- `test_create_user_duplicate_email_raises_value_error`
- `test_get_user_by_username_success`
- `test_get_user_by_username_not_found_raises`
- `test_get_user_by_id_success`
- `test_update_last_access`

### `crossword/tests/test_user_use_cases.py`
- `test_create_user_hashes_password` — stored hash equals `sha256(plain)`
- `test_create_user_propagates_duplicate_username_error`
- `test_create_user_propagates_duplicate_email_error`

### `crossword/tests/test_auth_handlers.py`
Uses mocked `app.auth_uc` and a minimal mock `request_handler`.

- `test_handle_login_success_sets_cookie`
- `test_handle_login_bad_credentials_returns_401` (same message for bad username and bad password)
- `test_handle_logout_clears_cookie`
- `test_handle_me_authenticated`
- `test_handle_me_unauthenticated_returns_401`

### `crossword/tests/test_http_server.py` (updates)
Existing handler tests that assert `puzzle_uc` method calls with `user_id=1`
need `current_user={"id": 1, "username": "test", "role": "user"}` added to
each handler call, e.g.:

```python
handle_create_puzzle(
    (), {}, {"name": "demo", "size": 15}, None, request_handler,
    app=app, current_user={"id": 1, "username": "test"}
)
```

---

## Implementation Order

1. `User` domain model
2. `UserPort` / `AuthError` / `UserNotFound` port
3. Expose `conn` property on `SQLitePersistenceAdapter`
4. `SQLiteUserAdapter`
5. `MemorySessionStore`
6. `UserUseCases`
7. `AuthUseCases`
8. Wire everything in `wiring/__init__.py` and `AppContainer`
9. `Route.requires_auth` flag + auth gating in `server.py`
10. Auth handlers (`auth_handlers.py`) + register routes in `main.py`
11. Replace `user_id = 1` hardcodes in all handlers
12. `tools/create_user.py` CLI
13. Tests (adapter, use case, handler, existing handler updates)
