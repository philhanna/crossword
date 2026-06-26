# Submission Tracking — design (draft, pre-decision)

> **Status:** This document is a first pass at scoping the feature. It is
> deliberately written *before* any schema or code exists. All decisions —
> the major forks (publisher modeling, the `rejected` outcome, storage
> technology, email sending) and the narrower questions that followed
> (body format, publisher reference-data shape, UI placement, editor
> referencing) — are resolved in §4. Implementation may proceed against
> §3's schema, read together with those decisions.

## 1. Purpose

Today (per [puzzle_state.md](puzzle_state.md) /
[dashboard_impl.md](dashboard_impl.md), already implemented) every puzzle
carries a **current-state snapshot** directly on the `puzzles` row: `state`
(`draft → filled → finished → submitted → published`, or `archived`),
plus `publisher` (free text), `date_submitted`, and `date_published`. The
Dashboard lets the user move a puzzle between these states and enter the
publisher as free text at that point.

This feature extends that mechanism to support the **submission workflow in
more detail**:

1. **Audit history**, not just a current snapshot — every state transition,
   and every email sent or received about a given puzzle's submission, is
   recorded as a discrete, timestamped event, not overwritten in place.
2. **Structured publisher data** — publisher name, contact email,
   submission requirements, and (possibly) payment terms, looked up rather
   than typed freehand each time.
3. **Per-publisher editor contacts**, since a publisher may have more than
   one editor and submissions may be addressed to a specific person.
4. **Submission email drafting** — composing the email to a publisher
   according to that publisher's stated requirements.
5. A **`rejected` outcome** — a publisher can decline a puzzle, after which
   it returns to a pre-submission state rather than continuing toward
   `published`.

## 2. Relationship to the existing puzzle-state machine

The existing `puzzles.state` enum is `draft`, `filled`, `finished`,
`submitted`, `published`, `archived`
([crossword/domain/puzzle_state.py](../../crossword/domain/puzzle_state.py)).
There is no `rejected` state today, and per §4 there won't be one: a
rejection is logged as an **event** in the new event log, whose *effect* is
to write `puzzles.state` back to `'finished'` (and clear `date_submitted`).
The Dashboard's existing cards/tabs are unaffected.

## 3. Proposed data model (draft — see §5 before building any of this)

All three tables are new. Column names below follow the existing schema's
mixed convention (`userid`/`puzzlename` with no separator on older columns,
`date_submitted`/`last_mode` with underscores on newer ones); pick one
convention before implementing (Q5 in §5).

### 3.1 `submission_events` — append-only audit log

One row per event in a puzzle's submission history. Never updated or
deleted; the current snapshot on `puzzles` is derived from (or kept in sync
with) the latest relevant row here.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK, autoincrement | |
| `puzzle_id` | INTEGER, FK → `puzzles.id` | which puzzle |
| `timestamp` | TEXT (ISO 8601) | when the event occurred |
| `event_type` | TEXT | e.g. `submitted`, `email_sent`, `email_received`, `accepted`, `rejected`, `archived` — needs a closed enum (Q2) |
| `resulting_state` | TEXT | the `puzzles.state` value this event produces, if any — may be `NULL` for events that don't change state (e.g. a comment) |
| `publisher_id` | INTEGER, FK → `publishers.id`, nullable | which publisher this event concerns |
| `editor_id` | INTEGER, FK → `editors.id`, nullable | which editor, if applicable |
| `body` | TEXT | Markdown source — outgoing draft, or (user-pasted, then converted) incoming reply text; see decision 5 |

### 3.2 `publishers` — reference data, one row per publisher

`puzzles.publisher` changes from free text to a foreign key referencing
`publishers.id` (§4, decision 1). Existing free-text values in production
data need a one-off migration to matching `publishers.id` codes — the same
"rebuild into a fresh DB" pattern used for the state-column migration in
[puzzle_state.md §9](puzzle_state.md#9-one-off-migration-tool) is the
natural fit, once the set of real publishers is known.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT (3-char code) PK | e.g. `NYT`, `LAT`, `WSJ` — matches the example codes already used as free-text `publisher` values today |
| `name` | TEXT | full publisher name |
| `email` | TEXT | general/submissions contact address |
| `submission_limits` | TEXT | free text; no structured schema for now — see decision 6 |
| `payment_info` | TEXT | free text; no structured schema for now — see decision 6 |
| `spec_url` | TEXT | link to the publisher's submission specification |

### 3.3 `editors` — contacts at a publisher

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK, autoincrement | |
| `publisher_id` | TEXT, FK → `publishers.id` | |
| `name` | TEXT | |
| `email` | TEXT | |
| `is_primary` | BOOLEAN | at most one per publisher; default editor when an event doesn't name one — see decision 8 |

## 4. Resolved decisions

1. **`puzzles.publisher` becomes a foreign key** into the new `publishers`
   table, replacing the free-text field the Dashboard uses today. Existing
   free-text values must be migrated to `publishers.id` codes (§3.2).
2. **`rejected` is an event type, not a new `puzzles.state` value.** Logging
   a `rejected` event writes `puzzles.state` back to `'finished'`; the
   state enum, the completion ladder, and the Dashboard's cards/tabs are
   unchanged (§2).
3. **Storage stays in the existing SQLite database** — no separate
   NoSQL/JSON store. The event log and reference tables are ordinary
   tables in the same file as `puzzles`/`grids`/`users`, consistent with
   the project's SQLite-only architecture. A `TEXT` column holding a JSON
   string remains available for `submission_limits`/`payment_info` if
   those turn out to need a flexible/nested shape (open in Q2 below).
4. **The app only drafts the submission email**; it does not send it. No
   SMTP/API integration, credentials, or send infrastructure are in scope.
   `submission_events.body` records the drafted (or, if the user pastes
   back what they actually sent, the final) text.

5. **`submission_events.body` is Markdown, in both directions.** Outgoing
   drafts are composed and stored as Markdown. A client-side "Copy for
   Gmail" action renders that Markdown to HTML and writes both `text/html`
   and `text/plain` to the clipboard (via `ClipboardItem`), so pasting into
   Gmail's compose box reproduces real rich-text formatting rather than
   literal Markdown syntax. Incoming mail itself is **not** stored here —
   the email lives in Gmail (e.g. a `Crosswords/<publisher_id>` folder);
   logging an `email_received` event means the user pastes the relevant
   text in, and a client-side HTML→Markdown conversion step normalizes it
   to the same Markdown form before saving. One stored representation;
   conversion happens at the UI edge in both directions.

6. **`submission_limits` and `payment_info` stay free text.** No structured
   columns until real publisher data shows a concrete pattern worth
   defining a schema for.

7. **The Submission Editor is a separate application**, not a new view
   within the existing SPA's `home` / `grid-editor` / `puzzle-editor`
   menu machine. It shares the backend and database (per decision 3) but
   is its own frontend, launched independently of the puzzle/grid SPA.
   This describes the scope for 4.7 only: at this stage the Dashboard's
   existing cards/tabs are unaffected. Eventually the application becomes
   **three related SPAs sharing a common backend and database** — the
   puzzle/grid editor, the Submission Editor, and a third — and the
   Dashboard itself becomes its own SPA that links the other three. That
   future Dashboard gains new cards beyond today's, e.g. a **"Themes"**
   card for tracking themes under development (a new feature), and its
   existing **"Submitted"** card starts tracking data produced by the
   Submission Editor rather than the free-text fields described in §1.

8. **`editor_id` on an event stays optional, and `editors` gains an
   `is_primary` flag** (§3.3) so the UI can default to a publisher's main
   contact when an event doesn't name a specific editor. An event
   references at most one editor — no CC/multi-editor list.
