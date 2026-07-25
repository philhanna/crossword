# Submissions Editor — Implementation Plan

Implementation plan for
[§4 Submissions editor](restructured_crossword_composer_requirements.md#4-submissions-editor)
of the restructuring requirements. It fleshes out
[restructuring_impl.md](restructuring_impl.md)'s Phase 1 (the submissions-related
slice) and Phase 2 checklist items into concrete signatures, DDL, endpoints,
and a database migration — the same level of detail
[puzzle_state.md](puzzle_state.md) gave the state-machine feature it now
supersedes. Nothing here is executed by this plan; it's a blueprint for later
work, ordered bottom-up through the hexagonal layers.

## Contents

- [1. Data model](#1-data-model)
- [2. Domain changes](#2-domain-changes)
- [3. Port changes](#3-port-changes)
- [4. Adapter changes](#4-adapter-changes)
- [5. Use-case changes](#5-use-case-changes)
- [6. Integration with the existing puzzle-state code](#6-integration-with-the-existing-puzzle-state-code)
- [7. HTTP layer](#7-http-layer)
- [8. Frontend — submissions editor SPA](#8-frontend--submissions-editor-spa)
- [9. Existing dashboard changes](#9-existing-dashboard-changes)
- [10. Migration of the existing database](#10-migration-of-the-existing-database)
- [11. Tests](#11-tests)
- [12. Suggested implementation order](#12-suggested-implementation-order)

---

## 1. Data model

Three new tables, plus three columns dropped from `puzzles` (§4.3, decision 1
§4.5). All new columns use the underscored convention (Appendix A.3).

```sql
CREATE TABLE IF NOT EXISTS publishers (
    id                TEXT PRIMARY KEY,      -- 3-char code, e.g. 'NYT'
    name              TEXT NOT NULL,
    email             TEXT,
    submission_limits TEXT,
    payment_info      TEXT,
    spec_url          TEXT
);

CREATE TABLE IF NOT EXISTS editors (
    id           INTEGER PRIMARY KEY,
    publisher_id TEXT NOT NULL REFERENCES publishers(id),
    name         TEXT NOT NULL,
    email        TEXT
);

CREATE INDEX IF NOT EXISTS idx_editors_publisher_id
    ON editors(publisher_id);

CREATE TABLE IF NOT EXISTS submission_events (
    id               INTEGER PRIMARY KEY,
    puzzle_id        INTEGER NOT NULL REFERENCES puzzles(id),
    timestamp        TEXT NOT NULL,
    event_type       TEXT NOT NULL CHECK (event_type IN (
                          'submitted', 'email_sent', 'email_received',
                          'accepted', 'rejected', 'archived', 'comment')),
    resulting_state  TEXT CHECK (resulting_state IN (
                          'submitted', 'published', 'finished', 'archived')),
    publisher_id     TEXT REFERENCES publishers(id),
    editor_id        INTEGER REFERENCES editors(id),
    body             TEXT
);

CREATE INDEX IF NOT EXISTS idx_submission_events_puzzle_id
    ON submission_events(puzzle_id);
```

Notes:

- No `user_id` on `publishers`/`editors` — global reference data (Appendix
  A.7).
- `resulting_state`'s `CHECK` is `finished` for a rejection (decision 2,
  §4.5), never `draft`/`filled` — those stay ladder-only (§4.2).
- `puzzles.publisher`, `puzzles.date_submitted`, `puzzles.date_published`
  (currently at
  [sqlite_persistence_adapter.py:75-77](../../crossword/adapters/sqlite_persistence_adapter.py#L75-L77))
  are dropped from the schema a *fresh* database gets. `puzzles.state`'s
  `CHECK` constraint is **left as-is** (still allows all six values) — see
  §10 for why existing rows can keep a physical `submitted`/`published`/
  `archived` value harmlessly after migration.
- Because SQLite `CREATE TABLE IF NOT EXISTS` can't retroactively drop
  columns from an already-existing `puzzles` table, dropping the three
  columns only takes effect for genuinely new databases (`:memory:`, or a
  brand-new file). An existing production database keeps the physical
  columns until the rebuild migration in §10 runs; the running adapter code
  simply stops reading/writing them (§4). Dead columns on an un-migrated DB
  are harmless.

---

## 2. Domain changes

New module `crossword/domain/submission_event.py`, mirroring the style of
[puzzle_state.py](../../crossword/domain/puzzle_state.py) — the closed enum
(Appendix A.2) plus the `event_type → resulting_state` table from §4.4.3,
pinned in code as the single source of truth:

```python
"""
Submission event types and the puzzles.state value each one produces.
See docs/dev/restructured_crossword_composer_requirements.md §4.4.3.
"""

from crossword.domain import puzzle_state as ps

SUBMITTED = "submitted"
EMAIL_SENT = "email_sent"
EMAIL_RECEIVED = "email_received"
ACCEPTED = "accepted"
REJECTED = "rejected"
ARCHIVED = "archived"
COMMENT = "comment"

ALL_EVENT_TYPES = [
    SUBMITTED, EMAIL_SENT, EMAIL_RECEIVED,
    ACCEPTED, REJECTED, ARCHIVED, COMMENT,
]

# event_type -> resulting_state written on the event row; None = no state change
RESULTING_STATE = {
    SUBMITTED: ps.SUBMITTED,
    REJECTED: ps.FINISHED,       # decision 2, §4.5 — no separate 'rejected' state
    ACCEPTED: ps.PUBLISHED,
    EMAIL_SENT: None,
    EMAIL_RECEIVED: None,
    ARCHIVED: ps.ARCHIVED,
    COMMENT: None,
}
```

New pure helper `crossword/domain/publisher_code.py`, used by both the
migration tool (§10) and `PublisherUseCases` (§5.1) — kept dependency-free so
the migration tool can use it without importing adapters, matching
[migrate_puzzle_state.py](../../tools/dev/migrate_puzzle_state.py)'s "no
adapter import" convention:

```python
def derive_publisher_code(free_text: str, existing_codes: set[str]) -> str:
    """
    Turn a free-text publisher value into a 3-char code.

    Existing production `puzzles.publisher` values already look like codes
    ('NYT', 'LAT', 'WSJ' — §4.3.2), so a short alnum value is used as-is.
    Longer values are reduced to their first 3 alnum characters, uppercased,
    with a trailing digit appended on collision with a different original
    value already mapped into existing_codes.
    """
```

No third-party Markdown/HTML library lives in `crossword/domain/` or
`crossword/adapters/` — decision 5 (§4.5) puts that conversion at the
frontend edge only (§8), not the backend.

---

## 3. Port changes

Extend `crossword/ports/persistence_port.py` rather than adding a sibling
port: submissions/publishers/editors share the same SQLite connection and
transaction boundary as puzzles, and every method still takes `(user_id,
name)` for puzzle-scoped operations — consistent with the rest of the port,
which never exposes the internal `puzzles.id` to callers.

```python
# --- Publishers (global, no user_id — Appendix A.7) -------------------------

@abstractmethod
def create_publisher(self, id: str, name: str, email: str | None = None,
                      submission_limits: str | None = None,
                      payment_info: str | None = None,
                      spec_url: str | None = None) -> None: ...

@abstractmethod
def update_publisher(self, id: str, name: str, email: str | None = None,
                      submission_limits: str | None = None,
                      payment_info: str | None = None,
                      spec_url: str | None = None) -> None:
    """Full replace (PUT semantics), consistent with the rest of the API."""

@abstractmethod
def delete_publisher(self, id: str) -> None:
    """Raises PersistenceError if referenced by editors or submission_events
    (Appendix A.4) — no cascade."""

@abstractmethod
def get_publisher(self, id: str) -> dict | None: ...

@abstractmethod
def list_publishers(self) -> list[dict]: ...

# --- Editors ------------------------------------------------------------

@abstractmethod
def create_editor(self, publisher_id: str, name: str,
                   email: str | None = None) -> int:
    """Returns the new editor's id."""

@abstractmethod
def update_editor(self, id: int, name: str, email: str | None = None) -> None: ...

@abstractmethod
def delete_editor(self, id: int) -> None: ...

@abstractmethod
def get_editor(self, id: int) -> dict | None: ...

@abstractmethod
def list_editors(self, publisher_id: str) -> list[dict]: ...

# --- Submission events (append-only, §4.3.1) -----------------------------

@abstractmethod
def append_submission_event(self, user_id: int, name: str, event_type: str, *,
                             resulting_state: str | None = None,
                             publisher_id: str | None = None,
                             editor_id: int | None = None,
                             body: str | None = None) -> dict:
    """
    Appends a timestamped event row for the named puzzle and returns it.

    Raises PersistenceError if the puzzle isn't found, or if editor_id is
    given but doesn't belong to publisher_id (§4.4.5).
    """

@abstractmethod
def get_submission_history(self, user_id: int, name: str) -> list[dict]:
    """All events for the puzzle, oldest first."""

@abstractmethod
def get_current_submission_status(self, user_id: int, name: str) -> dict:
    """
    {"state": <effective state>, "publisher_id": <current publisher or None>}

    `state` is the `resulting_state` of the most recent event that has one
    (Appendix A.6); if the puzzle has no submission_events rows at all, falls
    back to the stored `puzzles.state` ladder value (§4.2) — never None.
    `publisher_id` is the `publisher_id` of the most recent event that has
    one, independent of `state`'s derivation (a rejection can still be the
    most recent publisher-bearing event even though its `resulting_state`
    falls back to 'finished').
    """
```

`list_puzzle_summaries` (existing method, currently returning `publisher`/
`date_submitted`/`date_published` per row —
[persistence_port.py:154-172](../../crossword/ports/persistence_port.py#L154-L172))
drops those three keys; callers that need submission status now call
`get_current_submission_status` explicitly (§6).

---

## 4. Adapter changes

All on `SQLitePersistenceAdapter`:

- `_ensure_schema_compatibility()`
  ([sqlite_persistence_adapter.py:53-88](../../crossword/adapters/sqlite_persistence_adapter.py#L53-L88)):
  add the three `CREATE TABLE IF NOT EXISTS` statements + indexes from §1;
  drop `publisher`/`date_submitted`/`date_published` from the `puzzles`
  DDL (only affects fresh databases, per §1's note).
- `save_puzzle`, `load_puzzle`, `delete_puzzle`, `rename_puzzle` — unchanged.
- `set_puzzle_state`/`get_puzzle_state`
  ([sqlite_persistence_adapter.py:188-232](../../crossword/adapters/sqlite_persistence_adapter.py#L188-L232)):
  drop the `publisher`/`date_submitted`/`date_published` parameters and
  columns from both. `set_puzzle_state` becomes `(user_id, name, state)` —
  it's now only ever called with a ladder value (§6).
- `list_puzzle_summaries`
  ([sqlite_persistence_adapter.py:279-307](../../crossword/adapters/sqlite_persistence_adapter.py#L279-L307)):
  drop the three columns from the `SELECT` and the returned dicts.
- New methods implementing §3's publisher/editor/submission-event port
  additions:
  - `delete_publisher`: `SELECT EXISTS(SELECT 1 FROM editors WHERE
    publisher_id = ?) OR EXISTS(SELECT 1 FROM submission_events WHERE
    publisher_id = ?)` guard before the `DELETE`, raising `PersistenceError`
    on a hit — same style as the adapter's existing rowcount-based guards.
  - `append_submission_event`: resolves `puzzle_id` via `SELECT id FROM
    puzzles WHERE userid = ? AND puzzlename = ?`; if `editor_id` is given,
    checks `SELECT publisher_id FROM editors WHERE id = ?` matches the
    passed `publisher_id` before inserting, raising `PersistenceError`
    otherwise; `timestamp` is `datetime.now().isoformat()`, matching
    `save_puzzle`'s existing timestamp convention.
  - `get_current_submission_status`: two queries — `SELECT resulting_state
    FROM submission_events WHERE puzzle_id = ? AND resulting_state IS NOT
    NULL ORDER BY id DESC LIMIT 1` (falls back to `puzzles.state` if empty),
    and `SELECT publisher_id FROM submission_events WHERE puzzle_id = ? AND
    publisher_id IS NOT NULL ORDER BY id DESC LIMIT 1`. Ordering by `id
    DESC` rather than `timestamp DESC` avoids ties when two events share a
    timestamp (same second).

---

## 5. Use-case changes

### 5.1 `crossword/use_cases/publisher_use_cases.py` — `PublisherUseCases`

```python
class PublisherUseCases:
    def __init__(self, persistence: PersistencePort):
        self.persistence = persistence

    def create_publisher(self, id, name, email=None, submission_limits=None,
                          payment_info=None, spec_url=None) -> dict: ...
    def update_publisher(self, id, name, email=None, submission_limits=None,
                          payment_info=None, spec_url=None) -> dict: ...
    def delete_publisher(self, id) -> None: ...
    def get_publisher(self, id) -> dict: ...
    def list_publishers(self) -> list[dict]: ...
```

Validates `id` is non-empty and `name` is non-empty; otherwise thin
pass-through to the port (§4.4.1).

### 5.2 `crossword/use_cases/editor_use_cases.py` — `EditorUseCases`

```python
class EditorUseCases:
    def __init__(self, persistence: PersistencePort):
        self.persistence = persistence

    def create_editor(self, publisher_id, name, email=None) -> dict: ...
    def update_editor(self, id, name, email=None) -> dict: ...
    def delete_editor(self, id) -> None: ...
    def list_editors(self, publisher_id) -> list[dict]: ...
```

Validates the publisher exists (via `persistence.get_publisher`) before
creating an editor under it (§4.4.2).

### 5.3 `crossword/use_cases/submission_use_cases.py` — `SubmissionUseCases`

One method per event type (§4.4.3's table), each validating inputs then
delegating to `append_submission_event` with the `resulting_state` from
`submission_event.RESULTING_STATE`:

```python
class SubmissionUseCases:
    def __init__(self, persistence: PersistencePort, editor_uc: EditorUseCases | None = None):
        self.persistence = persistence
        self.editor_uc = editor_uc

    def submit(self, user_id, name, publisher_id, editor_id=None, body=None) -> dict:
        """publisher_id is required — a submission is always to a publisher."""

    def reject(self, user_id, name, publisher_id, editor_id=None, body=None) -> dict:
        """publisher_id required (decision 2 — resulting_state='finished')."""

    def accept(self, user_id, name, publisher_id, editor_id=None, body=None) -> dict:
        """publisher_id required (resulting_state='published')."""

    def log_email_sent(self, user_id, name, publisher_id=None, editor_id=None, body=None) -> dict: ...
    def log_email_received(self, user_id, name, publisher_id=None, editor_id=None, body=None) -> dict: ...
    def archive(self, user_id, name, body=None) -> dict: ...

    def comment(self, user_id, name, body) -> dict:
        """body is required and non-empty — a comment with no text is meaningless."""

    def get_history(self, user_id, name) -> list[dict]: ...
    def get_current_status(self, user_id, name) -> dict: ...
```

Each event method validates `event_type in ALL_EVENT_TYPES` (trivially true
since callers can't pass an arbitrary type here — enforced structurally by
having one method per type) and, when `editor_id` is given, that it belongs
to `publisher_id`: `self.editor_uc.list_editors(publisher_id)` and check
membership before calling the port (raises `ValueError`, not
`PersistenceError`, for this input-validation failure — the port-level check
in §4 is the storage-layer backstop for callers that bypass the use case,
e.g. direct adapter tests).

Email drafting (§4.4.4), same module:

```python
def draft_submission_email(self, user_id, name, publisher_id, editor_id=None) -> dict:
    """
    Returns {"body": "<markdown>"}. Composes a template using the puzzle's
    title, the publisher's submission_limits/email, and the editor's name
    if editor_id is given. Backend-only — no Markdown->HTML conversion or
    ClipboardItem write here (decision 5, that's frontend, §8).
    """
```

First-draft template (adjustable — flag for product review before wiring
into the UI):

```
Dear {editor_name or "Editors"},

I am submitting a crossword puzzle, "{puzzle_title}", for your consideration.

{publisher.submission_limits, if set}

Please let me know if you have any questions.

Best regards,
{config author_name}
```

### 5.4 Wiring

`crossword/wiring/__init__.py`: add `publisher_uc`, `editor_uc`,
`submission_uc` to `AppContainer.__init__` and construct them in
`make_app()` alongside `puzzle_uc`/`word_uc`, all sharing the one
`persistence` adapter instance already created there.

---

## 6. Integration with the existing puzzle-state code

This is the part not explicitly spelled out in §4 but required to make it
correct, since `puzzles.state`/`publisher` are live, already-shipped code
today (per the requirements doc's header note).

- **`PuzzleUseCases.set_puzzle_state`**
  ([puzzle_use_cases.py:207-251](../../crossword/use_cases/puzzle_use_cases.py#L207-L251))
  currently lets a caller set *any* of the six states, with `publisher`/
  `date_submitted`/`date_published` required for `submitted`/`published`.
  Per §4.2, those three states are "no longer written to `puzzles.state`
  directly." Narrow this method to only accept `draft`/`filled`/`finished`
  (`ps.COMPLETION_LADDER`), raising `ValueError` for the other three —
  those transitions now only happen through `SubmissionUseCases`
  (`submit`/`accept`/`archive`/`reject`). In practice this method becomes
  rarely used directly (the ladder is auto-set on save via
  `_auto_set_state_on_save`,
  [puzzle_use_cases.py:164-167](../../crossword/use_cases/puzzle_use_cases.py#L164-L167));
  keep it only for the dashboard's "Reopen" action (→ `draft`).
- **`PuzzleUseCases.get_puzzle_state`**
  ([puzzle_use_cases.py:188-205](../../crossword/use_cases/puzzle_use_cases.py#L188-L205)):
  drop `publisher`/`date_submitted`/`date_published` from the returned dict
  to match the adapter change (§4).
- **`PuzzleUseCases.get_dashboard`/`_dashboard_row`**
  ([puzzle_use_cases.py:611-650](../../crossword/use_cases/puzzle_use_cases.py#L611-L650)):
  replace the `summary["publisher"]`/`summary["date_submitted"]`/
  `summary["date_published"]` reads with a call to
  `submission_uc.get_current_status(user_id, name)`, and use its `state`
  in place of `summary["state"]` for the row's `state` field (Appendix A.8).
  Requires `PuzzleUseCases` to receive a `submission_uc` reference — add a
  constructor parameter, same pattern as the existing `word_uc`/
  `grid_generator` optional deps at
  [puzzle_use_cases.py:54-58](../../crossword/use_cases/puzzle_use_cases.py#L54-L58).
- **`crossword/http_server/puzzle_handlers.py`**
  ([puzzle_handlers.py:285,315,338-340](../../crossword/http_server/puzzle_handlers.py#L285-L340)):
  the `PUT /api/puzzles/{name}/state` handler's docstring/body no longer
  reference `publisher`/`date_submitted`/`date_published`; it now 400s if
  the target state isn't in `ps.COMPLETION_LADDER`, with an error message
  pointing at the submissions editor for the other transitions.
- **`tools/dev/swagger.py`**
  (lines ~116-118, ~304-306, ~449-461): update the `PUT
  /api/puzzles/{name}/state` spec entry to drop the publisher/date fields
  and narrow the allowed `state` enum to the ladder three; add spec entries
  for all the new §7 routes. Run `python3 tools/dev/swagger.py --check`
  after wiring the new routes to confirm no gaps.

---

## 7. HTTP layer

New file `crossword/http_server/submission_handlers.py`, sibling of
`puzzle_handlers.py`. One route per use case; publishers/editors are
top-level resources (no `user_id` scoping, Appendix A.7), submission events
are nested under the owning puzzle:

| Method | Path | Handler |
|---|---|---|
| GET | `/api/publishers` | `handle_list_publishers` |
| POST | `/api/publishers` | `handle_create_publisher` |
| GET | `/api/publishers/([^/]+)` | `handle_get_publisher` |
| PUT | `/api/publishers/([^/]+)` | `handle_update_publisher` |
| DELETE | `/api/publishers/([^/]+)` | `handle_delete_publisher` |
| GET | `/api/publishers/([^/]+)/editors` | `handle_list_editors` |
| POST | `/api/publishers/([^/]+)/editors` | `handle_create_editor` |
| PUT | `/api/editors/(\d+)` | `handle_update_editor` |
| DELETE | `/api/editors/(\d+)` | `handle_delete_editor` |
| GET | `/api/puzzles/([^/]+)/submission-events` | `handle_get_submission_history` |
| GET | `/api/puzzles/([^/]+)/submission-status` | `handle_get_submission_status` |
| POST | `/api/puzzles/([^/]+)/submission-events/submit` | `handle_submit` |
| POST | `/api/puzzles/([^/]+)/submission-events/reject` | `handle_reject` |
| POST | `/api/puzzles/([^/]+)/submission-events/accept` | `handle_accept` |
| POST | `/api/puzzles/([^/]+)/submission-events/email-sent` | `handle_log_email_sent` |
| POST | `/api/puzzles/([^/]+)/submission-events/email-received` | `handle_log_email_received` |
| POST | `/api/puzzles/([^/]+)/submission-events/archive` | `handle_archive` |
| POST | `/api/puzzles/([^/]+)/submission-events/comment` | `handle_comment` |
| POST | `/api/puzzles/([^/]+)/submission-events/draft-email` | `handle_draft_submission_email` |

Registered in `crossword/http_server/main.py::register_routes()`, same
pattern as the existing `puzzle_handlers`/`word_handlers` blocks
([main.py:87-122](../../crossword/http_server/main.py#L87-L122)). Error
conventions match the existing handlers: 400 on `ValueError` (bad
`event_type` implicitly via wrong route, missing required field, editor/
publisher mismatch), 404 when `PersistenceError` indicates "not found" (a
publisher/editor/puzzle id that doesn't exist), 409-style 400 on the
publisher delete guard.

---

## 8. Frontend — submissions editor SPA

Per decision 7 (§4.5), this is its own SPA, not a new state in the existing
`home`/`grid-editor`/`puzzle-editor` menu machine
([frontend/index.html](../../frontend/index.html),
[frontend/static/js/state.js](../../frontend/static/js/state.js)). Using the
directory layout already named in
[restructuring_impl.md §6.4](restructuring_impl.md#64-submissions-editor-spa-new):
`frontend/submissions-editor/index.html` + `submissions.js`, served at
`/submissions/`.

### 8.1 Minimal static-serving change

This doc only needs to stand up *this one* SPA, not the full four-way split
restructuring_impl.md's Phase 0/6 eventually does. Add two routes to
`crossword/http_server/main.py`, reusing
`static_handlers.get_frontend_dir()`'s pattern but rooted at
`frontend/submissions-editor/` instead of `frontend/`:

```
GET  /submissions/               -> serve frontend/submissions-editor/index.html
GET  /submissions/static/(.+)$   -> serve frontend/submissions-editor/static/<path>
```

Implemented as two small handlers in a new
`crossword/http_server/submission_static_handlers.py` (copy-and-adapt
`handle_get_index`/`handle_get_static`, same traversal guard). When the
full four-SPA restructuring (Phase 0/6) happens later, these get folded into
the generalized per-app static serving described there — no rework needed
now, just don't hand-roll something incompatible with that direction.

### 8.2 Screens

- **Publisher/editor admin** — list publishers (table: id, name, email,
  spec_url link); create/edit/delete a publisher; per-publisher expandable
  editor list with create/edit/delete.
- **Puzzle picker** — when opened without a `?puzzle=` query param, a list
  of puzzles with their current submission status (via
  `GET /api/puzzles/{name}/submission-status` per row, or a new bulk
  endpoint if per-row fetches prove too slow); opened *with* `?puzzle=name`
  (linked from the dashboard, §9) it jumps straight to the detail view.
- **Puzzle detail / timeline** — renders `get_submission_history` as a
  reverse-chronological list (event type, timestamp, publisher/editor name,
  a truncated `body` preview); a status badge from `get_current_status`;
  action buttons for each event type, each opening a small form (publisher
  picker, optional editor picker scoped to that publisher, optional body
  textarea) that POSTs to the matching §7 route and re-renders the timeline.
- **Email draft modal** — opened from the "Submit" action: fetches
  `draft-email` for the chosen publisher/editor, shows the Markdown in an
  editable textarea, with:
  - **"Copy for Gmail"** — client-side Markdown→HTML, writes both
    `text/html` and `text/plain` via `ClipboardItem` (§4.4.4, decision 5).
  - **Paste-in box for a reply** — client-side HTML→Markdown conversion on
    paste, then POSTs the result as `email_received`'s `body`.
  - No send button anywhere (decision 4).

### 8.3 Markdown ⇄ HTML conversion

Purely client-side per decision 5 — nothing in the backend does this (§2,
§5.3). Vendor two small, dependency-free, MIT-licensed libraries into
`frontend/submissions-editor/static/js/vendor/` (e.g. `marked` for
Markdown→HTML, `turndown` for HTML→Markdown) rather than hand-rolling a
converter — email bodies use a modest but real subset (bold/italic/links/
lists/paragraphs) that a hand-rolled regex converter would get wrong at the
edges. Flag this dependency choice for confirmation before implementation,
since it's the one place this feature pulls in third-party frontend code.

---

## 9. Existing dashboard changes

The current dashboard already has a full manual state-setting UI that this
feature supersedes for three of its six states:
[frontend/static/js/dashboard.js:320-410](../../frontend/static/js/dashboard.js#L320-L410)
(the `#state-dialog` modal — state dropdown + publisher/date inputs) and its
markup in
[frontend/index.html:236-238](../../frontend/index.html#L236-L238).

- Narrow `ALL_STATES`
  ([dashboard.js:8](../../frontend/static/js/dashboard.js#L8)) usage in the
  state-dialog dropdown to `ps.COMPLETION_LADDER` (`draft`/`filled`/
  `finished`) — matching §6's backend change — plus a "Reopen" affordance
  back to `draft`. Remove the publisher/date input rows entirely
  (`#state-dialog-publisher-row`/`#state-dialog-date-row`).
  Submitted/published/archived/rejected transitions no longer happen from
  this dialog.
- Each dashboard row's "Submitted" column
  ([dashboard.js:30-31](../../frontend/static/js/dashboard.js#L30-L31)) now
  reads `state`/`publisher_id` from the dashboard payload's per-row
  submission-status fields (populated server-side by §6's
  `_dashboard_row` change) instead of the dropped `row.publisher` field.
- Add a "Manage submission" link/button per row (visible once a puzzle is
  at least `finished`) that navigates to `/submissions/?puzzle={name}` —
  the dashboard's entry point into the new SPA (§8.2).

---

## 10. Migration of the existing database

Follows the rebuild-not-alter pattern already established by
[migrate_puzzle_state.py](../../tools/dev/migrate_puzzle_state.py) and
documented at
[puzzle_state.md §9](puzzle_state.md#9-one-off-migration-tool): the running
app never runs `ALTER TABLE`; a one-off tool reads the existing database
read-only and writes a **brand-new** file with the full target schema. This
is the *only* way an existing database gets the three new tables and loses
the three dropped columns.

New tool: `tools/dev/migrate_submissions.py`, sibling of
`migrate_puzzle_state.py`, same CLI contract and structure:

```
python3 tools/dev/migrate_submissions.py --new-dbfile PATH [--old-dbfile PATH] [--dry-run]
```

- `--new-dbfile` — destination, required, must not already exist (no
  `--force`, no overlay).
- `--old-dbfile` — source, defaults to the app's configured `dbfile`
  (`init_config()["dbfile"]`, same resolution as the existing tool).
- `--dry-run` — reports counts and writes nothing.

Plain `sqlite3` throughout; does not import `SQLitePersistenceAdapter` (same
convention as `migrate_puzzle_state.py`); does import the pure
`crossword.domain.publisher_code.derive_publisher_code` helper from §2 —
that one's dependency-free, so it doesn't violate the "no adapter import"
rule.

### 10.1 Schema

Defines, unconditionally in one pass (no `IF NOT EXISTS`, no probing):

- `puzzles` — **identical** to the source table's columns *except* dropping
  `publisher`, `date_submitted`, `date_published`. Unlike
  `migrate_puzzle_state.py` (which recomputes `state` from scratch because
  it's introducing the state columns for the first time), this migration
  runs on a database that **already has real `state` values**, including
  `submitted`/`published`/`archived` set by users through the existing
  dashboard. Those values are **copied as-is** — not recomputed — since
  they reflect real history, not something derivable from `jsonstr` alone.
- `publishers`, `editors`, `submission_events` — the §1 DDL, created empty
  and then populated by the row-copy step below.

### 10.2 Row copy procedure

1. Open `--old-dbfile` read-only (`file:...?mode=ro`), same as
   `migrate_puzzle_state.py`'s `open_readonly`.
2. Copy every real puzzle row (`puzzlename NOT NULL`, excluding `__wc__`/
   `__new__` working copies — same filter as the existing tool), preserving
   `id`, into the new `puzzles` table, **including its existing `state`**
   verbatim, but **excluding** the three dropped columns from the
   `INSERT`.
3. For every copied puzzle whose *old* row had a non-null, non-empty
   `publisher`:
   a. Collect the distinct set of such free-text values across the whole
      database first (a single pass), and run
      `derive_publisher_code` over them to build a `{free_text: code}`
      map, inserting one `publishers` row per distinct code (`name` set to
      the original free-text value — the user can rename it later via
      `PublisherUseCases.update_publisher`; `email`/`submission_limits`/
      `payment_info`/`spec_url` left `NULL`).
   b. For each such puzzle, synthesize one `submission_events` row:
      `event_type = 'submitted'`, `resulting_state = 'submitted'`,
      `publisher_id` = the mapped code, `timestamp` = the old row's
      `date_submitted` if set, else its `modified` timestamp (§4.3.2).
   c. If the old row also had a non-null `date_published`, synthesize a
      second event: `event_type = 'accepted'`, `resulting_state =
      'published'`, same `publisher_id`, `timestamp = date_published`.
   d. If the old row's `state` was `'archived'`, synthesize a third event
      after the above: `event_type = 'archived'`, `resulting_state =
      'archived'`, `timestamp` = the row's `modified` (no better signal
      available for when archiving happened).
4. Commit.

Because `puzzles.state` is copied verbatim, a puzzle with `state =
'submitted'` ends up with **both** the physical column value `'submitted'`
**and** a `submission_events` row deriving to `'submitted'`. This is
intentional, not a bug to fix: `get_current_submission_status` (§3) only
ever falls back to reading `puzzles.state` directly when a puzzle has *zero*
`submission_events` rows, and every puzzle handled by step 3 above has at
least one by construction — so the derived read path always finds the event
row first and the stale-looking column value is never actually consulted
for those puzzles. It's inert, not incorrect.

### 10.3 `--dry-run` output

Mirrors `clear_work_files.py`'s reporting style:

```
Real puzzles to copy: N
Distinct free-text publishers found: M
  <free-text value> -> <derived code>
  ...
Submission events to synthesize: K (submitted: a, accepted: b, archived: c)
```

### 10.4 Ordering relative to the puzzle-state migration

If a legacy database predates *both* features (no `state` column at all),
`migrate_puzzle_state.py` must run first — this tool's row-copy step assumes
`state`/`publisher`/`date_submitted`/`date_published` already exist on the
source `puzzles` table. Note this explicitly in the new tool's docstring, as
`migrate_puzzle_state.py`'s own docstring already documents its own
prerequisites.

### 10.5 Post-migration

Same as the existing tool: update `dbfile` in
`~/.config/crossword/config.yaml` (or rename the new file into place), then
restart the app. Recommend the user spot-check a handful of migrated
publishers/dates against the dashboard before deleting the old file.

---

## 11. Tests

All under `crossword/tests/`, pytest, following the existing fixture style
(`Mock()` persistence for use-case tests per
[test_puzzle_use_cases.py:14-20](../../crossword/tests/test_puzzle_use_cases.py#L14-L20),
a real `:memory:` `SQLitePersistenceAdapter` for adapter tests, and
`importlib.util.spec_from_file_location` to load the migration tool as a
module per
[test_migrate_puzzle_state.py:27-30](../../crossword/tests/test_migrate_puzzle_state.py#L27-L30)):

- **Domain** (`test_submission_event.py`): `ALL_EVENT_TYPES` membership;
  `RESULTING_STATE` mapping matches §4.4.3's table exactly, including
  `REJECTED -> ps.FINISHED`. `test_publisher_code.py`: short values pass
  through unchanged; long values reduce to 3 chars; collisions get a
  disambiguating suffix.
- **Adapter** (`test_sqlite_adapter.py` additions): CRUD for all three new
  tables; `delete_publisher` raises when referenced by an editor or an
  event, succeeds otherwise; `append_submission_event` raises when
  `editor_id` doesn't belong to `publisher_id`; `get_current_submission_status`
  over a synthetic event history — no events (falls back to `puzzles.state`),
  a single `submitted` event, a `rejected` event (state falls back to
  `finished`, but a *separate* test confirms the publisher-derivation query
  still returns that rejection's `publisher_id` even though its
  `resulting_state` isn't the "final" word — the two derivations are
  independent), and non-state-changing events (`comment`/`email_sent`)
  interleaved and correctly skipped. `set_puzzle_state`/`get_puzzle_state`/
  `list_puzzle_summaries` no longer reference the dropped columns.
- **Use case** (`test_publisher_use_cases.py`, `test_editor_use_cases.py`,
  `test_submission_use_cases.py`): each `SubmissionUseCases` event method
  logs the right `event_type`/`resulting_state`; `submit`/`reject`/`accept`
  reject a missing `publisher_id`; `comment` rejects an empty `body`; the
  editor/publisher mismatch check raises `ValueError` before touching
  persistence; `draft_submission_email` produces a body containing the
  puzzle title and, when given, the editor's name.
- **Integration** (`test_puzzle_use_cases.py` additions): `set_puzzle_state`
  rejects `submitted`/`published`/`archived`/anything not in
  `COMPLETION_LADDER`; `get_dashboard` reflects a freshly logged submission
  event immediately (Appendix A.8 — no caching).
- **HTTP** (`test_http_server.py` additions): happy path for every §7
  route; 400 on a bad publisher/editor id or missing required field; 404 on
  an unknown publisher/editor/puzzle; the narrowed `PUT
  /api/puzzles/{name}/state` 400s on `submitted`.
- **Migration** (`test_migrate_submissions.py`, mirroring
  `test_migrate_puzzle_state.py`): writes a fresh DB without touching the
  source; refuses an existing destination; `puzzles.state` is copied
  verbatim (not recomputed); dropped columns are actually absent from the
  new schema; free-text publishers correctly map to codes including a
  collision case; `submitted`/`accepted`/`archived` events are synthesized
  correctly from `date_submitted`/`date_published`/`state='archived'`;
  `--dry-run` writes nothing.

---

## 12. Suggested implementation order

1. Domain: `submission_event.py`, `publisher_code.py` (+ tests) — §2.
2. Port: extend `PersistencePort` — §3.
3. Adapter: schema (§1) + all new/changed methods on
   `SQLitePersistenceAdapter` (+ tests) — §4.
4. Use cases: `PublisherUseCases`, `EditorUseCases`, `SubmissionUseCases`
   (+ tests), wired into `AppContainer` — §5.
5. Integration: narrow `PuzzleUseCases.set_puzzle_state`, rework
   `get_dashboard`/`_dashboard_row` (+ tests) — §6.
6. HTTP: `submission_handlers.py`, route registration, narrow the existing
   state route (+ tests) — §7.
7. Migration tool: `tools/dev/migrate_submissions.py` (+ tests) — §10. Can
   happen any time after step 3 (schema is defined), but do it before
   relying on it against a real production copy.
8. Frontend: submissions-editor SPA + minimal static-serving routes (§8),
   dashboard changes (§9). Manual smoke test in a browser per the project's
   golden-path testing convention.
9. Docs: regenerate `docs/dev/endpoints.md`
   (`tools/dev/gen_endpoints_doc.py`), update `tools/dev/swagger.py` and run
   `--check`, add a cross-reference note to `puzzle_state.md` that
   `publisher`/`date_submitted`/`date_published` were superseded by this
   feature.
10. Full `pytest crossword/tests/` pass before calling this done.
