# Plan: Theme Words

Allow the user to start a puzzle from a pool of theme words, select a working
set of 4, try placements in a grid, and commit the result as a new puzzle.

---

## Domain

### New model: `ThemeSet`

```
ThemeSet
  name: str
  words: list[str]          # full candidate pool
  selections: list[list[str]]  # saved 4-word attempts (history)
```

- Lives in `crossword/domain/theme_set.py`
- No grid reference — a theme set is independent until committed
- Word validation: alpha only, length 3–15, no duplicates

---

## Persistence

### New table: `theme_sets`

```sql
CREATE TABLE theme_sets (
    id          INTEGER PRIMARY KEY,
    userid      INTEGER,
    name        TEXT,
    created     TEXT,
    modified    TEXT,
    jsonstr     TEXT
);
```

- Add `load_theme_set` / `save_theme_set` / `delete_theme_set` / `list_theme_sets`
  to `SQLiteAdapter` and the persistence port interface.

---

## Use Cases

### New class: `ThemeUseCases`

| Method | Description |
|---|---|
| `create_theme_set(user_id, name, words)` | Validate and save a new pool |
| `update_theme_set(user_id, name, words)` | Replace pool words |
| `delete_theme_set(user_id, name)` | Delete pool |
| `list_theme_sets(user_id)` | List pool names |
| `select_theme_words(user_id, name, selected)` | Validate exactly 4 words, append to selections |
| `suggest_placements(user_id, grid_name, words)` | Return scored placement options |
| `commit_theme(user_id, grid_name, puzzle_name, placement)` | Create puzzle with theme words pre-placed |

---

## Placement Suggestion Algorithm

Given 4 words and a grid:

1. Find all valid positions for each word (empty rows/cols of sufficient length).
2. For each combination of 4 placements, check that crossing cells have matching
   letters (an ACROSS and DOWN that share a cell must agree on the letter).
3. Score valid combinations:
   - Symmetry of positions
   - Centrality (prefer center of grid)
   - Number of crossings among the 4 theme words themselves
   - Estimated fill quality (ratio of constrained remaining white cells)
4. Return top N placements as `[{word, seq, dir, row, col}, ...]` lists.

Brute-force with pruning is fine — only 4 words, bounded search space.

---

## HTTP Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/themes` | List theme set names |
| `POST` | `/api/themes` | Create theme set `{name, words}` |
| `GET` | `/api/themes/{name}` | Get theme set |
| `PUT` | `/api/themes/{name}` | Update pool words |
| `DELETE` | `/api/themes/{name}` | Delete theme set |
| `POST` | `/api/themes/{name}/suggest` | `{grid, words[4]}` → placement options |
| `POST` | `/api/themes/{name}/commit` | `{grid, puzzle_name, placement}` → new puzzle |

---

## Frontend

### New UI flow

1. **Theme pool panel** — new menu item under Puzzle > New from Theme
   - Textarea/tag input to enter pool words
   - Save as named theme set (reuse name-prompt modal)

2. **Select 4 words** — checklist from pool, enforces exactly 4

3. **Suggest placements** — fetch `POST /api/themes/{name}/suggest`
   - Show SVG previews of top placements (reuse preview chooser pattern)
   - Each preview shows the 4 theme words highlighted in the grid

4. **Swap a word** — uncheck one word, pick replacement from pool, re-suggest

5. **Commit** — calls `POST /api/themes/{name}/commit`
   - Opens resulting puzzle in the puzzle editor (same flow as New Puzzle)

### Menu state

Theme flow runs as a sub-flow of `home` state — no new top-level editor state
needed. The commit step transitions normally into `puzzle-editor`.

---

## What's New vs. Reused

| New | Reused |
|---|---|
| `ThemeSet` domain model | Preview chooser (`showPreviewChooser`) |
| `theme_sets` DB table | Puzzle creation flow (`do_puzzle_new`) |
| `ThemeUseCases` | SVG rendering |
| Placement suggestion algorithm | Name-prompt modal |
| Theme pool / select / suggest UI | Undo/redo on resulting puzzle |

---

## Implementation Order

1. `ThemeSet` domain model + validation
2. Persistence: table + `SQLiteAdapter` methods + port interface
3. `ThemeUseCases`: CRUD methods (no suggestion yet)
4. HTTP handlers + routes for CRUD endpoints
5. Placement suggestion algorithm + `/suggest` endpoint
6. `/commit` endpoint (thin wrapper over existing puzzle creation)
7. Frontend: pool management UI
8. Frontend: select + suggest + swap flow
9. Frontend: commit → open puzzle editor
