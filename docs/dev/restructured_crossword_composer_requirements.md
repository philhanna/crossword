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

Similar to the existing dashboard, with two changes:

- The "Archived" card is removed.
- A new "Themes" card is added as the leftmost card, linking to the theme
  editor (§2).

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

Filling in these attributes from empty is the theme editor's job.

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
- Rename a theme
- Delete a theme
- Select a crossword grid suited to the theme — essentially identical to
  the "new puzzle" functionality of the existing application (see the
  Grid selection component item in Appendix A)

### 2.3 Grid selection and evaluation

While selecting and fitting a grid, the editor should support:

- Finding a grid whose slot structure matches `word_lengths`
- Checking the grid and the proposed word placement for initial
  fillability, similar to the "Fill Order" function in the existing
  puzzle editor (§3.2) — it's important to detect early whether placing
  the theme words in the selected grid will make the rest of the fill
  difficult
- If the initial placement isn't satisfactory:
  - Reordering the theme words across the grid's symmetric slots, trying
    every permutation whose lengths still fit
  - Substituting `alternate_words` into `selected_words` and re-checking
    fillability
  - Selecting a different grid

### 2.4 Project phases

- **Phase 1 (base level):** the manual functionality described above.
- **Phase 2:** automation for theme types that are amenable to it — see
  [the automation design notes](https://docs.google.com/document/d/1LzysDPl1R3-8XdTh3mirkDbBA27meOhCGtcuQrKJXf8/edit?tab=t.0#heading=h.fk4gvjm280sp)
  and the [Cruciverb theme types](https://www.cruciverb.com/index.php?action=ezportal;sa=page;p=70)
  reference.

## 3. Composing editor

Essentially the existing puzzle and word editors, with the enhancements
below. Unlike §2, these are not yet split into phases — see Appendix A.

### 3.1 Word editor

- Allow a wider range of regular expressions, not just `.`
- Provide some way to see how constraints affect word selection

### 3.2 Improvements to the Fill Order function

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

### 3.3 Improvements to the word list

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
workflow in more detail:

1. **Audit history, not just a current snapshot** — every state transition,
   and every email sent or received about a given puzzle's submission, is
   recorded as a discrete, timestamped event, not overwritten in place.
2. **Structured publisher data** — publisher name, contact email,
   submission requirements, and (possibly) payment terms, looked up rather
   than typed freehand each time.
3. **Per-publisher editor contacts**, since a publisher may have more than
   one editor and submissions may be addressed to a specific person.
4. **Submission email drafting** — composing the email to a publisher
   according to that publisher's stated requirements.
5. **A rejected outcome** — a publisher can decline a puzzle, after which
   it returns to a pre-submission state rather than continuing toward
   publication.

### 4.2 Relationship to the existing puzzle-state machine

The existing `puzzles.state` enum is `draft`, `filled`, `finished`,
`submitted`, `published`, `archived`
([crossword/domain/puzzle_state.py](../../crossword/domain/puzzle_state.py)).
There is no `rejected` state, and per decision 2 (§4.5) there won't be
one: a rejection is logged as an *event*, whose effect is to write
`puzzles.state` back to `finished`. The state enum, the completion ladder,
and the Dashboard's existing cards/tabs are unchanged by this feature.

### 4.3 Proposed data model

All three tables are new. Column names below follow the existing schema's
mixed convention (`userid`/`puzzlename` with no separator on older
columns, `date_submitted`/`last_mode` with underscores on newer ones).
Decision §4.5 still leaves *which* convention to use for these new tables
open — see Appendix A.

#### 4.3.1 `submission_events` — append-only audit log

One row per event in a puzzle's submission history. Never updated or
deleted; the current snapshot on `puzzles` is derived from (or kept in
sync with) the latest relevant row here.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK, autoincrement | |
| `puzzle_id` | INTEGER, FK → `puzzles.id` | which puzzle |
| `timestamp` | TEXT (ISO 8601) | when the event occurred |
| `event_type` | TEXT | e.g. `submitted`, `email_sent`, `email_received`, `accepted`, `rejected`, `archived` — needs a closed enum (Appendix A) |
| `resulting_state` | TEXT | the `puzzles.state` value this event produces, if any — `NULL` for events that don't change state (e.g. a comment) |
| `publisher_id` | INTEGER, FK → `publishers.id`, nullable | which publisher this event concerns |
| `editor_id` | INTEGER, FK → `editors.id`, nullable | which editor, if applicable |
| `body` | TEXT | Markdown source — outgoing draft, or (user-pasted, then converted) incoming reply text; see decision 5 (§4.5) |

#### 4.3.2 `publishers` — reference data, one row per publisher

`puzzles.publisher` changes from free text to a foreign key referencing
`publishers.id` (decision 1, §4.5). Existing free-text values in
production data need a one-off migration to matching `publishers.id`
codes — the same "rebuild into a fresh DB" pattern used for the
state-column migration in
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
| `is_primary` | BOOLEAN | at most one per publisher; default editor when an event doesn't name one (decision 8, §4.5) |

### 4.4 Use cases

Following the existing code's pattern (`PuzzleUseCases`, `WordUseCases`,
etc. in [crossword/use_cases/](../../crossword/use_cases/)), this feature
implies three new use-case groups, plus a handful of cross-cutting
requirements not named explicitly above.

#### 4.4.1 `PublisherUseCases`

- Create / update / delete a publisher (`name`, `email`,
  `submission_limits`, `payment_info`, `spec_url`)
- List/lookup publishers — used both by the submission picker and by the
  one-off migration tool
- One-off migration: scan existing free-text `puzzles.publisher` values,
  create/match `publishers.id` codes, rewrite the column (§4.3.2,
  decision 1)

#### 4.4.2 `EditorUseCases`

- Create / update / delete an editor under a publisher
- Set/clear `is_primary` — must enforce "at most one per publisher"
  (§4.3.3, decision 8)
- Get the primary editor for a publisher, to default an event's editor
  when none is named

#### 4.4.3 `SubmissionUseCases` (the append-only event log, §4.3.1)

Each event type is its own use case, since its effect on `puzzles.state`
differs:

| Use case | Event logged | Effect on `puzzles` |
|---|---|---|
| Submit | `submitted` | `state = 'submitted'`, set `date_submitted` |
| Reject | `rejected` | `state = 'finished'`, clear `date_submitted` (decision 2) |
| Accept | `accepted` | `state = 'published'`, set `date_published` |
| Log email sent | `email_sent` | none (`resulting_state` is `NULL`) |
| Log email received | `email_received` | none (`resulting_state` is `NULL`) |
| Archive | `archived` | `state = 'archived'` |

Plus:

- Get submission history for a puzzle (renders the audit timeline)
- Get the current submission snapshot for a puzzle — derives/syncs the
  data the dashboard's "Submitted" card reads (decision 7; see also
  Appendix A on whether this is in scope for §1's dashboard)

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

The following gaps are unresolved design questions, not yet decisions —
they're carried to Appendix A rather than answered here: the publisher
delete guard, primary-editor reassignment, the snapshot sync strategy, and
whether `publishers`/`editors` are global or per-user.

### 4.5 Resolved decisions

1. **`puzzles.publisher` becomes a foreign key** into the new `publishers`
   table, replacing today's free-text field. Existing free-text values
   must be migrated to `publishers.id` codes (§4.3.2).
2. **`rejected` is an event type, not a new `puzzles.state` value.**
   Logging a `rejected` event writes `puzzles.state` back to `'finished'`;
   the state enum, the completion ladder, and the Dashboard's cards/tabs
   are unchanged (§4.2).
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
8. **`editor_id` on an event stays optional, and `editors` gains an
   `is_primary` flag** (§4.3.3) so the UI can default to a publisher's
   main contact when an event doesn't name a specific editor. An event
   references at most one editor — no CC/multi-editor list.

## Appendix A — Open issues

### A.1 Grid selection component

The grid selection in the theme editor (§2.3) and in the main puzzle
editor (§3) is essentially identical. Which editor should own this
component? Or should it be its own SPA, shared by both?

### A.2 `event_type` closed enum

§4.3.1 lists six example values (`submitted`, `email_sent`,
`email_received`, `accepted`, `rejected`, `archived`), but the full closed
enum isn't pinned down — e.g. is a non-state-changing "comment" event
(implied by `resulting_state` allowing `NULL`) in scope?

### A.3 Column naming convention for the new submissions tables

Pick one of the existing schema's two conventions — no separator
(`userid`, `puzzlename`) or underscored (`date_submitted`, `last_mode`) —
for all new columns in `submission_events`, `publishers`, and `editors`,
before implementing.

### A.4 Publisher delete guard

Deleting a publisher referenced by `editors`, `submission_events`, or
`puzzles.publisher_id` needs an in-use check or a defined cascade; §4.3.2
doesn't specify which.

### A.5 Primary-editor reassignment

Deleting or deactivating the editor flagged `is_primary` leaves the
publisher with no primary contact. Is there an explicit rule (e.g.
promote another editor automatically) or a use case the UI must call?

### A.6 Snapshot sync strategy

§4.3.1 says the `puzzles` snapshot is "derived from (or kept in sync
with) the latest relevant row" in `submission_events`. Does that sync
happen on write (push, at event-logging time) or on read (pull, computed
when the snapshot is requested)? This determines whether a separate
recompute use case is needed.

### A.7 Scoping of `publishers`/`editors`

Unlike `puzzles`, the proposed `publishers` and `editors` tables carry no
`user_id`. Confirm they're intended as global reference data shared
across all users, rather than per-user, before wiring `user_id` checks
into `PublisherUseCases`/`EditorUseCases`.

### A.8 Dashboard scope vs. the submissions snapshot

§4.4.3 says the submission snapshot use case feeds the dashboard's
"Submitted" card, but §1 (Dashboard) doesn't mention any change to that
card. Is consuming the new snapshot in scope for the dashboard described
in §1, or is it deferred to a later phase once the submissions editor
ships?

### A.9 Theme rename and identity

§2.2 lists "Rename a theme" as a CRUD operation. Puzzles have an explicit
rule that rename preserves the puzzle's `id` (see
[puzzle_state.md §11](puzzle_state.md#11-resolved-decisions)) — should
theme rename follow the same rule?

### A.10 Theme save semantics during editing

§2.1 requires 3–6 `selected_words` matching `len(word_lengths)`, and a
valid `grid`. Can a theme be saved while incomplete — e.g. before any
words are selected, or while the grid isn't yet chosen — consistent with
the existing app's auto-persist-on-edit pattern, or must "Save" enforce
that the theme is in a complete, internally consistent state?

### A.11 Phasing for the composing editor

§2.4 splits the theme editor into a base phase and a later automation
phase. §3 has no equivalent split, even though several of its items are
tagged **ML project** and are clearly longer-term research rather than
base functionality. Should §3 be explicitly phased the same way, and if
so, which items belong in the first version of the restructured
composing editor?
