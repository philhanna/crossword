# Theme Spec for Puzzle Creation

## Overview

When the user creates a new puzzle, they may optionally supply a *theme spec*: a
palindromic list of integers representing the lengths of the theme (Across) words
(e.g., `7,5,5,7`). The spec is stored in the frontend for the duration of the
editing session and is passed to the generate-grid endpoint each time the user
clicks "Generate".

---

## Frontend

### Puzzle creation dialog

After the user enters the grid size, optionally prompt for a theme spec as a
comma-separated list of positive integers (e.g., `7,5,5,7`). The field is
optional; if left blank, no spec is stored.

**Validation (JavaScript):** If the field is non-empty, parse the input into an
integer array and verify that it is a palindrome. Reject non-palindromic input
with an error message before proceeding.

Store the validated spec as an integer array in a state variable (e.g.,
`currentSpec`) scoped to the current puzzle editor session. The spec is never
persisted to the database and is discarded when the puzzle is closed.

### Generate button

When the user clicks "Generate" in the puzzle editor, if `currentSpec` is
non-empty, append it to the request as `?spec=7,5,5,7` (comma-separated integers).
Clicking "Generate" multiple times reuses the same spec. If no spec was entered,
the parameter is omitted and existing behavior is unchanged.

---

## Backend

### Endpoint

`POST /api/puzzles/{name}/grid/generate`

Parse the optional `spec` query parameter into a list of integers and pass it
down the call stack to the `GridGeneratorPort` adapter.

### Adapter routing

| `xdfile` in config | `spec` provided | Behavior |
|---|---|---|
| absent | either | Ignore `spec`; use existing behavior |
| present | absent | Existing size-only matching |
| present | present | Apply theme constraints (see below) |

### Grid selection constraints

When both `xdfile` is configured and a `spec` is provided, the grid selection
query enforces two constraints simultaneously:

**1. Exact Across counts**

For each distinct length *L* in `spec`, the grid must have exactly `count(spec, L)`
Across slots of length *L*. This is implemented as one JOIN per distinct length
value.

**2. No forbidden lengths**

The grid must contain no Across or Down slot whose length either:

- exceeds `max(spec)`, or
- falls in a gap between any two consecutive distinct values of `spec` when sorted.

Implemented as a NOT EXISTS subquery. Slots shorter than `min(spec)` are
permitted (short fill entries are allowed).

**Example:** `spec = [7, 5, 5, 7]`, sorted distinct = `[5, 7]`

- Exactly 2 Across slots of length 5, exactly 2 of length 7
- No Across or Down slots of length 6 or ≥ 8
- 3- and 4-letter fill entries are permitted

### Grid construction (unchanged)

Select one matching row at random. Parse `grid_text` (newline-separated rows,
`#` = black cell) into a `Grid` object. Raise `RuntimeError` if no matching grid
exists.
