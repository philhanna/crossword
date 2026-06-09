# Dashboard — implementation plan

Implements [dashboard.md](dashboard.md): a new SPA **dashboard** view with a
four-card summary (top half) and a tabbed, full-width puzzle list (bottom half).

The lifecycle-state backend is already in place — `puzzle_state.py`,
`set_puzzle_state`/`get_puzzle_state`, the `state` column + filter on
`list_puzzles`, and the `GET`/`PUT /api/puzzles/<name>/state` routes (see
[puzzle_state.md](puzzle_state.md)). This plan adds **one read endpoint** for
batched dashboard data plus the **front-end** that consumes it.

## Resolved design decisions

1. **Data source** — a new batched endpoint `GET /api/dashboard` returns every
   real puzzle with all the metadata the view needs, in one round-trip.
2. **Fill %** — white cells containing a letter ÷ total white (non-black) cells.
3. **Navigation** — the dashboard *replaces* the current `home` welcome screen as
   the landing view; a nav button returns to it from the editor.
4. **State-change dialog** — collects a free-form **publisher** (required only
   for `submitted`, matching the backend) and a **date** field (defaulting to
   today) for `submitted`/`published`. Backend validation errors surface inline;
   the backend's date requirement is **not** relaxed.

---

## Part 1 — Backend

### 1.1 Domain — fill fraction (pure)

Add to [`Puzzle`](../../crossword/domain/puzzle.py), next to `is_filled()`:

```python
def fill_fraction(self) -> float:
    """Fraction (0.0–1.0) of white cells that contain a letter.

    White cells are all non-black cells; a cell is 'filled' when its value
    is neither WHITE (' ') nor BLACK ('*'). Returns 0.0 when there are no
    white cells.
    """
    white = [v for v in self.cells.values() if v != Puzzle.BLACK]
    if not white:
        return 0.0
    filled = sum(1 for v in white if v != Puzzle.WHITE)
    return filled / len(white)
```

The view shows `round(fill_fraction * 100)` as the percentage. Keeping the raw
fraction in the domain leaves rounding to the presentation layer.

> Reuses the existing `cells` map and `WHITE`/`BLACK` constants
> ([puzzle.py:11-12](../../crossword/domain/puzzle.py#L11-L12)). No new state.

### 1.2 Use case — `get_dashboard`

Add to [`PuzzleUseCases`](../../crossword/use_cases/puzzle_use_cases.py). It
walks every real puzzle once, loading each puzzle (which already carries its
state columns) and computing the per-row summary the dashboard needs.

```python
def get_dashboard(self, user_id: int) -> dict:
    """Return all real puzzles with the summary metadata the dashboard needs.

    Excludes working copies (__wc__ / __new__) and legacy NULL names — the
    same set list_puzzles already returns. One row per puzzle, sorted most
    recently modified first.

    Returns:
        {"puzzles": [ {name, title, state, publisher, date_submitted,
                       date_published, modified, size, word_count,
                       top_lengths: [{length, count}, ...],   # top 2 desc
                       fill_pct}  ... ]}
    """
```

Per-puzzle assembly (one helper, e.g. `_dashboard_row(user_id, name)`):

- `puzzle = self.persistence.load_puzzle(user_id, name)`
- `st = self.persistence.get_puzzle_state(user_id, name)` →
  `state`, `publisher`, `date_submitted`, `date_published`
- `size = puzzle.n`
- `word_count = puzzle.get_word_count()`
- `top_lengths`: from `puzzle.get_word_lengths()`, take the two largest lengths
  (`sorted(..., reverse=True)[:2]`), each `count = len(alist) + len(dlist)` —
  the same computation as
  [`get_puzzle_preview`](../../crossword/use_cases/puzzle_use_cases.py#L595-L600).
- `fill_pct = round(puzzle.fill_fraction() * 100)`
- `title = puzzle.title` (may be empty; the front end falls back to `name`)
- `modified`: see note below.

**`modified` timestamp.** `list_puzzles` returns only names and `load_puzzle`
doesn't expose `modified`. Add a thin persistence read so the use case stays out
of SQL:

```python
# PersistencePort + SQLitePersistenceAdapter
def list_puzzle_summaries(self, user_id: int) -> list[dict]:
    """[{name, modified, state, publisher, date_submitted, date_published}, ...]
    for real puzzles, ORDER BY modified DESC. Excludes working copies
    (puzzlename LIKE '__wc__%' / '__new__%') and legacy NULL names."""
```

`get_dashboard` then iterates these summary rows (giving order + `modified` +
state columns for free) and only loads the full `Puzzle` to compute
`size`/`word_count`/`top_lengths`/`fill_pct`. This avoids a second
`get_puzzle_state` round-trip per puzzle.

> One `SELECT puzzlename, modified, state, publisher, date_submitted,
> date_published FROM puzzles WHERE userid=? AND puzzlename IS NOT NULL ORDER BY
> modified DESC`, plus one `load_puzzle` per row. The full-`Puzzle` load is the
> cost; if it ever matters, `word_count`/`top_lengths`/`fill_pct` could later be
> denormalized onto the row, but start simple.

Working copies: `list_puzzle_summaries` excludes `__wc__%`/`__new__%` names (and
NULLs) directly in its `WHERE` clause, so the dashboard never shows transient
rows. This mirrors the visible set the choosers present.

### 1.3 HTTP — handler + route

Handler in
[puzzle_handlers.py](../../crossword/http_server/puzzle_handlers.py), following
the `handle_get_puzzle_state` shape (extract `user_id = current_user["id"]`,
call the use case, `request_handler._send_json(...)`):

```python
def handle_get_dashboard(path_params, query_params, body_params,
                         session_token, request_handler, app=None,
                         current_user=None, **kwargs):
    user_id = current_user["id"]
    data = app.puzzle_uc.get_dashboard(user_id)
    request_handler._send_json(data)
```

Route in [main.py](../../crossword/http_server/main.py), near the other
`/api/puzzles` routes:

```python
router.add_route("GET", r"^/api/dashboard$", handle_get_dashboard)
```

### 1.4 Docs

- Add `GET /api/dashboard` to [endpoints.md](endpoints.md) with the response
  shape above.
- Add the path + response schema to the Swagger spec used by
  `tools/dev/swagger.py`; verify with `python3 tools/swagger.py --check`.

### State transitions — already implemented

The dashboard's state-change dialog reuses the existing
`PUT /api/puzzles/<name>/state`
([handle_set_puzzle_state](../../crossword/http_server/puzzle_handlers.py#L289)),
which already validates state ∈ `ALL_STATES` and enforces publisher/date
requirements. **No backend change** is needed for transitions.

---

## Part 2 — Front-end

New file **`frontend/static/js/dashboard.js`**, loaded from
[index.html](../../frontend/index.html) before `puzzle-editor.js`. The dashboard
renders into the existing `#lhs`/`#rhs` workspace via a new `showView('dashboard')`
branch; `#rhs` stays empty (the dashboard is full-width — see CSS note).

**Layout.** The dashboard occupies the existing `<main id="workspace">` region,
i.e. it overlays the whole current main view **below** the
`<header class="app-bar">` ([index.html:18](../../frontend/index.html#L18)). The
app bar — logo, Puzzle/Import/Export menus, settings, Help — stays in place and
fully visible/usable; only the workspace content swaps to the dashboard. No part
of the dashboard renders over or replaces the header.

### 2.1 View wiring ([ui.js](../../frontend/static/js/ui.js))

- **Landing view:** the app currently boots into `home`. Change the initial
  `showView(...)` call (in the startup path) to `showView('dashboard')`, and
  point the post-close/`do_puzzle_close` return at `'dashboard'` instead of
  `'home'`.
- **`showView` switch** ([ui.js:416](../../frontend/static/js/ui.js#L416)): add
  a `case 'dashboard':` that calls `renderDashboard()` (clears `#rhs`, fills
  `#lhs`), and keep/repurpose `renderHome` or drop it. The `'home'` case can
  alias to the dashboard so existing callers don't break.
- **`updateMenu`** ([ui.js:383](../../frontend/static/js/ui.js#L383)): the
  current `home` checks gate New/Open/Import. Treat `dashboard` like the old
  `home` for menu enablement: `const onDashboard = AppState.view === 'dashboard'`
  enables New/Open/Import; editor-only items stay gated on `'editor'`.
- **Nav button:** add a Dashboard entry to the app bar so the user can return
  from the editor. Either a top-level `app-nav-btn` (`onclick="showView('dashboard')"`)
  or a Puzzle-menu item. A standalone button is simplest and always visible.

### 2.2 Data load

```js
async function renderDashboard() {
    const data = await apiFetch('GET', '/api/dashboard');   // {puzzles:[...]}
    DashboardState.puzzles = data.puzzles || [];
    document.getElementById('rhs').innerHTML = '';
    document.getElementById('lhs').innerHTML = dashboardHtml(DashboardState.puzzles);
    bindDashboardEvents();
}
```

Keep the fetched rows in a small module-level cache (`DashboardState.puzzles`)
so tab switching and the top cards render client-side without refetching. After
any state change, re-fetch and re-render.

### 2.3 Category → state mapping (top half)

| Card | Title | States included | Background |
|---|---|---|---|
| 1 | IN PROGRESS | `draft` | `#ffffcc` (w3-pale-yellow) |
| 2 | COMPLETED   | `filled`, `finished` | `#ddffdd` (w3-pale-green) |
| 3 | SUBMITTED   | `submitted`, `published` | `#ddffff` (w3-pale-blue) |
| 4 | ARCHIVED    | `archived` | `#f1f1f1` (w3-light-grey) |

Hex values extracted from w3.css per the spec (stylesheet **not** added to the
project). Define them as CSS classes (`.dash-card-1` … `.dash-card-4`) in
`style.css`.

**Card layout.** Title = `<b>NAME</b> (N)` where `N` is the **total** count of
puzzles in that category (not just the visible rows). Below the title, render the
**4 most-recently-modified** rows (the `puzzles` array is already `modified DESC`,
so filter by the card's states and `slice(0, 4)`). Overflow beyond 4 is reachable
via the bottom tabs — no "see more" link.

**Row content (all cards):**
- Puzzle **title** in bold, font smaller than the card title (`title || name`).
  Clicking it opens the **preview popup** (2.6).
- Line 2: `modified` as **mm/dd**, `size` as `n x n`, and the **top-two lengths**
  (e.g. `7-letter: 12, 6-letter: 18`) from `top_lengths`.

**Per-card extra:**
- **Card 1 (IN PROGRESS):** a progress widget flush-right on the title row, using
  the markup from the spec:
  ```html
  <div class="progress-wrap">
    <div class="progress-bar"><div class="progress-fill" style="width:NN%"></div></div>
    <div class="progress-text">NN% filled</div>
  </div>
  ```
  `progress-fill` is a rounded bar; track is light-grey, fill is green up to
  `fill_pct%` (CSS in 2.6).
- **Card 2 (COMPLETED):** the text **"fully clued"** flush-right **only** when the
  row's `state === 'finished'` (a `filled` row shows nothing extra).
- **Card 3 (SUBMITTED):** flush-right text —
  `"submitted to " + publisher` when `state === 'submitted'`, or
  `"published by " + publisher` when `state === 'published'`.
- **Card 4 (ARCHIVED):** no extra.

mm/dd helper: parse the ISO-ish `modified` string and format `MM/dd` (small JS
helper `fmtMonthDay(iso)`; guard against missing/blank).

### 2.4 Bottom half — tabbed list

Full-width card under the four cards. Tabs:
`draft · filled · finished · submitted · published · archived · all`.
Clicking a tab sets `DashboardState.activeTab` and re-renders the table from the
cached `puzzles` (no refetch). The `all` tab shows every puzzle.

**Columns by tab:**

| Tab | Columns |
|---|---|
| draft / filled / finished | State, Name, Title, Size, Words, Modified |
| submitted / published / all | State, **Publisher**, Name, Title, Size, Words, Modified |

- **State** column: a `<select>` dropdown of all six `ALL_STATES`, current state
  preselected. Changing it opens the **state-change dialog** (2.5) rather than
  applying immediately.
- **Name / Title** columns: clicking either opens the **preview popup** (2.6).
- **Size** = `n x n`; **Words** = `word_count`; **Modified** = **mm/dd** (same
  `fmtMonthDay(iso)` helper the cards use).
- Rows are a scrollable list (`max-height` + `overflow-y:auto` on the table body
  container).

### 2.5 State-change dialog

A new modal (the existing `#mb`/`#ib` are too constrained — `#ib` is a single
text input; this needs a select + two conditional fields). Add a dedicated
`#state-dialog` modal to [index.html](../../frontend/index.html) following the
existing `dialog-card`/`dialog-header`/`dialog-body` structure used by the other
modals, with fields:

- **Puzzle name:** read-only text (the row's name).
- **Current state:** read-only; if current state is `submitted`/`published`, also
  show its `publisher`.
- **New state:** `<select>` (defaults to the value the user picked in the row
  dropdown).
- **Publisher:** text input — shown when new state is `submitted` or `published`;
  **required** only for `submitted` (matches backend; `published` accepts an
  optional publisher).
- **Date:** date input — shown for `submitted`/`published`, pre-filled with
  today's date (`new Date().toISOString().slice(0,10)`); maps to `date_submitted`
  / `date_published` respectively.
- **OK / Cancel.**

Show/hide the publisher+date fields reactively when the New-state select changes.

**On OK** → `PUT /api/puzzles/<name>/state` with only the relevant fields:

```js
const body = { state: newState };
if (newState === 'submitted')  { body.publisher = pub; body.date_submitted  = date; }
if (newState === 'published')  { if (pub) body.publisher = pub; body.date_published = date; }
const resp = await apiFetch('PUT', `/api/puzzles/${encodeURIComponent(name)}/state`, body);
```

If the response carries an `error` (e.g. 400 missing publisher/date), show it
inline in the dialog and keep it open; otherwise close, re-fetch the dashboard,
and re-render. Reset the row's `<select>` to the actual state on Cancel/error so
the UI never drifts from the server.

> The backend requires `date_submitted` for `submitted` and `date_published` for
> `published`; since both default to today in the dialog, the happy path always
> satisfies it. Publisher-required-on-submit is enforced both client-side
> (`required`) and server-side.

### 2.6 Puzzle-preview popup (open-from-dashboard)

Clicking a puzzle's **name or title** — in either a top-half card row or a
bottom-table row — pops up a **preview** of that puzzle, the same size and
content as the thumbnails in the current Open-puzzle dialog, but framed with
**Open** and **Cancel** buttons.

- **Data:** `GET /api/puzzles/<name>/preview` →
  `{name, heading, width, svgstr}`, exactly as `showPreviewChooser` /
  `_chLoadPreviewsFromNames` already fetch
  ([ui.js:228](../../frontend/static/js/ui.js#L228),
  [puzzle_use_cases.py:573](../../crossword/use_cases/puzzle_use_cases.py#L573)).
  No new endpoint.
- **Render:** reuse the chooser thumbnail layout — the `svgstr` sized to `width`,
  with the `heading` (e.g. `name (N words, 7-letter: 12, …)`) below it — inside a
  modal `dialog-card`, so it matches the Open dialog's preview visually.
- **Buttons:** **Cancel** just dismisses the popup. **Open** dismisses it and
  opens the puzzle the normal way via `_openPuzzleInEditor(name)`
  ([puzzle-editor.js:713](../../frontend/static/js/puzzle-editor.js#L713)) —
  the same call `do_puzzle_open`'s chooser uses — then the view switches to the
  editor.
- **Markup:** add a dedicated `#preview-popup` modal to
  [index.html](../../frontend/index.html) (same `dialog-card` structure as the
  other modals: header with title + close, a body that holds the SVG, and a
  `dialog-actions` footer with Open/Cancel). A `showPuzzlePreview(name)` helper
  in `dashboard.js` fetches the preview, injects it, and wires the buttons.

> Only the name/title is the click target (it should look clickable — pointer
> cursor / link styling). The State dropdown and other row controls keep their
> own behavior; clicks there must not trigger the preview.

### 2.7 CSS ([style.css](../../frontend/static/css/style.css))

- `.dash-card-1..4` background colors (the four hex values above), card padding,
  rounded corners, and a 4-up responsive row (`display:flex`/`grid`, wraps on
  narrow widths).
- `.dash-card-title` (bold, larger) and `.dash-row-title` (bold, smaller).
- Progress widget: `.progress-wrap` (flex, right-aligned), `.progress-bar`
  (light-grey rounded track), `.progress-fill` (green, rounded, `width` set
  inline), `.progress-text` (small).
- Bottom card: full-width container, tab strip (reuse existing tab styling if any
  — the word editor / settings already have tab patterns), scrollable table body.
- `#state-dialog` reuses existing `dialog-card` styles; only field-specific
  tweaks needed.
- Dashboard view should span full width: when `AppState.view === 'dashboard'`,
  `#rhs` is empty — ensure `#lhs` takes the full workspace (a `workspace--full`
  modifier class toggled in `showView`, or `#rhs:empty` handling).

---

## Part 3 — Tests

### Backend (pytest, `crossword/tests/`)

- **Domain `fill_fraction`:** empty puzzle → 0.0; all white blank → 0.0;
  half-filled → ~0.5; fully filled → 1.0; all-black/no-white → 0.0.
- **Use case `get_dashboard`:** returns one row per real puzzle; excludes
  `__wc__`/`__new__`/NULL names; rows sorted `modified DESC`; each row has the
  documented keys; `top_lengths` holds the two largest lengths with correct
  counts; `state`/`publisher`/dates reflect the stored columns; `fill_pct` is the
  rounded percentage.
- **Persistence `list_puzzle_summaries`:** returns name+modified+state columns,
  filtered + ordered correctly.
- **HTTP:** `GET /api/dashboard` happy-path returns `{puzzles:[...]}` with the
  right shape for a seeded user; empty for a user with no puzzles.

### Front-end

Manual / visual verification (no JS test harness in the project):

- Four cards show correct counts, colors, top-4 rows, and per-card extras
  (progress bar / "fully clued" / "submitted to"/"published by").
- Tabs filter correctly; Publisher column appears only on
  submitted/published/all; `all` shows everything.
- State dropdown → dialog → OK transitions the puzzle and the view refreshes;
  Cancel reverts the dropdown; missing publisher/date surfaces the backend error
  inline.
- Clicking a name/title opens the preview popup with the same SVG/heading as the
  Open dialog; Open launches the editor; Cancel dismisses; clicks on the State
  dropdown don't trigger it.
- Dashboard is the landing view; nav button returns to it from the editor.

---

## Part 4 — Implementation order

1. **Domain** `Puzzle.fill_fraction()` + tests.
2. **Persistence** `list_puzzle_summaries()` on the port + SQLite adapter + tests.
3. **Use case** `get_dashboard()` + tests.
4. **HTTP** `handle_get_dashboard` + route; endpoints.md + Swagger; `--check`.
5. **Front-end** `dashboard.js`: data load + top-half cards.
6. Bottom-half tabbed table.
7. State-change dialog (`#state-dialog` modal + wiring to `PUT …/state`).
8. Preview popup (`#preview-popup` modal + `showPuzzlePreview` → Open/Cancel),
   wired to name/title clicks in cards and table.
9. CSS; make dashboard the landing view + nav button + `updateMenu` handling.
10. Visual pass against the spec; fix UI bugs.
