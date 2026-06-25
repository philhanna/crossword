# Submission Tracking — design (draft, pre-decision)

> **Status:** This document is a first pass at scoping the feature. It is
> deliberately written *before* any schema or code exists. The major forks
> (publisher modeling, the `rejected` outcome, storage technology, email
> sending) are resolved in §4; the remaining open questions in §5 are
> narrower and should be settled before implementation starts.

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
| `body` | TEXT | the email body, or a free-text comment — see Q3 on representation |

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
| `submission_limits` | TEXT or structured fields | meaning needs defining — see Q4 |
| `payment_info` | TEXT or structured fields | meaning needs defining — see Q4 |
| `spec_url` | TEXT | link to the publisher's submission specification |

### 3.3 `editors` — contacts at a publisher

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK, autoincrement | |
| `publisher_id` | TEXT, FK → `publishers.id` | |
| `name` | TEXT | |
| `email` | TEXT | |

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
   back what they actually sent, the final) text — see Q1.

## 5. Open questions

These are narrower than §4 but still need answers before implementation.

**Q1 — What does the `body` column actually hold?**
Given decision 4 (draft-only, no sending), is `body` always plain text the
user can copy out and paste into their own mail client, or does it need to
support HTML/rich formatting to match a publisher's required email format?
And for `email_received` events, is the reply pasted in by the user, or is
this feature not responsible for logging inbound mail at all?

**Q2 — What goes in `submission_limits` and `payment_info`?**
As written these are free-text placeholders. Examples of what you have in
mind would let this become real columns (e.g. "max N submissions per
month", "pays $X on acceptance") instead of an opaque text blob.

**Q3 — Is this a new view in the existing SPA, or a separate app?**
"Next generation Crossword Puzzle app" in §1's source wording is ambiguous.
The existing frontend already has a 3-state menu machine (`home` /
`grid-editor` / `puzzle-editor`) plus the Dashboard view added in
[dashboard_impl.md](dashboard_impl.md). Is the "Submission Editor" a further
view/tab within that same SPA (most likely, given it reuses the same
backend and database per §2 of the original note), or a separate
application?

**Q4 — Does an event reference one editor, or can it reference several?**
A submission might be emailed to a publisher's general address with no
specific editor, or to a named editor. Is `editor_id` on the event always
optional, and is there a notion of a publisher's "primary" editor for
defaulting purposes?
