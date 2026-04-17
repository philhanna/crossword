# Phase 1 Implementation Plan — PostgreSQL Backend

## Goal

Replace the SQLite storage backend with PostgreSQL, running locally.
The application must work identically to today after this phase — same features,
same behaviour, same tests passing. No auth changes, no deployment changes.

## Background

Two adapters currently wrap a single SQLite connection:

- `SQLitePersistenceAdapter` — stores puzzles (implements `PersistencePort`)
- `SQLiteUserAdapter` — stores users and profile data (implements `UserPort`)
  - Receives `persistence_adapter.conn` directly (they share one connection)

Both will get PostgreSQL counterparts. The shared-connection pattern is replicated
by passing one `psycopg2` connection to both adapters.

---

## Step 1 — Add dependency

In `pyproject.toml`, add `psycopg2-binary` to `dependencies`:

```toml
dependencies = ["PyYAML", "psycopg2-binary"]
```

`psycopg2-binary` bundles its own libpq — no system library needed.
(Switch to `psycopg2` without `-binary` if you ever build a Docker image that
compiles from source, but binary is fine for local dev.)

---

## Step 2 — Config: add `database_url` support

**File:** `crossword/__init__.py` → `init_config()`

Add `DATABASE_URL` environment variable support alongside the existing YAML config.
Env var takes precedence over the YAML file (standard 12-factor convention):

```python
import os

def init_config():
    defaults = {
        'dbfile': os.path.join(project_root_dir, "examples", "sample.crossword.db"),
        'log_level': "INFO",
    }
    filename = os.path.expanduser("~/.config/crossword/config.yaml")
    if os.path.exists(filename):
        with open(filename) as f:
            loaded = yaml.safe_load(f) or {}
        options = {**defaults, **loaded}
    else:
        options = defaults

    # Environment variable overrides config file
    if os.environ.get('DATABASE_URL'):
        options['database_url'] = os.environ['DATABASE_URL']

    return options
```

`database_url` in the YAML file also works (for local dev without env vars):

```yaml
database_url: "postgresql://user:password@localhost:5432/crossword"
```

---

## Step 3 — PostgresPersistenceAdapter

**New file:** `crossword/adapters/postgres_persistence_adapter.py`

This implements `PersistencePort` identically to `SQLitePersistenceAdapter`.

### Schema

The schema is equivalent to SQLite's, with these PostgreSQL-specific changes:

| SQLite | PostgreSQL |
|--------|------------|
| `INTEGER PRIMARY KEY` (auto-increment) | `SERIAL PRIMARY KEY` |
| `?` parameter placeholders | `%s` parameter placeholders |
| `sqlite3.Row` dict-like rows | `psycopg2.extras.RealDictCursor` |
| `conn.row_factory = sqlite3.Row` | pass `cursor_factory` to cursor |

```sql
CREATE TABLE IF NOT EXISTS puzzles (
    id          SERIAL PRIMARY KEY,
    userid      INTEGER NOT NULL,
    puzzlename  TEXT NOT NULL,
    created     TEXT NOT NULL,
    modified    TEXT NOT NULL,
    last_mode   TEXT NOT NULL DEFAULT 'puzzle'
                    CHECK (last_mode IN ('grid', 'puzzle')),
    jsonstr     TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_puzzles_userid_puzzlename
    ON puzzles (userid, puzzlename);
```

### Key implementation notes

- Use `psycopg2.extras.RealDictCursor` so rows are accessed by column name,
  matching how `sqlite3.Row` is used in the existing adapter.
- The `conn` object is a plain `psycopg2` connection. Pass it in via the constructor
  (same pattern as `SQLiteUserAdapter` receiving the SQLite connection).
- Call `conn.commit()` after every mutating operation (INSERT, UPDATE, DELETE).
  SQLite's default isolation level auto-commits; psycopg2 does not.
- `init_schema()` — same public method name as in the SQLite adapter, used by tests
  and the init script.
- No `_ensure_schema_compatibility()` needed for phase 1. The init script creates
  the schema from scratch. (Forward migrations can be added later.)

### Constructor signature

```python
class PostgresPersistenceAdapter:
    def __init__(self, conn):
        self.conn = conn
        self.init_schema()
```

---

## Step 4 — PostgresUserAdapter

**New file:** `crossword/adapters/postgres_user_adapter.py`

Implements `UserPort`, same method signatures as `SQLiteUserAdapter`.

### Schema changes

| SQLite | PostgreSQL |
|--------|------------|
| `BLOB` (for password hash) | `BYTEA` |
| `INTEGER PRIMARY KEY` | `SERIAL PRIMARY KEY` |
| `?` placeholders | `%s` placeholders |
| last insert id via `cursor.lastrowid` | use `RETURNING id` clause |

```sql
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    username        TEXT,
    password        BYTEA,
    created         TEXT,
    last_access     TEXT,
    email           TEXT,
    confirmed       TEXT,
    author_name     TEXT,
    address_line_1  TEXT,
    address_line_2  TEXT,
    address_city    TEXT,
    address_state   TEXT,
    address_zip     TEXT
);
```

### Key implementation note

`cursor.lastrowid` does not work in psycopg2. Use `RETURNING id` in the INSERT and
fetch the result:

```python
cursor.execute(
    "INSERT INTO users (...) VALUES (...) RETURNING id",
    (...)
)
new_id = cursor.fetchone()['id']
conn.commit()
```

---

## Step 5 — Schema init script

**New file:** `tools/dev/init_db.py`

Creates all tables in a target PostgreSQL database. Safe to run on an empty DB
(uses `CREATE TABLE IF NOT EXISTS`). Exits with an error if the DB is not reachable.

```
Usage: python tools/dev/init_db.py [--url DATABASE_URL]

If --url is omitted, reads DATABASE_URL from the environment.
```

Contains the DDL for both `puzzles` and `users` tables. Calls `init_schema()` on
both adapter classes (so the DDL lives in one place — the adapters — not duplicated
in this script).

---

## Step 6 — Data migration script

**New file:** `tools/dev/migrate_sqlite_to_postgres.py`

Copies all rows from an existing SQLite DB into the PostgreSQL DB.

```
Usage: python tools/dev/migrate_sqlite_to_postgres.py \
           --sqlite examples/samples.db \
           --url DATABASE_URL
```

Steps:
1. Open SQLite DB read-only.
2. Connect to PostgreSQL.
3. Copy `users` table rows (mapping `BLOB` → `BYTEA` for the password field).
4. Copy `puzzles` table rows (all columns map directly; `jsonstr` is TEXT in both).
5. Print a summary: N users, M puzzles migrated.

Run this once when switching. It is idempotent if the target DB is empty
(the unique index on `puzzles(userid, puzzlename)` prevents duplicate rows).

---

## Step 7 — Update wiring

**File:** `crossword/wiring/__init__.py` → `make_app()`

Select the adapter based on config. SQLite remains the default so existing local
dev still works without any config change.

```python
def make_app(config=None):
    config = config or init_config()

    if config.get('database_url'):
        import psycopg2
        conn = psycopg2.connect(config['database_url'])
        persistence = PostgresPersistenceAdapter(conn)
        user_adapter = PostgresUserAdapter(conn)
    else:
        dbfile = config['dbfile']
        persistence = SQLitePersistenceAdapter(dbfile)
        user_adapter = SQLiteUserAdapter(persistence.conn)

    # rest of wiring unchanged ...
```

---

## Step 8 — Tests

The existing tests in `crossword/tests/adapters/test_sqlite_adapter.py` test the
SQLite adapter directly. Add a parallel file:

**New file:** `crossword/tests/adapters/test_postgres_adapter.py`

- Use a fixture that connects to a local test PostgreSQL DB
  (e.g. `postgresql://localhost/crossword_test`).
- Skip the whole module if `TEST_DATABASE_URL` is not set, so CI without Postgres
  does not fail.
- The test cases mirror `test_sqlite_adapter.py` exactly — same assertions,
  different adapter under test.

```python
import pytest
import os

pytestmark = pytest.mark.skipif(
    not os.environ.get('TEST_DATABASE_URL'),
    reason="TEST_DATABASE_URL not set"
)
```

---

## Step 9 — Local PostgreSQL setup

Install PostgreSQL locally and create a database:

```
sudo apt install postgresql        # Ubuntu/Debian
# or
brew install postgresql@16         # macOS

createdb crossword
```

Store connection strings in a local `.env` file (not committed):

```
# .env  — do not commit
DATABASE_URL=postgresql://localhost/crossword
TEST_DATABASE_URL=postgresql://localhost/crossword_test
```

Add `.env` to `.gitignore`.

---

## Step 10 — Smoke test procedure

1. Load env vars: `source .env`
2. Run init script: `python tools/dev/init_db.py`
3. Optionally migrate existing data:
   ```
   python tools/dev/migrate_sqlite_to_postgres.py --sqlite examples/samples.db
   ```
   (script reads `DATABASE_URL` from the environment if `--url` is omitted)
4. Start the server: `python -m crossword.http_server`
5. Open the browser and exercise the full flow: create a grid, create a puzzle,
   fill some words, save and reopen.
6. Restart the server and confirm data persisted.
7. Run Postgres-backed tests:
   ```
   pytest crossword/tests/adapters/test_postgres_adapter.py
   ```

---

## Files changed / created

| File | Action |
|------|--------|
| `pyproject.toml` | Add `psycopg2-binary` dependency |
| `.gitignore` | Add `.env` |
| `crossword/__init__.py` | Add `DATABASE_URL` env var support |
| `crossword/adapters/postgres_persistence_adapter.py` | New |
| `crossword/adapters/postgres_user_adapter.py` | New |
| `crossword/wiring/__init__.py` | Select adapter based on config |
| `tools/dev/init_db.py` | New — creates Postgres schema |
| `tools/dev/migrate_sqlite_to_postgres.py` | New — copies SQLite data to Postgres |
| `crossword/tests/adapters/test_postgres_adapter.py` | New |

No changes to use cases, domain models, HTTP handlers, frontend, or the SQLite
adapters themselves. SQLite continues to work as before.
