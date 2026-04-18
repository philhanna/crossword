# Frontend–Server Contact Points

All HTTP interactions go through `apiFetch(method, path, body?)` at [app.js:59](frontend/static/js/app.js#L59),
which JSON-encodes the body and JSON-parses the response.
The export download uses a raw `fetch()` to stream a blob.

---

## Puzzles

| Method | Path | Triggered by | Notes |
|--------|------|--------------|-------|
| `GET` | `/api/puzzles` | `do_puzzle_open`, `do_puzzle_delete`, `do_export` (from home) | List all puzzle names |
| `POST` | `/api/puzzles` | `do_puzzle_new` | Body: `{name, size}`. Creates new puzzle |
| `POST` | `/api/puzzles/{name}/open` | `_openPuzzleInEditor` | Creates working copy; returns `{working_name}` |
| `GET` | `/api/puzzles/{name}` | `_openPuzzleInEditor`, `do_puzzle_title` (refresh) | Fetch full puzzle data |
| `POST` | `/api/puzzles/{wn}/copy` | `do_puzzle_save`, `_savePuzzleAsName` | Body: `{new_name}`. Save/Save-As |
| `POST` | `/api/puzzles/{name}/rename` | `do_puzzle_rename` | Body: `{new_name}`. Rename puzzle in place |
| `PUT` | `/api/puzzles/{wn}/title` | `do_puzzle_title` | Body: `{title}` |
| `DELETE` | `/api/puzzles/{name}` | `_doPuzzleCloseConfirmed` (cleanup wc), `do_puzzle_delete` | Delete working copy on close, or named puzzle |
| `GET` | `/api/puzzles/{name}/preview` | `showPreviewChooser` | Returns `{name, heading, svgstr}`; fetched in parallel for all names |
| `GET` | `/api/puzzles/{wn}/stats` | `do_puzzle_stats`, `_refreshPuzzleStatsIfVisible` | Puzzle statistics |
| `GET` | `/api/puzzles/{wn}/fill-order` | `do_puzzle_fill_order` | Fill priority order for unfilled words |

---

## Puzzle — Words

| Method | Path | Triggered by | Notes |
|--------|------|--------------|-------|
| `GET` | `/api/puzzles/{wn}/words/{seq}/{dir}` | `openWordEditor` | Fetch word data for editing |
| `PUT` | `/api/puzzles/{wn}/words/{seq}/{dir}` | `doWordEditOK`, `_peCommitWord` | Body: `{text?, clue?}`. Save answer and/or clue; returns full puzzle data |
| `GET` | `/api/puzzles/{wn}/words/{seq}/{dir}/constraints` | `doShowConstraints` | Crosser constraint table |
| `GET` | `/api/puzzles/{wn}/words/{seq}/{dir}/suggestions?pattern=` | `_fetchConstrainedSuggestions` | Constrained word suggestions (respects crossing letters) |

---

## Puzzle — Grid editing

| Method | Path | Triggered by | Notes |
|--------|------|--------------|-------|
| `PUT` | `/api/puzzles/{wn}/grid/cells/{r}/{c}` | `handleGridModeClick` | Toggle cell black/white |
| `POST` | `/api/puzzles/{wn}/grid/rotate` | `do_puzzle_rotate_grid` | Rotate grid 90° |
| `POST` | `/api/puzzles/{wn}/grid/generate` | `do_puzzle_generate_grid` | Auto-fill grid using fill-priority algorithm |
| `POST` | `/api/puzzles/{wn}/grid/undo` | `do_puzzle_undo` (grid mode) | Undo last grid change |
| `POST` | `/api/puzzles/{wn}/grid/redo` | `do_puzzle_redo` (grid mode) | Redo last grid change |
| `POST` | `/api/puzzles/{wn}/undo` | `do_puzzle_undo` (puzzle mode) | Undo last puzzle-text change |
| `POST` | `/api/puzzles/{wn}/redo` | `do_puzzle_redo` (puzzle mode) | Redo last puzzle-text change |

---

## Puzzle — Mode switching

| Method | Path | Triggered by | Notes |
|--------|------|--------------|-------|
| `POST` | `/api/puzzles/{wn}/mode/grid` | `do_switch_to_grid_mode` | Switch working copy to grid-edit mode |
| `POST` | `/api/puzzles/{wn}/mode/puzzle` | `do_switch_to_puzzle_mode` | Switch back to puzzle mode; recomputes entries |

---

## Words (dictionary)

| Method | Path | Triggered by | Notes |
|--------|------|--------------|-------|
| `GET` | `/api/words/suggestions?pattern=` | `_fetchPatternSuggestions` | Unconstrained pattern-based word list |
| `GET` | `/api/words/{word}/definitions` | `doWordDefinitions` | Dictionary definitions for a word (toggle show/hide in word editor) |

---

## Import

| Method | Path | Triggered by | Notes |
|--------|------|--------------|-------|
| `POST` | `/api/import/acrosslite` | `do_puzzle_import` | Body: `{name, content}`. Imports AcrossLite `.txt` file content |

---

## Export

| Method | Path | Triggered by | Notes |
|--------|------|--------------|-------|
| `GET` | `/api/export/puzzles/{name}/acrosslite` | `_downloadExport('puz')` | Raw `fetch()`; response streamed as blob download |
| `GET` | `/api/export/puzzles/{name}/xml` | `_downloadExport('xml')` | Raw `fetch()`; Crossword Compiler XML |
| `GET` | `/api/export/puzzles/{name}/nytimes` | `_downloadExport('nyt')` | Raw `fetch()`; NYT PDF |
| `GET` | `/api/export/puzzles/{name}/solver-pdf` | `_downloadExport('solver')` | Raw `fetch()`; Solver PDF |
| `GET` | `/api/export/puzzles/{name}/json` | — | JSON export; not yet wired to frontend |
