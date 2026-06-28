# Restructured Crossword Composer — Requirements

**Status:** Draft requirements for the next major version. Section 4 carries
forward the decisions and open items from `submissions_app_design.md`
(now superseded by this document — see Appendix A).

## Contents

- [Overview](#overview)
- [1. Dashboard](#1-dashboard)
- [2. Theme editor](#2-theme-editor)
- [3. Composing editor](#3-composing-editor)
- [4. Submissions editor](#4-submissions-editor)
- [Appendix A — Open issues](#appendix-a--open-issues)

## Overview

The application is currently a single SPA with a dashboard and a puzzle
editor. This document restructures it into four applications, sharing a
common database and Python server component, each with its own SPA:

1. A dashboard that links the other three editors
2. The theme editor (new)
3. The composing editor (the existing grid/puzzle editor, enhanced)
4. The submissions editor (new)

## 1. Dashboard

Similar to the existing dashboard, with three changes:

- The "Archived" card is removed.
- A new "Themes" card is added as the leftmost card, linking to the theme
  editor (§2).
- Cards driven by submission status (e.g. "Submitted") read the derived
  status from §4.4.3 instead of `puzzles.state`/`puzzles.publisher`
  directly, so they reflect submission events as they're logged
  (Appendix A.8).

### 1.1 Use cases

- **Get dashboard summary** — the existing `PuzzleUseCases.get_dashboard`
  use case, updated to drop the "Archived" card and to source
  submission-related rows (e.g. "Submitted") from the submissions
  editor's "get current submission status" use case (§4.4.3) instead of
  reading `puzzles.state`/`puzzles.publisher` directly (Appendix A.8)
- **List themes for the "Themes" card** — delegates to the new
  `ThemeUseCases.list_themes` (§2.5), used both to populate the card and
  to link through to the theme editor (§2)

## 2. Theme editor

### 2.1 Object model

A theme is an object with the following attributes, all empty when the
theme is first created:

| Attribute | Description |
|---|---|
| `id` | unique identifier |
| `name` | short theme name |
| `word_lengths` | a palindromic list of lengths, e.g. `[13, 12, 12, 13]` or `[10, 15, 10]` — reflects the point symmetry of the grid, since theme entries occupy symmetric slots |
| `candidate_words` | theme words that fit `word_lengths` |
| `selected_words` | the words actually placed in the grid; between 3 and 6 of them, drawn from `candidate_words`. The count must equal `len(word_lengths)` |
| `alternate_words` | a small number of additional `candidate_words` that fit `word_lengths` but are not currently selected |
| `grid` | a valid crossword grid into which `selected_words` can be placed |

Filling in these attributes from empty is the theme editor's job. There
is no separate completeness/status field — a theme is "complete" when
`grid` is set and `len(selected_words) == len(word_lengths)`, computed
on the fly rather than stored (Appendix A.12).

### 2.2 Editor functionality

The user can perform the usual CRUD operations on a theme:

- Create a new theme
- Open an existing theme
- Edit its attributes
- Add, delete, and change words in `candidate_words` and `alternate_words`
- Move words between `candidate_words` and `alternate_words`
- Validate theme words and alternates against the existing word-list API
- Save the theme
- Save the theme under a new name
- Rename a theme — preserves the theme's `id`, same as puzzle rename
  (Appendix A.9)
- Delete a theme — no in-use check needed; puzzles created from a theme
  keep no reference back to it (Appendix A.13)
- Select a crossword grid suited to the theme — essentially identical to
  the "new puzzle" functionality of the existing application, via the
  shared grid-picker component (Appendix A.1)

### 2.3 Grid selection and evaluation

While selecting and fitting a grid (via the shared component, Appendix
A.1), the editor should support:

- Finding a grid whose slot structure matches `word_lengths`
- Checking the grid and the proposed word placement for initial
  fillability, similar to the "Fill Order" function in the existing
  puzzle editor (§3.3) — it's important to detect early whether placing
  the theme words in the selected grid will make the rest of the fill
  difficult
- If the initial placement isn't satisfactory, the user can perform any
of the following actions:
  - Reorder the theme words across the grid's symmetric slots, trying
    every permutation whose lengths still fit
  - Substitute `alternate_words` into `selected_words` and re-checking
    fillability
  - Select a different grid

### 2.4 Project phases

- **Phase 1 (base level):** the manual functionality described above.
- **Phase 2:** automation for theme types that are amenable to it — see
  [the automation design notes](https://docs.google.com/document/d/1LzysDPl1R3-8XdTh3mirkDbBA27meOhCGtcuQrKJXf8/edit?tab=t.0#heading=h.fk4gvjm280sp)
  and the [Cruciverb theme types](https://www.cruciverb.com/index.php?action=ezportal;sa=page;p=70)
  reference.

### 2.5 Use cases

New `ThemeUseCases` group, following the existing pattern
(`PuzzleUseCases`, `WordUseCases`, etc. in
[crossword/use_cases/](../../crossword/use_cases/)):

- Create / open / delete a theme — delete needs no in-use check, since
  puzzles created from a theme keep no reference back to it (Appendix
  A.13)
- Save / save-as / rename a theme — rename preserves the theme's `id`
  (Appendix A.9)
- Edit attributes: set `word_lengths`; add, delete, and edit words in
  `candidate_words`/`alternate_words`; move words between the two
- Validate theme words and alternates — delegates to the existing
  word-list API (`WordUseCases`)
- Check whether a theme is "complete" — computed from `grid` and
  `selected_words` (Appendix A.12), not a stored field
- Select and evaluate a grid for a theme (§2.3), via the shared
  grid-picker component (Appendix A.1):
  - Find grids whose slot structure matches `word_lengths`
  - Check initial fillability of the proposed placement
  - Reorder theme words across the grid's symmetric slots
  - Substitute `alternate_words` into `selected_words` and recheck
    fillability
  - Select a different grid
- List/preview themes — used by this editor's own chooser and by §3.1's
  theme picker, which filters to "complete" themes only

## 3. Composing editor

Essentially the existing puzzle and word editors, with the enhancements
below. Unlike §2, these are not split into phases — each item ships
independently, including the **ML project**-tagged items, with no
global phase plan tying it to the theme editor's phasing (Appendix
A.11). Its existing "new puzzle" grid selection moves onto the shared
grid-picker component (Appendix A.1), the same one the theme editor's
§2.3 uses.

### 3.1 New puzzle
The existing functionality needs to be preserved, with the sole exception
of the prompt shown when creating a new puzzle.
- For themed puzzles, the "new puzzle" action needs to select
from a theme picker
  - Show a richly formatted list of completed themes built by the
  theme editor — "completed" per Appendix A.12 (`grid` set,
  `len(selected_words) == len(word_lengths)`), computed on the fly
  rather than a stored status.
  - Selecting a theme will necessarily provide the grid size, the
  grid attributes, and the slot locations of the theme words.  The composing editor will create a new puzzle in puzzle mode and invoke the puzzle editor as usual.  The theme words will start in the locked state.
  - The theme's data is copied into the new puzzle; the puzzle keeps no
  reference back to the source theme (Appendix A.13).
  - At this point, the puzzle will be tracked as part of the composing editor in draft mode.  The dashboard will show it as such.

### 3.2 Word editor

- Allow a wider range of regular expressions, not just `.`
    - For example, `MA[^AEIOU]` for "MA" followed by a consonant
    - All regular expressions should be permitted, although the
    suggest button functionality will only search for words of the correct length.

### 3.3 Improvements to the Fill Order function

- Make it genuinely correct and fast.
- Refine the ranking criteria — candidates so far:
  - Most-constrained words first
  - Critical-bridge detection
  - Suitability (limit crosswordese, unpleasant words, etc.)
  - There may be more
- Probability-based predictor of constraint satisfaction, instead of
  scanning the full ~500,000-word list (**ML project**; some prior work
  exists — see [wordmatch_pattern](https://github.com/philhanna/wordmatch_pattern))
- Possibly build a labeled training set from uncompleted words:
  - Capture uncompleted words whenever "Fill Order" is clicked
  - Add these to a training set of regular expressions for the model
- Scored word lists, so the best words sort to the top — ordering is more
  than just constraint matching
- Cache fill-order results (granularity — per word? per puzzle? — and
  invalidation rule are open; see Appendix A)
- Pre-fill the cache on a background thread whenever a word changes
- Possibly a heat map to highlight critical areas
- Auto-fill:
  - Select an area with the mouse and fill just that area
  - Cycle through alternatives, as the grid-generate button does today
  - Requires the suitability-scored word list above
- Cluing:
  - Possibly embed an ML clue-writing tool in the word editor
  - Possibly characterize publishers' preferred clue style by analyzing
    their published clues (**ML project**)

### 3.4 Improvements to the word list

- Score words by suitability (**ML project**):
  - Switch from a plain text file to CSV with multiple attributes
  - Score the entire list, e.g. a 0–1 score from frequency of use in
    published puzzles (see the [GXD clues database](https://xd.saul.pw/data));
    some prior work exists (see [word-scorer](https://github.com/philhanna/word-scorer)).
    Other scoring schemes are possible, e.g.
    [Peter Broda's word list](https://www.peterbroda.me/crosswords/wordlist/lists/peter-broda-wordlist__gridtext__scored__july-25-2023.txt).
    Scoring needs to integrate with the constraint checking the word
    editor's "Suggest" button already provides.
  - Option to restrict suggestions to words above a score threshold
    (effectively filtering out crosswordese)
  - Sort by length, score, then word
- Other ML projects:
  - Build per-publisher word lists from the GXD puzzle database
  - Train per-publisher models on word frequency (**ML project**)
  - Predict which publishers might want a given filled puzzle, from word
    characteristics and theme type (**ML project**)
- Split compound entries into individual words, e.g. "ABETTERPLACE" into
  "A" / "BETTER" / "PLACE" (and potentially "ABET" / "ABETTER")
- Classify words by part of speech (**ML project**); a word may have more
  than one (e.g. "iron" as noun, verb, possibly adjective)

### 3.5 Use cases

Extends the existing `PuzzleUseCases`/`WordUseCases`, plus one new use
case for the theme-driven flow:

- **Create puzzle from theme** (new, §3.1) — given a theme, copies its
  grid and words into a new puzzle in puzzle mode, locks the theme
  words, and tracks the puzzle in draft mode on the dashboard. Stores no
  reference back to the source theme (Appendix A.13)
- List completed themes — for §3.1's theme picker; delegates to
  `ThemeUseCases` (§2.5), filtered to "complete" themes (Appendix A.12)
- Existing grid/puzzle use cases (`create_puzzle`,
  `switch_to_grid_mode`/`switch_to_puzzle_mode`, etc.) are unchanged for
  the non-themed "new puzzle" path, including the shared grid-picker
  (Appendix A.1)
- `WordUseCases.get_word_constraints`/`get_ranked_suggestions` extended
  to support the wider regex syntax in §3.2 (e.g. `MA[^AEIOU]`), while
  "Suggest" still only searches words of the correct length
- `PuzzleUseCases.get_fill_order`, reworked per §3.3: corrected/faster
  computation, refined ranking, caching with an invalidation rule, and
  auto-fill over a user-selected area
- Word-list use cases extended per §3.4 for suitability scoring and the
  other **ML project** items

## 4. Submissions editor

### 4.1 Purpose

Today, every puzzle carries a current-state snapshot directly on the
`puzzles` row: `state` (`draft → filled → finished → submitted →
published`, or `archived`), plus `publisher` (free text), `date_submitted`,
and `date_published` (see [puzzle_state.md](puzzle_state.md), already
implemented — the earlier `dashboard_impl.md` design has since been
superseded by the shipped implementation). The Dashboard lets the user
move a puzzle between these states and enter the publisher as free text at
that point.

The submissions editor extends that mechanism to support the submission
workflow in more detail, and normalizes away the duplication between that
snapshot and the new event log:

1. **Audit history, not just a current snapshot** — every state transition,
   and every email sent or received about a given puzzle's submission, is
   recorded as a discrete, timestamped event, not overwritten in place.
2. **No redundant snapshot columns** — `publisher`, `date_submitted`, and
   `date_published` are removed from `puzzles` entirely. The submission
   status, publisher, and dates are always derived by querying
   `submission_events` directly, rather than kept as a second copy that
   has to stay in sync with it (Appendix A.6).
3. **Structured publisher data** — publisher name, contact email,
   submission requirements, and (possibly) payment terms, looked up rather
   than typed freehand each time.
4. **Per-publisher editor contacts**, since a publisher may have more than
   one editor and submissions may be addressed to a specific person.
5. **Submission email drafting** — composing the email to a publisher
   according to that publisher's stated requirements.
6. **A rejected outcome** — a publisher can decline a puzzle, after which
   it returns to a pre-submission state rather than continuing toward
   publication.

### 4.2 Relationship to the existing puzzle-state machine

The existing `puzzles.state` enum is `draft`, `filled`, `finished`,
`submitted`, `published`, `archived`
([crossword/domain/puzzle_state.py](../../crossword/domain/puzzle_state.py)).
`draft`/`filled`/`finished` are auto-detected from puzzle content
(`detect_completion_state`) and stay a stored column on `puzzles`,
unaffected by this feature.

`submitted`/`published`/`archived` are no longer written to
`puzzles.state` directly — that's a change to today's "set from the
dashboard" behavior noted in `puzzle_state.py`. Once a puzzle has at
least one row in `submission_events`, its effective status is the
`resulting_state` of that puzzle's most recent event that has a
non-`NULL` `resulting_state` (events like `email_sent`/`email_received`/
`comment` don't change status, so the lookup skips past them to the
last one that did). A puzzle with no submission events yet is still
read straight from the `draft`/`filled`/`finished` column.

There is no `rejected` state, and per decision 2 (§4.5) there won't be
one: a rejection is logged as an *event* whose `resulting_state` is
`finished` — the same derivation that surfaces `submitted`/`published`/
`archived` falls back to `finished` after a rejection, without writing
anything back to `puzzles`. The completion ladder and the Dashboard's
existing cards/tabs are unchanged by this feature.

### 4.3 Proposed data model

All three tables are new. The existing schema mixes two conventions
(`userid`/`puzzlename` with no separator on older columns,
`date_submitted`/`last_mode` with underscores on newer ones); the column
names below use the underscored convention throughout (resolved, Appendix
A.3).

#### 4.3.1 `submission_events` — append-only audit log

One row per event in a puzzle's submission history. Never updated or
deleted. There is no snapshot stored on `puzzles` — submission status,
publisher, and submission/publication dates are always derived by
querying this table directly (resolved, Appendix A.6).

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK, autoincrement | |
| `puzzle_id` | INTEGER, FK → `puzzles.id` | which puzzle |
| `timestamp` | TEXT (ISO 8601) | when the event occurred |
| `event_type` | TEXT | closed enum (Appendix A): `submitted`, `email_sent`, `email_received`, `accepted`, `rejected`, `archived`, `comment` |
| `resulting_state` | TEXT | the `puzzles.state` value this event produces, if any — `NULL` for events that don't change state (e.g. a comment) |
| `publisher_id` | INTEGER, FK → `publishers.id`, nullable | which publisher this event concerns |
| `editor_id` | INTEGER, FK → `editors.id`, nullable | which editor, if applicable |
| `body` | TEXT | Markdown source — outgoing draft, or (user-pasted, then converted) incoming reply text; see decision 5 (§4.5) |

#### 4.3.2 `publishers` — reference data, one row per publisher

`puzzles.publisher` (today's free-text column) is dropped; the current
publisher for a puzzle, if any, is the `publisher_id` of its most recent
`submission_events` row that has one (decision 1, §4.5). Existing
free-text `puzzles.publisher` values in production data need a one-off
migration: match each to a `publishers.id` code and synthesize a
`submitted` event carrying that `publisher_id`, so derivation has
something to find — the same "rebuild into a fresh DB" pattern used for
the state-column migration in
[puzzle_state.md §9](puzzle_state.md#9-one-off-migration-tool) is the
natural fit, once the set of real publishers is known.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT (3-char code) PK | e.g. `NYT`, `LAT`, `WSJ` — matches the example codes already used as free-text `publisher` values today |
| `name` | TEXT | full publisher name |
| `email` | TEXT | general/submissions contact address |
| `submission_limits` | TEXT | free text; no structured schema for now (decision 6, §4.5) |
| `payment_info` | TEXT | free text; no structured schema for now (decision 6, §4.5) |
| `spec_url` | TEXT | link to the publisher's submission specification |

#### 4.3.3 `editors` — contacts at a publisher

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK, autoincrement | |
| `publisher_id` | TEXT, FK → `publishers.id` | |
| `name` | TEXT | |
| `email` | TEXT | |

### 4.4 Use cases

Following the existing code's pattern (`PuzzleUseCases`, `WordUseCases`,
etc. in [crossword/use_cases/](../../crossword/use_cases/)), this feature
implies three new use-case groups, plus a handful of cross-cutting
requirements not named explicitly above.

#### 4.4.1 `PublisherUseCases`

- Create / update / delete a publisher (`name`, `email`,
  `submission_limits`, `payment_info`, `spec_url`) — delete is rejected
  if the publisher is still referenced by `editors` or
  `submission_events` (Appendix A.4)
- List/lookup publishers — used both by the submission picker and by the
  one-off migration tool
- One-off migration: scan existing free-text `puzzles.publisher` values,
  create/match `publishers.id` codes, synthesize a `submitted` event per
  puzzle carrying that `publisher_id`, then drop the column (§4.3.2,
  decision 1)

#### 4.4.2 `EditorUseCases`

- Create / update / delete an editor under a publisher

#### 4.4.3 `SubmissionUseCases` (the append-only event log, §4.3.1)

Each event type is its own use case, since the `resulting_state` it
records differs (nothing is ever written back to `puzzles`; this is just
what later derivation reads, §4.2):

| Use case | Event logged | `resulting_state` recorded |
|---|---|---|
| Submit | `submitted` | `submitted` |
| Reject | `rejected` | `finished` (decision 2) |
| Accept | `accepted` | `published` |
| Log email sent | `email_sent` | `NULL` |
| Log email received | `email_received` | `NULL` |
| Archive | `archived` | `archived` |
| Comment | `comment` | `NULL` |

Plus:

- Get submission history for a puzzle (renders the audit timeline)
- Get the current submission status for a puzzle — a pure query over
  `submission_events` (§4.2), with no stored snapshot to keep in sync
  (decision 7; see also Appendix A.8 on whether this is in scope for
  §1's dashboard)

#### 4.4.4 Email drafting (decisions 4–5, §4.5)

- Draft a submission email body in Markdown, using the target publisher's
  `submission_limits`/contact info. The app only drafts the email; it
  does not send it — no SMTP/API integration is in scope (decision 4).
- Convert Markdown → `text/html` + `text/plain` and write both to the
  clipboard via `ClipboardItem` ("Copy for Gmail")
- Convert pasted HTML (an incoming reply) → Markdown before saving it as
  an `email_received` event's `body`

#### 4.4.5 Implicit requirements

Not named explicitly above, but required for §4.3/§4.4 to be correct:

- **Enum validation** — `event_type` must be checked against the closed
  enum once it's settled (Appendix A); `resulting_state`, if non-null,
  must be one of the existing `puzzles.state` values.
- **Referential checks** — an event naming both `publisher_id` and
  `editor_id` must validate that the editor actually belongs to that
  publisher.

### 4.5 Resolved decisions

1. **`puzzles.publisher` is dropped, not converted to a foreign key.**
   Today's free-text field is removed entirely; the current publisher
   for a puzzle is derived from its most recent `submission_events` row
   with a `publisher_id` set, referencing the new `publishers` table.
   Existing free-text values must be migrated to `publishers.id` codes
   and a corresponding event, not just rewritten in place (§4.3.2).
2. **`rejected` is an event type, not a new `puzzles.state` value.**
   Logging a `rejected` event records a `resulting_state` of `'finished'`
   on the event row; nothing is written back to `puzzles.state` itself —
   that value is derived when read (§4.2). The state enum, the completion
   ladder, and the Dashboard's cards/tabs are unchanged.
3. **Storage stays in the existing SQLite database** — no separate
   NoSQL/JSON store. The event log and reference tables are ordinary
   tables alongside `puzzles`/`grids`/`users`. A `TEXT` column holding a
   JSON string remains available for `submission_limits`/`payment_info`
   if those need a flexible/nested shape later (see decision 6).
4. **The app only drafts the submission email; it does not send it.** No
   SMTP/API integration, credentials, or send infrastructure are in
   scope. `submission_events.body` records the drafted (or, if the user
   pastes back what they actually sent, the final) text.
5. **`submission_events.body` is Markdown, in both directions.** Outgoing
   drafts are composed and stored as Markdown. A client-side "Copy for
   Gmail" action renders that Markdown to HTML and writes both
   `text/html` and `text/plain` to the clipboard (via `ClipboardItem`),
   so pasting into Gmail's compose box reproduces real rich-text
   formatting rather than literal Markdown syntax. Incoming mail itself
   is **not** stored here — the email lives in Gmail (e.g. a
   `Crosswords/<publisher_id>` folder); logging an `email_received`
   event means the user pastes the relevant text in, and a client-side
   HTML→Markdown conversion step normalizes it to the same Markdown form
   before saving. One stored representation; conversion happens at the
   UI edge in both directions.
6. **`submission_limits` and `payment_info` stay free text.** No
   structured columns until real publisher data shows a concrete pattern
   worth defining a schema for.
7. **The submissions editor is a separate application**, not a new view
   within the existing SPA's `home` / `grid-editor` / `puzzle-editor`
   menu machine. It shares the backend and database (decision 3) but is
   its own frontend. This restructuring (§Overview) carries that further:
   the application becomes four related SPAs sharing a common backend and
   database — the dashboard, the theme editor, the composing editor, and
   the submissions editor — with the dashboard linking the other three
   rather than embedding them.
8. **`editor_id` on an event stays optional, with no "primary editor"
   concept.** There's no functionality that depends on designating one
   editor per publisher as primary, so `editors` has no `is_primary`
   flag and there's no default-editor lookup (Appendix A.5). An event
   references at most one editor — no CC/multi-editor list.

## Appendix A — Open issues

### A.1 Grid selection component

Resolved: a shared frontend component, not its own SPA, and not owned
by either editor. The existing preview-chooser code (currently in
`frontend/static/js/app.js`) moves into a standalone, framework-free
module (e.g. `frontend/shared/grid_picker.js`) served as a static asset,
which both the theme editor SPA and the composing editor SPA include
directly. This extends decision 7's (§4.5) shared backend/database to
one shared frontend asset as well, while keeping the two SPAs otherwise
independent — a separate SPA would add cross-frame signaling and a
second navigation/modal stack for no benefit, since the component has no
routes or independent state of its own. Backend endpoints
(`/api/grids/{name}/preview` and friends) need no change; they're
already generic. Domain-specific behavior — §2.3's filtering by
`word_lengths` and fillability pre-check — stays in the theme editor,
layered on top via a filter passed into the shared picker, not inside
the shared component itself.

### A.2 `event_type` closed enum

Resolved: `event_type` is a closed enum with seven values — `submitted`,
`email_sent`, `email_received`, `accepted`, `rejected`, `archived`, and
`comment` (a non-state-changing event, `resulting_state` is `NULL`).

### A.3 Column naming convention for the new submissions tables

Resolved: all new columns in `submission_events`, `publishers`, and
`editors` use the underscored convention (`date_submitted`, `last_mode`),
not the no-separator convention (`userid`, `puzzlename`). The column
lists in §4.3.1–§4.3.3 already follow this.

### A.4 Publisher delete guard

Resolved: deleting a publisher requires an in-use check, not a cascade.
If the publisher is referenced by `editors` or `submission_events`
(`puzzles` no longer has a `publisher_id` column to check — §4.5
decision 1), the delete is rejected and the user must resolve the
references manually (e.g. reassign or delete the dependent
editors/events) before the publisher can be deleted.

### A.5 Primary-editor reassignment

Resolved: there's no "primary editor" concept. No functionality depends
on designating one editor per publisher as primary, so `editors` has no
`is_primary` flag, and there's no default-editor lookup or reassignment
rule to define (§4.5 decision 8).

### A.6 Snapshot sync strategy

Resolved: pull, not push. There is no stored snapshot on `puzzles` to
keep in sync — `state` (for `submitted`/`published`/`archived`),
publisher, and submission/publication dates are computed on read,
straight from `submission_events`, every time they're requested (§4.2,
§4.3.1, §4.5 decisions 1–2). No recompute-on-write use case is needed;
the only query needed is "the most recent event for this puzzle with a
non-`NULL` `resulting_state`" (and, for publisher, the most recent event
with a non-`NULL` `publisher_id`).

### A.7 Scoping of `publishers`/`editors`

Resolved: global, not per-user. `publishers` and `editors` are shared
reference data across all users, so they carry no `user_id` (unlike
`puzzles`), and `PublisherUseCases`/`EditorUseCases` need no `user_id`
checks.

### A.8 Dashboard scope vs. the submissions snapshot

Resolved: in scope, not deferred. The dashboard's cards (e.g.
"Submitted") must reflect submission status changes as they happen —
consuming the derived status from §4.4.3's "get current submission
status" use case is part of this feature, not a later phase.

### A.9 Theme rename and identity

Resolved: yes, theme rename follows the same rule as puzzles. §2.2 lists
"Rename a theme" as a CRUD operation; like puzzles' rename rule (see
[puzzle_state.md §11](puzzle_state.md#11-resolved-decisions)), renaming a
theme preserves its `id`.

### A.10 Theme save semantics during editing

Resolved: yes, a theme can be saved while incomplete. §2.1's constraints
(3–6 `selected_words` matching `len(word_lengths)`, a valid `grid`)
describe a *finished* theme, not a precondition for "Save" — consistent
with the existing app's auto-persist-on-edit pattern (e.g. before any
words are selected, or while the grid isn't yet chosen). "Save" does not
enforce completeness.

### A.11 Phasing for the composing editor

Resolved: there is no global phasing scheme across editors. §2.4's
base/automation phase split is local to the theme editor and isn't
mirrored onto §3 — each editor (theme, composing, submissions) can be
upgraded independently, on its own schedule, including the
**ML project**-tagged items in §3. The only requirement is that the
dashboard stay in sync with whichever capabilities are actually shipped
at a given point (Appendix A.8).

### A.12 Theme completeness for the new-puzzle theme picker

Resolved: computed, not stored. §2.1 gets no new status field. A theme
counts as "completed," and is eligible to appear in §3.1's theme picker,
if `grid` is set and `len(selected_words) == len(word_lengths)` — the
same fields already in the object model, checked on the fly rather than
tracked separately.

### A.13 Theme-puzzle link after puzzle creation

Resolved: a one-time copy, no ongoing link. When §3.1 creates a puzzle
from a theme, the theme's grid and words are copied into the new puzzle;
the puzzle keeps no `theme_id` reference back to its source theme.
Deleting the theme later has no effect on puzzles already created from
it, and (unlike A.4's publisher delete guard) no in-use check is needed
on theme deletion.
