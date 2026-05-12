# Cache Fill Order Plan

## Goal

Avoid re-fetching `GET /api/puzzles/{wn}/fill-order` from the server when the
result would be identical to the one already in `AppState._fillOrderData`.

The fill order is computed purely from constraint density — how many cells in
each word slot are already filled by crossing words — so it depends only on
word texts. The cache is therefore valid for as long as no word's text has
changed since the last fetch.

## Current State

`AppState._fillOrderData` is already used as a cache, but it is discarded
unconditionally in several places even when word texts have not changed:

| Site | Function | Reason to null |
|---|---|---|
| [puzzle-editor.js:517](frontend/static/js/puzzle-editor.js#L517) | `_puzzleUndoRedo` | over-aggressive — texts may not have changed |
| [puzzle-editor.js:560](frontend/static/js/puzzle-editor.js#L560) | `_switchToGridModeConfirmed` | grid structure changing — correct |
| [puzzle-editor.js:588](frontend/static/js/puzzle-editor.js#L588) | `do_switch_to_puzzle_mode` | grid may have changed — correct |
| [puzzle-editor.js:650](frontend/static/js/puzzle-editor.js#L650) | `_openPuzzleInEditor` | different puzzle — correct |
| [puzzle-editor.js:954](frontend/static/js/puzzle-editor.js#L954) | `_doPuzzleCloseConfirmed` | no puzzle — correct |

The cache is populated in two places:

- [puzzle-editor.js:425](frontend/static/js/puzzle-editor.js#L425) — `_refreshFillOrderIfVisible` (always re-fetches; no validity check)
- [puzzle-editor.js:1026](frontend/static/js/puzzle-editor.js#L1026) — `do_puzzle_fill_order` (always fetches on demand)

## Desired Model

Store a word-text fingerprint alongside `_fillOrderData`. When the fingerprint
of the current puzzle matches the stored one, the cache is still valid and no
fetch is needed. Only when a word text has changed (or a structural event has
occurred) is the cache discarded.

## Changes

### 1. New AppState field — `state.js`

Add `_fillOrderCellHash: null` next to `_fillOrderData`:

```js
_fillOrderData: null,       // cached fill-order response
_fillOrderCellHash: null,   // word-text fingerprint at time of last fetch
```

### 2. New helper `_wordTextsKey` — `puzzle-editor.js`

Returns a deterministic string that changes if and only if any word's text
changes. No cryptographic hash is needed; the string itself is the fingerprint.

```js
function _wordTextsKey(puzzleData) {
    if (!puzzleData?.puzzle?.words) return '';
    return puzzleData.puzzle.words
        .map(w => `${w.seq}${w.direction}:${w.text ?? ''}`)
        .join('|');
}
```

Place this near the other small helpers at the top of the fill-order section,
above `renderFillOrderPanel`.

### 3. Record the hash when fill order is cached

In both `_refreshFillOrderIfVisible` (line 425) and `do_puzzle_fill_order`
(line 1026), immediately after `AppState._fillOrderData = data`, add:

```js
AppState._fillOrderCellHash = _wordTextsKey(AppState.puzzleData);
```

### 4. New helper `_invalidateFillOrderIfChanged` — `puzzle-editor.js`

```js
function _invalidateFillOrderIfChanged(newPuzzleData) {
    if (AppState._fillOrderData &&
            _wordTextsKey(newPuzzleData) !== AppState._fillOrderCellHash) {
        AppState._fillOrderData   = null;
        AppState._fillOrderCellHash = null;
    }
}
```

### 5. Replace the blanket null in `_puzzleUndoRedo` (line 517)

`data` is the new puzzle state returned by the API. Replace:

```js
AppState._fillOrderData   = null;
```

with:

```js
_invalidateFillOrderIfChanged(data);
```

Call this **before** `AppState.puzzleData = data` so the helper receives the
incoming data (not the old state) as its argument.

### 6. Pair `_fillOrderCellHash = null` with the four remaining blanket nulls

Lines 560, 588, 650, and 954 each set `AppState._fillOrderData = null`
unconditionally (correct). Add `AppState._fillOrderCellHash = null;` on the
line immediately after each of those four assignments.

### 7. Short-circuit `_refreshFillOrderIfVisible` when cache is still valid

```js
async function _refreshFillOrderIfVisible() {
    if (AppState.sidebarTab !== 'fill-order' ||
            !AppState.puzzleWorkingName ||
            _currentEditorMode() !== 'puzzle') return;
    if (AppState._fillOrderData &&
            _wordTextsKey(AppState.puzzleData) === AppState._fillOrderCellHash) {
        renderPuzzleEditorRhs();
        return;
    }
    // ... existing fetch logic unchanged ...
}
```

## Files Changed

| File | Change |
|---|---|
| [frontend/static/js/state.js](frontend/static/js/state.js) | add `_fillOrderCellHash: null` |
| [frontend/static/js/puzzle-editor.js](frontend/static/js/puzzle-editor.js) | add `_wordTextsKey`, `_invalidateFillOrderIfChanged`; update 2 cache-store sites; replace 1 blanket null with conditional; add 4 paired hash clears; short-circuit `_refreshFillOrderIfVisible` |

## Manual Checks

1. Open a puzzle and click **Fill Order**. Verify it loads.
2. Undo a word-text change, then redo it (restoring the original text). Switch
   back to the Fill Order tab. Verify no network request is made to
   `/fill-order` — the cached panel reappears immediately.
3. Type a letter in a word slot. Switch to the Fill Order tab. Verify a fresh
   fetch occurs (the word text changed).
4. Undo a grid-mode change (toggle a black cell, then undo). Verify the fill
   order cache is discarded on mode switch.
5. Close and reopen a puzzle. Verify the fill order panel is empty until
   explicitly requested.
