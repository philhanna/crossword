# Restructuring Implementation Plan

Implementation plan for
[restructured_crossword_composer_requirements.md](restructured_crossword_composer_requirements.md).
Phases are ordered bottom-up through the hexagonal layers (domain → ports →
adapters → use cases → HTTP → frontend), and the submissions editor (§4) goes
first because every decision in that section is already resolved, whereas the
theme editor (§2) has an open Phase 2 (automation) and the composing editor
items (§3) are independent, lower-priority enhancements. Nothing here is
executed by this plan — it is a checklist for later work.

## Contents

- [Phase 0 — Groundwork](#phase-0--groundwork)
- [Phase 1 — Database migration](#phase-1--database-migration)
- [Phase 2 — Submissions editor backend](#phase-2--submissions-editor-backend-4)
- [Phase 3 — Theme editor backend](#phase-3--theme-editor-backend-2)
- [Phase 4 — Composing editor enhancements](#phase-4--composing-editor-enhancements-3)
- [Phase 5 — Dashboard updates](#phase-5--dashboard-updates-1)
- [Phase 6 — Frontend restructuring into four SPAs](#phase-6--frontend-restructuring-into-four-spas)
- [Phase 7 — Documentation & cleanup](#phase-7--documentation--cleanup)
- [Phase 8 — Deferred ML projects](#phase-8--deferred-ml-projects-out-of-scope-for-this-restructuring)

---

## Phase 0 — Groundwork

Shared infrastructure that both the theme editor and the frontend split
depend on, done first so later phases don't have to retrofit it.

- [ ] Extract the existing preview-chooser code out of
  `frontend/static/js/dashboard.js`/`puzzle-editor.js` into a standalone,
  framework-free module `frontend/shared/grid_picker.js` (Appendix A.1). No
  backend change needed — `/api/grids/{name}/preview` is already generic.
- [ ] Define the shared module's public interface (open picker, return
  selected grid, accept an optional filter callback) so the theme editor
  (§2.3 — filter by `word_lengths` + fillability pre-check) can layer
  domain-specific behavior on top without modifying the shared component.
- [ ] Decide and document the new top-level `frontend/` layout for the
  eventual four-SPA split (used starting Phase 6, designed now so Phase 0's
  extraction lands in the right place):
  ```
  frontend/
    shared/            grid_picker.js, svg.js, common CSS
    dashboard/          index.html, dashboard.js
    theme-editor/        index.html, theme-editor.js
    composing-editor/    index.html, puzzle-editor.js, word-editor.js, state.js, ui.js, settings.js
    submissions-editor/  index.html, submissions.js
  ```
- [ ] Update `crossword/http_server/static_handlers.py` to serve each app's
  `index.html` from its own path prefix (e.g. `/`, `/themes/`,
  `/compose/`, `/submissions/`) and its static assets from the matching
  subdirectory, instead of the single `frontend/index.html`/`static/` pair.
  Keep this change additive — don't break the existing single-SPA routes
  until Phase 6 actually moves the JS files.
- [ ] Add a placeholder section to `docs/dev/endpoints.md` for the new route
  groups (`/api/themes`, `/api/publishers`, `/api/editors`,
  `/api/submission-events`) so Phase 2/3 additions have somewhere to land
  incrementally.

---

## Phase 1 — Database migration

Follows the rebuild-not-alter pattern already used for the puzzle-state
migration
([puzzle_state.md §9](puzzle_state.md#9-one-off-migration-tool),
[migrate_puzzle_state.py](../../tools/dev/migrate_puzzle_state.py)): the
running app never runs `ALTER TABLE`; a one-off tool reads the old DB
read-only and writes a fresh file with the target schema.

### 1.1 Target schema additions

- [ ] `themes` table (new) — one row per theme (§2.1):
  `id INTEGER PK`, `userid INTEGER NOT NULL`, `name TEXT NOT NULL`,
  `created TEXT`, `modified TEXT`, `jsonstr TEXT NOT NULL` (holding
  `word_lengths`, `candidate_words`, `selected_words`, `alternate_words`,
  `grid` as a JSON blob, mirroring how `puzzles.jsonstr` already holds a
  serialized `Puzzle`). Unique index on `(userid, name)`, same shape as
  `idx_puzzles_userid_puzzlename`. No `theme_id` ever appears on `puzzles`
  (Appendix A.13) — confirm no FK is added in either direction.
- [ ] `publishers` table (new, §4.3.2): `id TEXT PK` (3-char code), `name`,
  `email`, `submission_limits` TEXT, `payment_info` TEXT, `spec_url`. No
  `user_id` — global reference data (Appendix A.7).
- [ ] `editors` table (new, §4.3.3): `id INTEGER PK`, `publisher_id TEXT FK
  → publishers.id`, `name`, `email`. No `user_id` (Appendix A.7).
- [ ] `submission_events` table (new, §4.3.1): `id INTEGER PK`, `puzzle_id
  INTEGER FK → puzzles.id`, `timestamp TEXT`, `event_type TEXT CHECK (...)`
  closed to the 7 values in Appendix A.2, `resulting_state TEXT` nullable
  with `CHECK` against `puzzles.state`'s existing enum, `publisher_id TEXT
  FK → publishers.id` nullable, `editor_id INTEGER FK → editors.id`
  nullable, `body TEXT`. Index on `puzzle_id` (every status/history read
  filters by it).
- [ ] Drop `publisher`, `date_submitted`, `date_published` from `puzzles`
  (§4.5 decision 1) — these become derived, not stored.
- [ ] Write the new `CREATE TABLE` statements into
  `SQLitePersistenceAdapter._ensure_schema_compatibility()` (or a sibling
  method per new adapter — see Phase 2.2/3.2) so every fresh database the
  app creates already has the right shape, matching the existing pattern
  where schema lives in code, not migration files.

### 1.2 One-off migration tool

- [ ] `tools/dev/migrate_submissions.py`, sibling of
  `migrate_puzzle_state.py`. Same contract: `--old-dbfile`, `--new-dbfile`
  (required, must not exist), `--dry-run`. Plain `sqlite3`, no
  `SQLitePersistenceAdapter` import, schema defined once unconditionally.
- [ ] Procedure: copy `puzzles` rows as-is except the three dropped columns;
  create `themes` (empty — nothing to backfill), `publishers`, `editors`,
  `submission_events` tables; for every existing puzzle row with a non-null
  free-text `publisher`, create-or-match a `publishers.id` code (prompt
  for/derive a 3-char code from the existing free-text values seen in the
  data) and synthesize one `submitted` event carrying that `publisher_id`,
  using `date_submitted` as the event `timestamp` if present, else
  `modified` (§4.3.2). If `date_published` is also set, synthesize a
  second `accepted` event after it.
- [ ] `--dry-run` reports: rows to copy, distinct free-text publisher
  values found and the codes they'll map to, count of synthesized events,
  like `clear_work_files.py`'s reporting style.
- [ ] Note in the tool's docstring that it should run *after*
  `migrate_puzzle_state.py` if both are ever needed on the same legacy DB
  (this tool assumes the state columns already exist on `puzzles`).

### 1.3 Tests

- [ ] `crossword/tests/` (pytest): migration tool writes a fresh DB without
  touching the source; refuses an existing destination; correctly
  drops the three columns; correctly maps free-text publishers to codes
  and synthesizes events; `--dry-run` writes nothing.
- [ ] Adapter-level schema tests: new tables created on a fresh `:memory:`
  DB; `puzzles` no longer has `publisher`/`date_submitted`/`date_published`
  columns.

---

## Phase 2 — Submissions editor backend (§4)

All decisions here are resolved (§4.5, Appendix A.2–A.8), so this is the
most mechanical phase — build it first.

### 2.1 Domain

- [ ] `crossword/domain/submission_event.py`: the closed `event_type` enum
  (`SUBMITTED`, `EMAIL_SENT`, `EMAIL_RECEIVED`, `ACCEPTED`, `REJECTED`,
  `ARCHIVED`, `COMMENT` — Appendix A.2) and the `event_type →
  resulting_state` mapping table from §4.4.3, mirroring how
  `crossword/domain/puzzle_state.py` holds the puzzle-state enum.
- [ ] Markdown ⇄ HTML conversion helpers for email drafting (§4.4.4,
  decision 5) — pick a small dependency-free approach or a single
  lightweight library; lives in `crossword/domain/` or a new
  `crossword/adapters/markdown_adapter.py` if it needs a third-party lib
  (keeps the dependency at the adapter boundary per the hexagonal rule).

### 2.2 Ports & adapter

- [ ] Extend `crossword/ports/persistence_port.py` (or add a sibling
  `submission_port.py` — prefer extending the existing port, since
  submissions/publishers/editors share the same SQLite connection and
  transaction boundary as puzzles) with:
  - `create_publisher` / `update_publisher` / `delete_publisher` /
    `get_publisher` / `list_publishers`
  - `create_editor` / `update_editor` / `delete_editor` / `list_editors`
  - `append_submission_event(puzzle_id, event_type, resulting_state,
    publisher_id=None, editor_id=None, body=None, timestamp=None)`
  - `get_submission_history(puzzle_id) -> list[dict]`
  - `get_current_submission_status(puzzle_id) -> dict | None` — most
    recent event with non-`NULL` `resulting_state` (Appendix A.6)
  - `get_current_publisher(puzzle_id) -> str | None` — most recent event
    with non-`NULL` `publisher_id` (Appendix A.6)
- [ ] Implement all of the above on `SQLitePersistenceAdapter`, reusing the
  schema from Phase 1.1. Delete guards: `delete_publisher` raises
  `PersistenceError` if referenced by `editors` or `submission_events`
  (Appendix A.4); enforce in SQL with a `SELECT EXISTS` check before the
  `DELETE`, consistent with the adapter's existing error-handling style.
  Referential check (§4.4.5): `append_submission_event` raises if
  `editor_id` is set but doesn't belong to `publisher_id`.

### 2.3 Use cases

- [ ] `crossword/use_cases/publisher_use_cases.py` — `PublisherUseCases`:
  create/update/delete/list/lookup, plus the one-off migration helper
  logic factored out so `tools/dev/migrate_submissions.py` (Phase 1.2) and
  any future re-run share one code path (§4.4.1).
- [ ] `crossword/use_cases/editor_use_cases.py` — `EditorUseCases`:
  create/update/delete under a publisher (§4.4.2).
- [ ] `crossword/use_cases/submission_use_cases.py` — `SubmissionUseCases`:
  one method per event type from the §4.4.3 table (`submit`, `reject`,
  `accept`, `log_email_sent`, `log_email_received`, `archive`, `comment`),
  each calling `append_submission_event` with the right
  `resulting_state`; `get_submission_history`; `get_current_status` (pulls
  status + publisher together for the dashboard, §4.2/A.8); enum
  validation per §4.4.5.
- [ ] Email drafting use cases (§4.4.4) on `SubmissionUseCases` or a small
  `EmailDraftUseCases`: draft body from a publisher's
  `submission_limits`/contact info; Markdown→HTML+plain for "Copy for
  Gmail" (the actual `ClipboardItem` write is frontend-only, Phase 6); HTML→
  Markdown for pasted-in replies before saving as `email_received.body`.
- [ ] Wire all three new use-case groups into
  `crossword/wiring/__init__.py`'s `AppContainer`/`make_app()`, alongside
  the existing `puzzle_uc`/`word_uc`.

### 2.4 HTTP layer

- [ ] `crossword/http_server/submission_handlers.py` (new file, sibling of
  `puzzle_handlers.py`): routes for publishers (`/api/publishers`,
  `/api/publishers/{id}`), editors (`/api/publishers/{id}/editors`,
  `/api/editors/{id}`), and submission events
  (`/api/puzzles/{name}/submission-events`,
  `/api/puzzles/{name}/submission-status`,
  `/api/puzzles/{name}/submission-events/draft-email`).
- [ ] Register routes in `crossword/http_server/server.py`'s router, same
  pattern as the existing `puzzle_handlers`/`word_handlers` registration.
- [ ] 400 on invalid `event_type`/mismatched `editor_id`/`publisher_id`,
  404 on unknown publisher/editor/puzzle, consistent with existing handler
  error conventions.

### 2.5 Tests

- [ ] Domain: enum validation, `resulting_state` mapping.
- [ ] Adapter: CRUD for all three new tables; delete guard on publishers;
  derivation queries (`get_current_submission_status`,
  `get_current_publisher`) over a synthetic event history including a
  rejection (falls back to `finished`, §4.2) and non-state-changing events
  interleaved (`comment`/`email_sent` skipped correctly).
  - [ ] Note: rejection currently maps the publisher-derivation query
    differently from the status-derivation query (the publisher lookup
    ignores `resulting_state`); add a test where the most recent
    publisher-bearing event is a `rejected` row to lock in that the two
    derivations are independent.
- [ ] Use case: each `SubmissionUseCases` method logs the right event +
  `resulting_state`; referential check rejects an editor that belongs to a
  different publisher; email drafting round-trips Markdown↔HTML for a
  representative sample (bold/italic/links/lists).
- [ ] HTTP: happy path for every new route; validation errors return the
  right status codes.

---

## Phase 3 — Theme editor backend (§2)

Phase 1 (manual functionality) only — Phase 2 (automation, §2.4) is
explicitly future work and out of scope here (it has its own design doc to
write later).

### 3.1 Domain

- [ ] `crossword/domain/theme.py` — `Theme` class: `id`, `name`,
  `word_lengths`, `candidate_words`, `selected_words`, `alternate_words`,
  `grid` (reuses the existing `Grid` domain object). `to_json()`/
  `from_json()` mirroring `Puzzle`'s pattern, for the `themes.jsonstr`
  column.
- [ ] `is_complete()` method (Appendix A.12): `grid is not None and
  len(selected_words) == len(word_lengths)` — computed, never stored, same
  spirit as `Puzzle.is_filled()`/`all_clues_complete()` in
  `puzzle_state.py`.
- [ ] Permutation helper for §2.3's "reorder theme words across the grid's
  symmetric slots" — every permutation of `selected_words` whose lengths
  still match `word_lengths`'s symmetric slot order.

### 3.2 Ports & adapter

- [ ] Extend `PersistencePort` (or it may be cleanest to keep themes on the
  same port as puzzles, given the identical CRUD shape) with
  `create_theme`/`load_theme`/`save_theme`/`delete_theme`/`rename_theme`/
  `list_themes`/`list_theme_summaries`, paralleling the existing
  puzzle methods 1:1 (`copy_puzzle` → `copy_theme` for save-as,
  `rename_puzzle` → `rename_theme` preserving `id`, Appendix A.9).
- [ ] Implement on `SQLitePersistenceAdapter` against the `themes` table
  from Phase 1.1. No in-use check on delete (Appendix A.13) — simpler than
  the publisher delete guard.

### 3.3 Use cases

- [ ] `crossword/use_cases/theme_use_cases.py` — `ThemeUseCases`:
  - CRUD: create/open/delete/save/save-as/rename (id-preserving)
  - Attribute edits: set `word_lengths`; add/delete/edit words in
    `candidate_words`/`alternate_words`; move words between the two
  - Validation: delegate to `WordUseCases.validate_word` for each
    candidate/alternate word
  - `is_complete` passthrough to the domain method
  - Grid selection/evaluation (§2.3): find grids whose slot structure
    matches `word_lengths` (likely a new query method on the grid side,
    or filtering `list_puzzles`/a grids table — confirm where grids
    actually live once Phase 0 groundwork on the shared picker is done,
    since grids and puzzles share one table distinguished by
    `last_mode`); initial-fillability check reusing
    `PuzzleUseCases.get_fill_order`'s underlying logic (factor the
    constraint-checking core out of `get_fill_order` if it isn't already
    separable, so both editors call the same code); reorder via the
    Phase 3.1 permutation helper + re-check; substitute
    `alternate_words` ↔ `selected_words` + re-check.
  - `list_themes`/`list_theme_summaries` (for this editor's own chooser)
    and a `list_complete_themes` filtered view (for §3.1's picker).
- [ ] Wire `ThemeUseCases` into `AppContainer`/`make_app()`.

### 3.4 HTTP layer

- [ ] `crossword/http_server/theme_handlers.py` (new file): CRUD routes
  under `/api/themes`, word-list editing sub-routes
  (`/api/themes/{name}/candidate-words`, `/.../alternate-words`), and grid
  evaluation routes (`/api/themes/{name}/grid-candidates`,
  `/api/themes/{name}/fit-check`) — exact shapes informed by whatever the
  shared grid-picker component (Phase 0) needs to call.
- [ ] Register in `server.py`'s router.

### 3.5 Tests

- [ ] Domain: `is_complete()` across empty/partial/complete themes;
  permutation helper only returns length-valid orderings.
- [ ] Adapter: CRUD, rename preserves `id`, no delete guard.
- [ ] Use case: word-list moves/edits; validation delegates correctly;
  fillability check flags an unfillable placement; substitution and
  reordering both produce a fillability re-check.
- [ ] HTTP: happy path + validation errors for all new routes.

---

## Phase 4 — Composing editor enhancements (§3)

Per Appendix A.11, there's no shared phase plan across editors — each item
below ships independently and in any order. Listed in requirements order;
non-ML items are the practical priority since the ML-tagged items are
substantial separate efforts (see [Phase 8](#phase-8--deferred-ml-projects-out-of-scope-for-this-restructuring)).

### 4.1 Create puzzle from theme (§3.1)

- [ ] `PuzzleUseCases.create_puzzle_from_theme(user_id, theme_name,
  new_puzzle_name)`: load the theme, copy `grid` + `selected_words` into a
  new `Puzzle` in puzzle mode, lock the theme words, save with `state =
  draft` (no `theme_id` stored back, Appendix A.13).
- [ ] `ThemeUseCases.list_complete_themes` (built in Phase 3.3) backs the
  new theme-picker endpoint.
- [ ] HTTP route `POST /api/puzzles/from-theme` in `puzzle_handlers.py`.
- [ ] Confirm the existing non-themed "new puzzle" path
  (`create_puzzle`/`switch_to_grid_mode`/`switch_to_puzzle_mode`) is
  unchanged and now shares the grid-picker component from Phase 0.
- [ ] Tests: theme→puzzle copy carries grid+words+locks correctly; puzzle
  has no reference back to the theme; dashboard shows it in draft mode.

### 4.2 Word editor regex (§3.2)

- [ ] Extend `WordUseCases._pattern_to_regex`/`get_word_constraints`/
  `get_ranked_suggestions` (`word_use_cases.py:75,167,224`) to accept full
  regex syntax (e.g. `MA[^AEIOU]`) instead of just `.`, while "Suggest"
  still filters candidates to the word's exact length.
- [ ] Tests: bracket-expression patterns match/reject correctly; length
  filtering still applies on top of the regex.

### 4.3 Fill Order improvements (§3.3) — non-ML subset

- [ ] Correctness/speed fixes to `PuzzleUseCases.get_fill_order`
  (`puzzle_use_cases.py:573`).
- [ ] Refined ranking: most-constrained-first, critical-bridge detection,
  suitability (depends on Phase 4.4's scored word list, so sequence
  suitability ranking after that lands).
- [ ] Caching with an invalidation rule (granularity TBD — start at
  per-puzzle, matching the existing `_invalidate_fill_order` hook at
  `puzzle_use_cases.py:60`); background pre-fill thread on word change.
- [ ] Auto-fill over a user-selected area; cycling alternatives like the
  existing grid-generate button.
- [ ] Tests: ranking order on known fixtures; cache invalidates on the
  right writes and not others.

### 4.4 Word list improvements (§3.4) — non-ML subset

- [ ] Switch `FlatFileWordListAdapter` (or add a new
  `ScoredWordListAdapter`) from plain text to CSV with a score column.
- [ ] Score-threshold filtering option on suggestions; sort by length,
  score, then word.
- [ ] Split compound entries into individual words (e.g. "ABETTERPLACE" →
  "A"/"BETTER"/"PLACE") as a word-list preprocessing step.
- [ ] Tests: CSV loads correctly; threshold filtering; sort order; split
  logic on known compounds.

---

## Phase 5 — Dashboard updates (§1)

Depends on Phase 2 (submission status derivation) and Phase 3 (themes
list), so it lands after both backends exist.

- [ ] `PuzzleUseCases.get_dashboard`/`_dashboard_row`
  (`puzzle_use_cases.py:611,627`): drop the "Archived" card; source
  submission-derived rows from `SubmissionUseCases.get_current_status`
  instead of reading `puzzles.state`/`publisher` directly (now that those
  columns are gone per Phase 1).
- [ ] New "Themes" card, leftmost, backed by `ThemeUseCases.list_themes`.
- [ ] Tests: dashboard reflects a freshly logged submission event
  immediately (Appendix A.8 — no caching/staleness); Archived card is
  gone; Themes card lists themes correctly.

---

## Phase 6 — Frontend restructuring into four SPAs

The biggest single change: one SPA becomes four, sharing backend/DB
(decision 3, §4.5) and the Phase 0 `grid_picker.js` asset (Appendix A.1),
but otherwise independent — no cross-frame signaling, no shared
navigation/modal stack.

### 6.1 Dashboard SPA

- [ ] Move `frontend/index.html` + `dashboard.js` into
  `frontend/dashboard/`. Replace the existing "Archived" card removal and
  add the "Themes" card (Phase 5) linking to `/themes/`.
- [ ] Convert the puzzle-related dashboard cards' links to the composing
  editor at `/compose/` and any submission-status card to link through to
  `/submissions/`.

### 6.2 Composing editor SPA

- [ ] Move `puzzle-editor.js`, `word-editor.js`, `state.js`, `ui.js`,
  `settings.js`, `svg.js` into `frontend/composing-editor/`, dropping the
  `home` menu-state (dashboard now lives in its own app) — keep
  `grid-editor`/`puzzle-editor` as the two states.
- [ ] Wire the "new puzzle" flow to the theme picker (§3.1) when the user
  chooses a themed puzzle, using the shared `grid_picker.js` for the
  non-themed path.
- [ ] Apply the word-editor regex UI change (§3.2) and any fill-order UI
  additions (auto-fill area selection, heat map if built in Phase 4.3).

### 6.3 Theme editor SPA (new)

- [ ] `frontend/theme-editor/index.html` + `theme-editor.js`: theme CRUD,
  attribute editing (`word_lengths`, candidate/selected/alternate word
  lists with move-between-lists UI), validation against the word-list API,
  and grid selection/evaluation built on the shared `grid_picker.js` with
  a theme-specific filter (matches `word_lengths`, fillability pre-check)
  and the reorder/substitute/reselect actions from §2.3.
- [ ] Save/Save-As/Rename/Delete following the existing puzzle editor's
  auto-persist working-copy pattern (consistent UX across editors).

### 6.4 Submissions editor SPA (new)

- [ ] `frontend/submissions-editor/index.html` + `submissions.js`:
  publisher/editor management screens; per-puzzle audit timeline (renders
  `get_submission_history`); action buttons for each event type
  (Submit/Reject/Accept/Log email sent/received/Archive/Comment).
- [ ] Email drafting UI: compose Markdown body from publisher
  requirements; "Copy for Gmail" button using `ClipboardItem` to write
  both `text/html` and `text/plain` (§4.4.4/decision 5); a paste-in box
  for incoming replies that runs client-side HTML→Markdown before posting
  as an `email_received` event.
- [ ] No "send" button anywhere in this UI — drafting only (decision 4).

### 6.5 Cross-cutting frontend work

- [ ] Update `crossword/http_server/static_handlers.py` routing (started
  in Phase 0) to actually serve the four new directories once the JS
  files have moved.
- [ ] Confirm `frontend.wiki`/screenshots or any hard-coded `/static/...`
  paths elsewhere in the repo are updated.
- [ ] Manual smoke test of all four apps end-to-end (per the project's
  "test the golden path in a browser" convention) before calling this
  phase done.

---

## Phase 7 — Documentation & cleanup

- [ ] Regenerate `docs/dev/endpoints.md` (there's a generator —
  `tools/dev/gen_endpoints_doc.py` — confirm it picks up the new handler
  modules, or extend it if it only scans specific files).
- [ ] Update the Swagger spec used by `tools/dev/swagger.py`; run
  `python3 tools/dev/swagger.py --check` to confirm no route gaps remain.
- [ ] Update `docs/dev/puzzle_state.md` to note that `publisher`/
  `date_submitted`/`date_published` were removed from `puzzles` in this
  restructuring and superseded by `submission_events` (cross-reference
  rather than duplicate content).
- [ ] Full `pytest crossword/tests/` pass.
- [ ] Update the wiki (`crossword.wiki`) overview page to describe the
  four-SPA structure if it currently documents the single-SPA layout.

---

## Phase 8 — Deferred ML projects (out of scope for this restructuring)

Tracked here so they aren't lost, but explicitly not part of this
restructuring effort (Appendix A.11 — no global phase plan ties them to
anything else):

- [ ] Probability-based fill-order predictor (§3.3) + training-set capture
  from uncompleted words on "Fill Order" clicks
- [ ] Suitability scoring model for the word list (§3.4), beyond the
  CSV-with-a-score-column mechanism built in Phase 4.4
- [ ] Per-publisher word lists / frequency models from the GXD database
  (§3.4)
- [ ] Publisher-fit predictor from word characteristics + theme type
  (§3.4)
- [ ] Part-of-speech classification for word-list entries (§3.4)
- [ ] ML clue-writing tool / publisher clue-style characterization (§3.3)
- [ ] Theme editor Phase 2 automation (§2.4) — needs its own design doc
  before implementation, per the linked automation notes and Cruciverb
  theme-type reference
