# Issue 202 Info Panel Integration Plan

## Goal

Implement a first user-facing version of issue #202 by showing a compact list of recommended fill slots in the existing Info panel.

The list should appear:

- after the `Black cells:` line
- before the word-length table

This version should help the user answer a practical question:

> Which slots should I try filling next?

## Why This Placement Works

The current Info screen is already the app's read-only analysis panel. That makes it a natural place for fill-order guidance.

This placement has several advantages:

- it does not disturb the main Across/Down clue lists
- it does not interrupt keyboard-based fill entry
- it keeps the feature discoverable through the existing `Info` button
- it allows a concise "recommended next fills" section without turning the UI into a diagnostic dashboard

## Product Direction

Issue #202 began as a structural-interlock idea, but the later discussion broadened it to a more useful ranking based on constrained fill. The UI should reflect that.

So the Info panel should not present this as only a list of "critical bridge" slots. Instead, it should present a short ranked list of recommended slots, where:

- candidate scarcity is the main signal
- structural criticality is an important boost and explanation

That keeps the feature aligned with how constructors actually work:

1. fill forced or near-forced entries first
2. prefer structurally important slots when several slots are similarly constrained

## Scope For V1

Add a new Info-panel section titled something like:

- `Best slots to try next`
- or `Fill priority`

V1 should:

- show only the top 5 to 10 slots
- be read-only
- be compact enough to fit naturally inside the existing stats panel
- make each slot clickable so the user can select that word in the grid

V1 should not:

- reorder the clue lists
- open the word editor automatically
- display raw graph-analysis internals unless needed for a short explanation
- try to expose the full ranking for every slot

## Recommended Presentation

Each row should contain:

- slot label, such as `14A`
- current pattern, such as `A..E.`
- candidate count, such as `3 candidates`
- a short reason, such as `Critical bridge` or `Tight crossings`

Example:

```text
Best slots to try next
14A  A..E.   3 candidates   Critical bridge
7D   ..R..T  5 candidates   Splits grid
22A  ....    8 candidates   Tight crossings
```

### Interaction

Clicking a row should:

- close nothing
- select that slot in the puzzle grid
- highlight it exactly as if the user had clicked the clue
- re-render the clue list with that slot selected if the user later closes Info

This should feel like a navigation shortcut, not a mode change.

## Data Shape

The backend stats response should grow a new field, for example:

```json
{
  "fill_priority": [
    {
      "seq": 14,
      "direction": "across",
      "label": "14A",
      "pattern": "A..E.",
      "candidate_count": 3,
      "critical": true,
      "reason": "Critical bridge"
    }
  ]
}
```

Suggested fields per item:

- `seq`
- `direction`
- `label`
- `pattern`
- `candidate_count`
- `critical`
- `reason`

Optional later fields:

- `score`
- `component_count`
- `component_sizes`

Those optional fields can stay internal for V1 if the UI does not need them.

## Ranking Model

Use a weighted ranking instead of a binary rule.

Suggested V1 ordering:

1. incomplete slots only
2. fewer candidates first
3. structurally critical slots ahead of non-critical slots when candidate counts are similar
4. shorter length as a mild tie-break
5. lower clue number as final stable tie-break

This keeps the ranking understandable and matches the issue discussion better than a pure interlock score.

## Backend Work

### 1. Reuse or extend fill-priority analysis

If the work from `help_fill.md` already exists in some form, reuse it. Otherwise create a domain helper that can rank slots and return UI-friendly metadata.

Likely module:

- `crossword/domain/fill_priority.py`

Suggested responsibilities:

- enumerate puzzle slots
- compute candidate counts for each slot
- compute structural criticality for each slot
- combine those into a stable ranking
- produce a short reason string for display

### 2. Feed the Info endpoint

Extend the existing puzzle stats use case or handler so `GET /api/puzzles/{name}/stats` includes the new ranked slot list.

This is a good fit because:

- the frontend already fetches stats only when Info is opened
- the Info panel is already rendered from a single payload
- no new top-level frontend mode is required

### 3. Keep the payload compact

The stats endpoint should probably return only the top N rows, such as 5 or 10.

That avoids:

- computing more data than needed for V1
- sending a large diagnostic structure to the browser
- encouraging an overcrowded panel

## Frontend Work

### 1. Extend `renderStatsPanel()`

Update `frontend/static/js/app.js` so the stats panel inserts a new section between:

- `Black cells:`
- the word-length table

The new section should render:

- a short heading
- a compact clickable list or table

### 2. Reuse existing selection behavior

Each row should call `selectWord(seq, direction)` so it behaves like selecting from the clue list.

That keeps the interaction consistent and avoids adding a second navigation model.

### 3. Keep the styling modest

This should look like part of the existing Info panel, not a separate app inside it.

Suggested visual treatment:

- section heading in the same style as other Info content
- simple list or table rows
- subtle emphasis on candidate count
- a small badge or plain-text label for `Critical bridge`

No dense score bars or debug metrics in V1.

## Suggested Reason Labels

Keep reasons short and user-facing. For example:

- `Only 1 candidate`
- `Only 3 candidates`
- `Critical bridge`
- `Splits grid`
- `Tight crossings`
- `Nearly forced`

Avoid exposing terms like `component_count=3` directly in the main row text.

If needed, that can be added later as a tooltip or secondary detail.

## Testing Plan

### Backend tests

Add tests that verify:

- stats responses include `fill_priority`
- items are sorted in the expected order
- complete slots are excluded
- reason strings are stable and human-readable
- structurally critical slots receive an explanatory label

### Frontend tests or manual verification

Verify that:

- opening Info shows the new section in the correct position
- clicking a recommended slot selects the corresponding word
- closing Info returns the user to the normal clue view with the slot still selected
- the panel remains usable on smaller screens

## Incremental Implementation Steps

1. Finalize the backend ranking output shape.
2. Add fill-priority data to the stats response.
3. Update `renderStatsPanel()` to render the new section.
4. Wire rows to `selectWord(seq, direction)`.
5. Add or update tests for stats payload and UI placement.
6. Tune wording and row count after trying it with a few real puzzles.

## Open Questions

- Should V1 show `candidate_count` exactly, or collapse high counts into `many candidates`?
- Should structural criticality be shown only in the reason text, or also as a small visual badge?
- Should partially filled slots rank above completely blank slots when candidate counts are similar?

My recommendation for V1:

- show exact candidate counts
- show criticality in the reason text only
- prefer partially filled slots only if the ranking logic naturally yields that result

## Bottom Line

For this codebase, the best first UX is not a new panel or a reordered clue list. It is a compact recommendation section inside the existing Info screen.

Placed after `Black cells:` and before the word-length table, it will be easy to discover, easy to implement, and easy to iterate once the ranking quality improves.
