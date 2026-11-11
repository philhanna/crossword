# Permute: swapping two locked words by drag and drop — design doc

## What this adds

In the Puzzle editor, a new **Permute** button on the toolbar turns on a
swap mode. While the mode is on, the user can pick up one **locked** word on
the grid and drop it onto another locked word of the same direction and
length. The two words trade places: each one's letters move into the other's squares, and
each one's clue goes with its letters. Both words are locked before the swap
and still locked after it.

Only locked words can be swapped. An unlocked word can't be picked up and
can't be dropped on.

Example: 14-Across is `OCEAN` with the clue "Big blue expanse", and 30-Across
is `RIVER` with the clue "Flows to the sea". Both are locked. After dragging
14-Across onto 30-Across, 14-Across holds `RIVER` / "Flows to the sea" and
30-Across holds `OCEAN` / "Big blue expanse". Both stay locked.

## Why only locked words

In this app a locked word is the way a puzzle maker marks the words that the
puzzle is built around (the theme answers). There is no separate "theme"
setting; the locked words are the theme words. Theme words
are the ones a puzzle maker most wants to rearrange, because their length and
position are chosen carefully and a theme often works with several different
orderings. Ordinary fill words are easy to retype or replace using the word
editor.

Limiting swaps to locked words also helps in two practical ways:

- **Nothing is picked up by accident.** Most of the grid is ordinary fill.
  Because only locked words react to a drag, and only after the user has
  clicked Permute, a mouse slip while clicking on the grid can never move
  anything.
- **There is never a doubt about which word is meant.** Every square belongs
  to an Across word and a Down word, but usually only one of the two is
  locked. That one is the word that gets picked up (see "How it works for the
  user").

## Today

There is no swap. To get the same result the user has to:

1. Write down both answers and both clues.
2. Unlock the first word, edit it to the second answer, and lock it again.
3. Do the same for the second word.
4. Retype both clues, because changing a word's letters clears its clue.

Each step is saved on its own, so undoing it takes several presses of Undo.

## What counts as a valid swap

A swap is allowed only when all of these are true. If any one fails, nothing
changes and the message line says which rule failed.

1. **Puzzle mode only.** In Grid mode there are no letters to swap.
2. **Both words are locked.** Otherwise the message is "Only locked words can
   be swapped".
3. **Same direction.** Across with Across, or Down with Down. (Swapping an
   Across word with a Down word is left out on purpose; see "Not included".)
4. **Same length.** `OCEAN` can only trade with another five-letter word.
5. **No other locked word would be changed.** Each square of a swapped word
   is also part of a word going the other way. If that crossing word is
   itself locked and the swap would change one of its letters, the swap is
   refused, with a message naming the locked word in the way. This protects
   the rest of the theme: a swap never alters a locked word except the two
   the user chose.
6. **No new duplicates.** The existing no-duplicate-words rule
   ([no_duplicate_words.md](no_duplicate_words.md)) applies. The two swapped
   words can't duplicate each other (they were both already in the puzzle),
   but a crossing word that changes can. If it would now match another word
   in the puzzle, the swap is refused with the same message the word editor
   gives.
7. **The two words must be different words,** and their letters must not be
   identical. Dropping a word on itself, or swapping two words that already
   hold the same letters, does nothing and shows no error.

Incomplete words (ones with blank squares) can be swapped too. Their blanks
move along with the letters. A clue only exists on a complete word, so an
incomplete word simply has no clue to carry.

## Locks during a swap

The app protects a locked word by quietly ignoring any attempt to write a
letter into one of its squares. A swap has to write letters into the two
chosen words, so for the moment of the swap those two words are unlocked, and
straight afterwards they are locked again.

- **Only the two chosen words are unlocked.** Rule 5 guarantees that no other
  locked word is affected, so no other word needs unlocking.
- **The unlock is never visible.** It all happens inside one request, so the
  user never sees a word flicker to unlocked and no other request can slip in
  between.
- **A refused swap relocks too.** If the swap fails partway (for example on a
  duplicate), the words are put back exactly as they were and both are
  locked again. An error can never leave a word unlocked.
- **Locks don't appear in Undo.** Both words have the same lock state before
  and after, so there is nothing about locks to undo. Undo and Redo do their
  own brief unlock and relock of the two words around putting the letters
  back, for the same reason the swap does.

## Clues of crossing words

Every square of a swapped word is also part of a word going the other way.
When the letters in a square change, that crossing word has changed too, so
its old clue may no longer fit. The app already deals with this when the user
edits a word: it clears the clue of any crossing word whose letters changed.
A swap follows the same rule. (These crossing words are always unlocked ones,
because of rule 5.)

What is new is that a swap remembers those cleared clues, so Undo can bring
them back. Today's single-word edit does not do that.

In the example above, each crossing word that touched `OCEAN` or `RIVER` may
lose its clue, unless the letter in that square happens to be the same in
both words. The message after the swap says how many clues were cleared, so
the user is not surprised.

## The Permute button

Swapping is something a puzzle maker will do only now and then, so the grid
does not watch for drags all the time. It only does so after the user asks
for it with a button.

**Where it is.** In the Puzzle-mode toolbar, in the group on the right, as the
first button, so it sits just to the left of **Clear** and **Delete**. It has
the label "Permute" and the standard swap-arrows icon (`swap_horiz`). While
Permute mode is on, the same button reads **Cancel** instead (see below). It
is not shown in Grid mode. The change is in the toolbar markup in
[editor.js](../../frontend/static/js/editor/editor.js) (the block that holds
`puzzle-clear-btn` and `puzzle-delete-btn`), with a new `data-action`
(`puzzle-permute`) registered alongside the others.

**When it can be clicked.** The button is greyed out, with a tooltip saying
why, when:

- the puzzle has no pair of locked words of the same direction and the same
  length (so there is nothing it could swap), or
- the word editor is open (the same condition that greys out Delete).

The first test is worked out in the browser from the puzzle data it already
has, and is re-checked after every redraw, so locking or unlocking a word
updates the button.

**Turning the mode on.** Clicking Permute:

1. Saves any word being typed, just as clicking elsewhere on the grid does.
2. Changes the button's label from "Permute" to "Cancel" and highlights it
   (the same look the active mode buttons have), and changes the pointer to a
   "grab" hand over locked words.
3. Shows a message: "Permute: drag a locked word onto another locked word of
   the same length. Esc to cancel."
4. Starts listening for drags on the grid. Before this point, no drag code is
   attached to the grid at all.

**Turning the mode off.** The mode ends, and the drag code is detached, when:

- a swap is done (one swap per click on Permute; click Permute again for
  another),
- the user clicks the button while it reads "Cancel",
- the user presses Escape (when no drag is under way; during a drag, Escape
  only cancels that drag), or
- the editor changes in a way that redraws everything: switching to Grid
  mode, closing or deleting the puzzle, or opening another one.

Whichever way the mode ends, the button goes back to reading "Permute" and is
enabled again (provided a swappable pair still exists, per "When it can be
clicked"). In particular, after a successful swap the button is immediately
usable for the next one. While the mode is on, the button is always enabled,
since it is the way out.

A refused swap leaves the mode on, so the user can try a different target.

## How it works for the user

**Picking up a word.** With Permute on, the user presses the mouse button on a square of a
locked word and starts moving. Moving a few pixels (about 5) turns the press
into a drag; a shorter movement is still an ordinary click. This keeps the
existing click behavior (single click selects the Across word, double click
the Down word) exactly as it is, in or out of Permute mode. Pressing on a
square that belongs to no locked word never starts a drag.

**Which word is picked up.** The word at the pressed square, in the
direction that is locked:

- If only one of the two words through that square is locked, that one is
  picked up.
- If both are locked (two theme words crossing), the already-selected word is
  picked up if the pressed square is part of it; otherwise the Across word.
  To drag the Down word, the user first selects it with a double click.

Locked squares are already drawn pale yellow, so the user can see what can be
picked up. While Permute is on, the mouse pointer changes to a "grab" hand
over them.

**While dragging.**

- The picked-up word is shaded.
- The locked word under the mouse, in the same direction and of the same
  length, is outlined green. If the word under the mouse is unlocked or has a
  different length, it is outlined red, with a short note near the pointer
  saying why ("Only locked words can be swapped" or "Different length").
- Pressing Escape, or letting go over a black square or off the grid, cancels
  the drag with no change. Permute stays on.

**Dropping.** On a valid target the swap happens, Permute turns itself off,
the grid redraws, and the message line says, for example, "Swapped 14-Across and 30-Across (3 crossing
clues cleared)". No word is left selected, so the user sees the result
plainly. If the server refuses (a duplicate, or a locked crossing word in the
way), the grid is left as it was, the reason is shown, and Permute stays on.

**Undo.** One press of Undo reverses the whole swap: both words' letters, both
clues, and any crossing clues that were cleared. Redo does it again.

## Where it fits in the code

The work is in the usual three layers, plus the web route and the browser
code. Each piece is small.

### 1. The puzzle itself (domain layer)

New method on `Puzzle` in [puzzle.py](../../crossword/domain/puzzle.py),
next to `set_text` and `clear_unlocked`:

`swap_words(seq_a, seq_b, direction)`

It does, in order:

1. Look up both words; raise `ValueError` if either does not exist.
2. Check rules 2, 3 and 4 (both locked, same direction, same length). Check
   rule 7 and return quietly if there is nothing to do.
3. Check rule 5: work out which squares would change, and raise `ValueError`
   naming the locked word if any of them belongs to a locked crossing word.
4. Remember "before" for the two swapped words and every crossing word whose
   letters will change: letters and clue. (Same idea as what
   `clear_unlocked` already records.)
5. Unlock the two swapped words. This is done directly on the words and is
   *not* recorded for Undo, because step 9 puts the locks back.
6. Write each word's letters into the other, and move the clues across.
7. Clear the clue of every crossing word whose letters changed.
8. Run the existing duplicate check (`_check_for_duplicates`, see
   [puzzle.py:125](../../crossword/domain/puzzle.py#L125)). If it finds a
   duplicate, put everything back from the "before" record and remember the
   error to re-raise.
9. Lock the two words again. This runs even when step 8 failed (use a
   `try`/`finally`), so an error can never leave either word unlocked.
10. Re-raise the duplicate error if there was one; otherwise push one entry
    onto the undo stack.

The undo entry is a new kind, `'swap'`. It holds the "before" list from step 4
(`(seq, direction, text, clue)` for each word) plus which two words were
swapped. Undo puts back the saved letters and clues and saves the current ones
on the Redo stack, and Redo does the reverse, in the same way the existing
`'clear'` entry works. The one difference is that Undo and Redo unlock the
two swapped words while writing and lock them again afterwards, as described
in "Locks during a swap". The undo stacks are not stored in the database, so
adding a new entry kind needs no data change.

### 2. The use case (application layer)

New method on `PuzzleUseCases` in
[puzzle_use_cases.py](../../crossword/use_cases/puzzle_use_cases.py):

`swap_words(user_id, name, direction, seq_a, seq_b) -> Puzzle`

It goes through the shared `_edit` helper, like `toggle_circle` does, which
loads the puzzle, runs the change, saves it, and throws away the cached fill
order (letters changed, so the cached order is stale). It refuses in Grid mode
with `ValueError`, matching `toggle_circle`. It adds a row to
[usecases.md](usecases.md).

### 3. The web route (driving side)

One new route in
[puzzle_routes.py](../../crossword/http_server/puzzle_routes.py):

```
POST /api/puzzles/{name}/words/swap
body: { "direction": "across", "seq_a": 14, "seq_b": 30 }
reply: the same full-puzzle reply the other editing routes give
```

It uses the same `puzzle_errors` wrapper as its neighbours, so a refused swap
reaches the browser as the usual `{"error": "..."}` message. The route is
registered before the `/words/{seq}/{direction}` routes so that `swap` is
never mistaken for a word number. [endpoints.md](endpoints.md) is generated,
so it is regenerated, not hand-edited.

### 4. The browser

A new file, `frontend/static/js/editor/word-drag.js`, in the `editor/` folder
with its neighbours. It keeps all the drag logic in one place so the click
code stays simple.

- **Nothing runs until Permute is on.** `word-drag.js` exports a function that
  attaches the drag listeners to the grid and another that removes them. The
  Permute button's action calls the first; the ways of leaving the mode
  (listed above) call the second. The grid is redrawn from scratch whenever
  the puzzle changes, which discards its old listeners, so the redraw code in
  [editor.js:134](../../frontend/static/js/editor/editor.js#L134) re-attaches
  them only if a small "Permute is on" flag is set. When the flag is off the
  file does nothing at all.
- **Events.** Uses pointer events (`pointerdown`, `pointermove`, `pointerup`,
  `pointercancel`) rather than the older mouse events, so touch screens and
  pens work too. The grid is given `touch-action: none`, only while Permute is on, so a finger drag
  doesn't scroll the page.
- **Only locked words start a drag.** Each word in the puzzle data the browser
  already has carries its `locked` flag, so on `pointerdown` the code can tell
  at once whether the square is part of a locked word. If not, it does
  nothing and the normal click handling carries on untouched.
- **Hand-off with clicks.** The existing click code waits 280 ms to tell a
  single click from a double click
  ([grid-clicks.js](../../frontend/static/js/editor/grid-clicks.js)). Once a
  press becomes a drag, the drag code cancels any waiting click and swallows
  the click the browser sends after the button is released. Otherwise every
  drop would also select a word.
- **Open word editor.** If the word editor is open, or the selected word has
  unsaved typing, it is saved first with the same
  `completeSelectedWordEdit()` call that clicking elsewhere already uses.
  Otherwise the unsaved text would be lost when the grid redraws after the
  swap.
- **Drawing the feedback.** The grid is an SVG redrawn from the puzzle data
  ([grid-svg.js](../../frontend/static/js/svg/grid-svg.js)). The shading and
  outlines are drawn as a thin extra layer on top, not by redrawing the grid
  on every mouse movement. The layer is removed on drop or cancel.
- **Checking before asking.** The browser applies the cheap rules (locked,
  same direction, same length) itself to decide green or red. It does *not*
  try to check duplicates or locked crossing words; the server owns those,
  and its message is shown if it says no. This avoids two copies of the same
  rules drifting apart.
- **After the drop.** Sends the request, replaces the puzzle data with the
  reply, redraws, and shows the message. On an error, shows the error and
  leaves the grid as it was.

## Things to decide before building

1. **Dragging from the clue list too.** The Clues tab already lists every
   word with its answer and clue. Dragging one row onto another would be a
   natural second way to swap, and it avoids the "which word at this square"
   question completely. It is not in this first version, but the server
   route is the same, so adding it later is only browser work. Worth doing?
2. **A way to swap without a mouse.** Drag and drop can't be done from the
   keyboard. A possible later addition is "mark this word, move to another,
   press a key to swap". Not included now; flagging it so it is a choice
   rather than an oversight.
3. **Message wording for cleared clues.** The count is useful but may be
   noisy when it is 0. Proposal: only mention clues when at least one was
   cleared.

## Not included

- Swapping an unlocked word, or a locked word with an unlocked one. (To
  rearrange ordinary fill, use the word editor.)
- Swapping an Across word with a Down word. They can have the same length,
  but they cross each other somewhere, so the swap would write into its own
  squares and the result is hard to explain. Refused for now.
- Swapping words of different lengths, or moving a word to an empty slot.
- Any change to saved data. A swap only changes letters and clues that
  already exist, so no database change is needed.

## Tests

Following the project's usual layout under `crossword/tests/`:

**Puzzle (pytest, no browser or server):**
- A plain swap of two locked words moves both words' letters and both clues.
- Both words are still locked afterwards.
- Swapping two words and then swapping them again gives back the original.
- Crossing clues are cleared only where the letter really changed.
- Refused, with the puzzle left exactly as it was: either word unlocked,
  different lengths, a different direction, and a locked crossing word that
  would change.
- A word swapped with itself, and two words with identical letters, do
  nothing and raise no error.
- A swap that would create a duplicate is refused, the puzzle is exactly as
  it was, and both words are still locked.
- One Undo restores letters, clues, and the cleared crossing clues, and both
  words are still locked; Redo repeats the swap.
- Incomplete words swap and carry no clue.

**Use case and route:** the success path, the Grid-mode refusal, an unknown
word number, an unlocked word, and that a refused swap comes back as
`{"error": ...}`.

**Browser (Playwright, in `crossword/tests/frontend/`):**
- Before Permute is clicked, pressing and dragging on a locked word does
  nothing but select it, as today.
- Permute is greyed out when there is no swappable pair, and enabled once
  two same-length locked words exist.
- Clicking Permute highlights it and changes its label to "Cancel";
  clicking it again, or pressing Escape, turns the mode off and restores the
  label "Permute".
- With Permute on, dragging one locked word onto another swaps them, shows
  the message, turns the mode off, and the button reads "Permute" and is
  enabled again.
- Pressing and dragging on an unlocked word does nothing (and a plain click
  on it still selects it).
- A short press-and-release on a locked word is still an ordinary click.
- Dropping on an unlocked or wrong-length word shows red and changes
  nothing, and Permute stays on.
- Escape during a drag cancels the drag only; a second Escape ends Permute.
- Switching to Grid mode while Permute is on ends it.
- Undo after a drop restores the original grid.

## Docs to update when it is built

- [usecases.md](usecases.md): the new `swap_words` row.
- [endpoints.md](endpoints.md): regenerate (the `sync-docs` skill does this).
- [frontend.md](frontend.md): add `word-drag.js` to the `editor/` folder list,
  describe the Permute button and mode, and the click/drag hand-off.

## Suggested order of work

1. `Puzzle.swap_words` and its undo handling, with the puzzle tests.
2. Use case and route, with their tests.
3. The Permute button and mode, then the browser drag code and feedback,
   with the Playwright tests.
4. Docs.

Steps 1 and 2 can be used and checked by hand (for example with the `/docs`
page) before any browser code exists.
