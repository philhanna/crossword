# Word Locking + Bulk Clear — design (decisions resolved, ready for implementation)

## 1. Purpose

Two related features for the puzzle editor:

1. **Lock word** — a checkbox in the word editor panel that, when checked,
   prevents that word's letters from being overwritten, whether by typing
   in the word editor, by editing a crossing word, or by undo/redo.
2. **Clear** — a toolbar button in the puzzle editor that blanks the text
   and clue of every word that is *not* locked, after an "Are you sure?"
   confirmation, leaving locked words untouched. This builds on the
   existing rule from `set_word_clue` (see
   [puzzle_use_cases.py:461](../../crossword/use_cases/puzzle_use_cases.py#L461))
   that a word's clue is cleared whenever its text is incomplete.

Both features assume the puzzle is mid-construction and the constructor
wants to protect work that's already finished (e.g. an entry confirmed
against a dictionary, or a themed entry that must not be auto-changed)
while bulk-clearing or continuing to edit the rest.

## 2. Current behavior (for contrast)

- Letters are stored per-cell on `Puzzle.cells`, keyed by `(r, c)`
  ([puzzle.py:29](../../crossword/domain/puzzle.py#L29)), not per-word.
  Across and down words that cross each other **share** the same cell
  entries.
- `Puzzle.set_text(seq, direction, text, undo=True)`
  ([puzzle.py:95](../../crossword/domain/puzzle.py#L95)) is the only write
  path for word text. It pushes `['text', seq, direction, old_text]` onto
  `puzzle.undo_stack` and then calls `word.set_text(text)`, which writes
  each cell in the word's `cell_iterator()` unconditionally.
- `Puzzle.undo()` / `Puzzle.redo()`
  ([puzzle.py:235](../../crossword/domain/puzzle.py#L235)) replay a popped
  `['text', seq, direction, old_text]` entry through the same
  `set_text(..., undo=False)` path — so undo/redo and direct typing funnel
  through identical, unconditional cell writes.
- Crucially, an edit to word A can silently overwrite cells that belong to
  a crossing word B, since they're the same `(r, c)` entries. There is no
  existing concept of read-only cells.

This last point is the central design problem: **a per-word lock flag is
not sufficient by itself** — it must protect the underlying *cells*, or a
lock on word A can still be defeated by editing word B.

## 3. Resolved decisions

1. **Locking is a property of a word, not a derived cell mask.** Each
   `Word` gets a `locked: bool` attribute (default `False`), set via
   `Word.set_locked(bool)` / read via `Word.is_locked()`, mirroring the
   existing `get_clue()`/`set_clue()` pair.
2. **Enforcement happens at the cell level, in one place.** `Puzzle`
   computes the set of cells covered by any locked word
   (`Puzzle.locked_cells` — a `set[(r, c)]` property, analogous to the
   existing `black_cells` property) and `Puzzle.set_cell(r, c, letter)`
   refuses to write to a cell in that set. Every write path —
   `word.set_text()` (direct typing), undo, and redo — already funnels
   through `Puzzle.set_cell`, so this one guard covers all three cases,
   including the cross-word case from §2 (editing word B is silently a
   no-op for any cell it shares with locked word A).
3. **Locking a word is itself an undoable action**, tracked the same way
   text changes are: a new undo-stack entry type, `['locked', seq,
   direction, old_value]`, pushed by `Puzzle.set_locked(seq, direction,
   value)`. This keeps "lock" and "unlock" inside the existing Ctrl+Z
   flow instead of being a separate, un-undoable side channel.
4. **An incomplete word can be locked.** Locking only stops further
   writes to its cells; it does not require the word to be filled first.
   (This matters for themed entries the constructor wants to "freeze" as
   a pattern before the rest of the grid is filled in.)
5. **The "Clear" button clears text and clue together**, reusing the
   existing rule that an incomplete word's clue is meaningless
   ([puzzle_use_cases.py:461](../../crossword/use_cases/puzzle_use_cases.py#L461)).
   Locked words (text *and* clue) are skipped entirely — not even their
   clue is cleared, since a locked word is being treated as finished.
6. **Clear is a single undo entry, not N entries.** Clearing 30 words one
   at a time would bury the user's prior undo history under 30 stack
   frames. Instead, `Puzzle.clear_unlocked()` pushes one
   `['clear', [(seq, direction, old_text, old_clue), ...]]` entry covering
   every word it actually changed, so a single Undo reverts the whole
   Clear.
7. **The confirmation dialog reuses `messageBox()`**
   ([ui.js:86](../../frontend/static/js/ui.js#L86)), the same helper used
   for puzzle delete ([puzzle-editor.js:1280](../../frontend/static/js/puzzle-editor.js#L1280)) — no new dialog component.
8. **Locked words get a light-blue background on the grid itself**, not
   just a checkbox state hidden inside the word editor. Every cell
   belonging to a locked word (`puzzle.locked_cells`, decision 2) is
   rendered with a distinct light-blue fill in the SVG, so locked state is
   visible without opening the word editor (§6.2).
9. **Grid typing on a locked word is refused locally**, not silently
   swallowed server-side. `_peKeydown` checks `sw.locked` and ignores
   letter/space/Delete/Backspace keys when the selected word is locked.
   Selection and navigation (arrows, Tab, clicking the word) are
   unaffected, and **"Edit word" still opens the word editor for a locked
   word** so the lock can be reviewed and unchecked there (§7.2).
10. **Locking a word only protects its answer text, not its clue.** The
    Clue field in the word editor stays editable while "Lock word" is
    checked; only the Answer field (and the suggestion/constraints tools
    that exist to help fill the answer) are disabled (§6.1).
11. **The Clear confirmation dialog shows counts** — "N words will be
    cleared. M locked words will be skipped." — computed client-side from
    the `locked` field already present on every word in `AppState.puzzleData`
    (decision/§5.3), with no extra API call needed (§6.3).
12. **Switching to Grid Mode is disabled while any word in the puzzle is
    locked.** Grid edits (rotate, regenerate, toggle black cell) change
    cell geometry and recompute words from scratch
    ([puzzle.py:403](../../crossword/domain/puzzle.py#L403)), which has no
    well-defined meaning for a word that's supposed to be frozen. Rather
    than design what a locked word "survives" a grid change as, grid mode
    is simply unreachable until every word is unlocked (§6.4). This is a
    **frontend-only guard** — the backend grid-mutation paths
    (`toggle_black_cell`, `rotate_grid`, `apply_generated_grid`) are left
    as-is, with no server-side re-check of `locked_cells`. The UI is the
    only route to those calls today, so the extra defensive check isn't
    worth the complexity.

## 4. Data model changes

### 4.1 `Word` ([word.py](../../crossword/domain/word.py))

```python
def __init__(self, puzzle, seq):
    ...
    self.locked = False

def is_locked(self):
    return self.locked

def set_locked(self, locked):
    self.locked = locked
```

### 4.2 `Puzzle` ([puzzle.py](../../crossword/domain/puzzle.py))

```python
@property
def locked_cells(self):
    """ Cells covered by any locked word """
    cells = set()
    for word in list(self.across_words.values()) + list(self.down_words.values()):
        if word.is_locked():
            cells.update(word.cell_iterator())
    return cells

def set_cell(self, r, c, letter):
    if (r, c) in self.locked_cells:
        return  # silently a no-op; callers don't need a special case
    self.cells[(r, c)] = letter

def set_locked(self, seq, direction, value):
    word = self.get_word(seq, direction)
    old_value = word.is_locked()
    if old_value != value:
        self.undo_stack.append(['locked', seq, direction, old_value])
    word.set_locked(value)

def clear_unlocked(self):
    """ Blanks text+clue for every unlocked word; returns True if anything changed """
    changes = []
    for word in list(self.across_words.values()) + list(self.down_words.values()):
        if word.is_locked():
            continue
        old_text, old_clue = word.get_text(), word.get_clue()
        blank = " " * word.length
        if old_text != blank or old_clue:
            changes.append((word.seq, word.direction, old_text, old_clue))
            word.set_text(blank)
            word.set_clue(None)
    if changes:
        self.undo_stack.append(['clear', changes])
    return bool(changes)
```

`undo()` / `redo()` gain a branch for `'locked'` (toggle back, push the
inverse) and `'clear'` (restore each `(seq, direction, old_text,
old_clue)` triple, push a `'clear'` entry of the *current* values onto the
opposite stack so the clear itself is redoable).

### 4.3 Serialization (`to_json` / `from_json`)

Each entry in `across_words` / `down_words` in `to_json()`
([puzzle.py:289](../../crossword/domain/puzzle.py#L289)) gains a `"locked"`
key alongside the existing `"text"`/`"clue"`, and `from_json()`
([puzzle.py:332](../../crossword/domain/puzzle.py#L332)) restores it via
`word.set_locked(...)`. This is a backward-compatible additive field —
existing saved puzzles simply default every word's `locked` to `False`.

## 5. Backend API changes

### 5.1 Extend the existing word-update endpoint

`PUT /api/puzzles/{name}/words/{seq}/{direction}`
([puzzle_handlers.py:646](../../crossword/http_server/puzzle_handlers.py#L646))
already accepts an optional `text` alongside `clue`. It gains a third
optional field:

```
Body: { "clue": "...", "text": "...", "locked": true }
```

`handle_set_word_clue` passes `locked` through to
`PuzzleUseCases.set_word_clue`, which — if `locked is not None` — calls
`puzzle.set_locked(seq, direction, locked)` before saving. This keeps the
one-PUT-per-Apply pattern the word editor already uses for text+clue.

### 5.2 New endpoint for Clear

```
POST /api/puzzles/{name}/clear
```

New handler `handle_clear_puzzle` in `puzzle_handlers.py`, new use case
`PuzzleUseCases.clear_unlocked(user_id, name)` that loads the puzzle,
calls `puzzle.clear_unlocked()`, saves if it returned `True`, and returns
the standard `_puzzle_response(puzzle)` (so the response shape matches
every other mutating puzzle endpoint, e.g. undo/redo).

### 5.3 `_puzzle_response` gains a `locked` field per word

[puzzle_handlers.py:49](../../crossword/http_server/puzzle_handlers.py#L49)
adds `"locked": word.is_locked()` to each entry in the `words` list it
builds, so the frontend always knows lock state without a separate fetch.

## 6. Frontend changes

### 6.1 Word editor panel — "Lock word" checkbox

`renderWordEditorPanel()`
([word-editor.js:444](../../frontend/static/js/word-editor.js#L444)) gains
a checkbox row immediately under the header, above the Answer field.
Checking it:

- Disables the Answer input and the Suggestions/Constraints/Definitions
  tools (mirrors how `defsDisabled` already conditionally disables the
  Definitions button at
  [word-editor.js:450](../../frontend/static/js/word-editor.js#L450)) —
  all of these exist only to help fill in the answer, which a locked word
  no longer needs. The **Clue input stays enabled** (decision 10): a
  locked word can still have its clue edited and re-applied.
- Is tracked as `sw.draftLocked` / `sw.originalLocked` on the selected-word
  object, the same dirty-tracking pattern already used for
  `draftText`/`originalText` and `draftClue`/`originalClue`
  ([word-editor.js:71](../../frontend/static/js/word-editor.js#L71)). A
  change to `draftLocked` alone is enough to make
  `_selectedWordHasChanges()` return `true` so Apply sends the PUT.
- On Apply, `completeSelectedWordEdit()` includes `locked:
  sw.draftLocked` in the PUT body alongside `text`/`clue`.
- **Locking a word with an incomplete answer is allowed** (decision 4) —
  no validation blocks it.

#### Mockup — unlocked word (current behavior, unchanged below the new checkbox)

```
┌───────────────────────────────────────┐
│ 14 Across                           × │  ← we-header
│ 5 letters                             │
├───────────────────────────────────────┤
│ ☐ Lock word                           │  ← NEW: we-lock-row
│                                       │
│ Answer                                │
│ ┌───────────────────────────────────┐ │
│ │ S.A.M.B.A                         │ │
│ └───────────────────────────────────┘ │
│                                       │
│ Clue                                  │
│ ┌───────────────────────────────────┐ │
│ │ Brazilian dance                   │ │
│ └───────────────────────────────────┘ │
│                                       │
│ Suggestions  ☑ Constrained  [Suggest] │
│                                       │
│ [Constraints]      [Definitions]      │
│                                       │
│        [ Apply ]      [ Cancel ]      │
└───────────────────────────────────────┘
```

#### Mockup — locked word (inputs disabled, greyed)

```
┌───────────────────────────────────────┐
│ 14 Across                           × │
│ 5 letters                             │
├───────────────────────────────────────┤
│ ☑ Lock word                           │  ← checked
│                                       │
│ Answer                                │
│ ┌───────────────────────────────────┐ │
│ │ SAMBA                       (lock)│ │  ← disabled, greyed
│ └───────────────────────────────────┘ │
│                                       │
│ Clue                                  │
│ ┌───────────────────────────────────┐ │
│ │ Brazilian dance                   │ │  ← still editable
│ └───────────────────────────────────┘ │
│                                       │
│ Suggestions  ☑ Constrained  [Suggest] │  ← Suggest disabled
│                                       │
│ [Constraints]      [Definitions]      │  ← both disabled
│                                       │
│        [ Apply ]      [ Cancel ]      │
└───────────────────────────────────────┘
```

`(lock)` above is a placeholder for a small lock glyph
(`<i class="material-icons">lock</i>`, consistent with the icon usage
already in the action bar) shown at the right edge of the disabled Answer
input, not literal text. The Clue field deliberately has no such
decoration — it isn't disabled.

### 6.2 Puzzle SVG — light-blue background for locked words

Per decision 8, every cell belonging to a locked word gets a distinct
light-blue fill so locked state is visible on the grid without opening
the word editor. `buildPuzzleSvg()` ([svg.js](../../frontend/static/js/svg.js))
already computes per-cell styling (black cells, the selected word's
highlight, the cursor cell); it gains one more layer underneath those:
for every `(r, c)` in `puzzle.locked_cells` (passed through in the
`_puzzle_response` payload as the per-word `locked` flag, decision/§5.3),
paint the cell background a light blue (e.g. `#eaf3ff`, matching the
`we-suggestion-list` hover/selected tones already in
[style.css](../../frontend/static/css/style.css#L835)) before drawing the
letter and any selection highlight on top. A cell belonging to two locked
crossing words is still just one light-blue cell — no special handling
needed since the fill isn't additive.

### 6.3 Puzzle editor toolbar — "Clear" button

`renderActionBar()`
([puzzle-editor.js:142](../../frontend/static/js/puzzle-editor.js#L142))
gets a new button in the puzzle-mode `ab-group` that already holds
Delete/Edit word/Fill order/Stats:

```html
<button id="puzzle-clear-btn" class="ab-btn" onclick="do_puzzle_clear()">
  <i class="material-icons">clear_all</i><span>Clear</span>
</button>
```

`do_puzzle_clear()` (new, in `puzzle-editor.js`) follows the exact pattern
of `do_puzzle_delete_current()`
([puzzle-editor.js:1271](../../frontend/static/js/puzzle-editor.js#L1271)):

```js
async function do_puzzle_clear() {
    if (_isWordEditorOpen()) return;
    const words = AppState.puzzleData.puzzle.words;
    const lockedCount   = words.filter(w => w.locked).length;
    const clearableCount = words.length - lockedCount;
    const lockedNote = lockedCount > 0
        ? ` ${lockedCount} locked word${lockedCount === 1 ? '' : 's'} will be skipped.`
        : '';
    messageBox(
        'Clear puzzle',
        `${clearableCount} word${clearableCount === 1 ? '' : 's'} will be cleared.${lockedNote}`,
        null,
        async () => {
            try {
                const data = await apiFetch('POST',
                    `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/clear`);
                if (data.error) { showMessageLine(`Error clearing puzzle: ${data.error}`, 'error', 0); return; }
                AppState.puzzleData = data;
                renderPuzzleEditor();
            } catch (e) { showMessageLine('Error clearing puzzle', 'error', 0); }
        }
    );
}
```

### 6.4 Grid Mode toggle disabled while any word is locked

Per decision 12, switching to Grid Mode is unavailable whenever the
puzzle has at least one locked word. `renderActionBar()`
([puzzle-editor.js:100](../../frontend/static/js/puzzle-editor.js#L100))
computes `const hasLockedWords = pd.puzzle.words.some(w => w.locked)` and
adds a disabled state to the `Grid Mode` button
([puzzle-editor.js:139](../../frontend/static/js/puzzle-editor.js#L139)),
the same way `genDisabled` already conditionally disables the Generate
button at [puzzle-editor.js:114](../../frontend/static/js/puzzle-editor.js#L114).
`do_switch_to_grid_mode()` ([puzzle-editor.js:658](../../frontend/static/js/puzzle-editor.js#L658))
gets the matching guard so the transition can't be triggered by any other
path either (keyboard shortcut, stale UI, etc.) — mirroring how
`do_puzzle_edit_word()` already guards on editor mode at the top of the
function. A disabled-button tooltip/title attribute explains why (e.g.
"Unlock all words before switching to Grid Mode").
