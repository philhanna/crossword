# Autofill — design doc

## Status

Implemented. The code is in
[autofill_use_cases.py](../../crossword/use_cases/autofill_use_cases.py), with
`Puzzle.apply_fill` in [puzzle.py](../../crossword/domain/puzzle.py), the
`POST /api/puzzles/{name}/autofill` route, and an Autofill button in the
editor toolbar. Where the result differs from the plan below:

- **The search starts over when it gets stuck.** If it has tried 500 words
  without finishing, it throws its work away and starts again in a new random
  order, allowing twice as many tries each time, until the time limit. This
  rescues runs that made a bad early choice and then spent the whole time
  digging around its consequences. Without it, a hard 15×15 grid could eat
  the full 10 seconds.
- **Word lookup is faster than first planned.** Rather than first measuring,
  the "which words have letter X in position N" lookup from *Speed notes* was
  built from the start: for each word length, each (position, letter) pair is
  stored as one big number whose bits mark the matching words, and combining
  constraints is a single "and".
- **Failure messages tell three cases apart:** a slot with no possible words
  from the start ("No words fit 7-Across as it stands"), a search that ran
  out of time ("No fill found in 10 seconds"), and a search that tried every
  possibility ("No fill is possible with this word list and the words already
  placed"). Each names the hardest spot where it can.
- **A locked word with blanks** is reported up front, since autofill is not
  allowed to touch locked words but the puzzle can't be filled while one has
  blanks.
- **The random seed is not shown in the error message.** The use case accepts
  one (so tests are repeatable) but the web route doesn't expose it yet.
- The undo entry is `['autofill', [(seq, direction, text), ...]]`; undo and
  redo swap the stored texts with the current ones.

Rough timing on a 368,000-word list: most 11×11 to 15×15 grids from the
random grid generator fill in under a second; a minority take the whole
10 seconds and give up.

## The problem this solves

Filling a grid by hand is the slow part of building a crossword. You place a
few words you care about (the theme words, say), and then have to find
words for everything else — each one fitting the letters already crossing
it, and none repeating another. Today the app helps with one slot at a time:
the word editor lists suggestions for the slot you are in, and the
fill-priority panel points out which empty slot to deal with next
([fill_priority.py](../../crossword/domain/fill_priority.py)). You still have
to pick, type, and often back up when two choices turn out to be
incompatible.

**Autofill** does the whole job in one click: it fills every incomplete word
in the puzzle with words from the word list, or tells you plainly that it
couldn't.

## What the user sees

- A new **Autofill** command in the Puzzle editor (Puzzle mode only; the
  grid shape can't change during a fill).
- Click it and the app works for a few seconds, then one of two things
  happens:
  - **It succeeded.** Every blank is filled. The puzzle looks as if you had
    typed all those words yourself, and a single **Undo** takes all of them
    back out again.
  - **It failed.** The puzzle is left exactly as it was, and a message says
    why, for example: *"No fill found in 10 seconds. The hardest spot was
    14-Down (pattern `C.T..R`, 3 candidates)."* Nothing half-filled is ever
    left behind.
- Clicking Autofill again after a success is not needed; clicking it again
  after a failure tries again with a different random order, which often
  succeeds where the first try didn't. (Clear a few words around the stuck
  spot yourself if it keeps failing.)

## Ground rules

These keep autofill from ever doing something the user wouldn't have done
by hand.

1. **Words that are already complete are never changed.** This includes
   unlocked ones. Autofill only adds; it does not second-guess what is
   there. (A "re-fill everything unlocked" option could be added later — see
   *Not in the first version*.)
2. **Letters already in a partly filled word stay.** A slot showing `C _ T`
   is treated as the search pattern `C.T`; only the blanks change.
3. **Locked words are never touched.** Locked words are the theme words (see
   the theme-words note in the project notes), so this is the same as
   "autofill works around your theme."
4. **No repeated words and no near-repeats.** The same check used when
   typing a word is used here, so a fill can't contain both CAT and CATS
   ([no_duplicate_words.md](no_duplicate_words.md)). Words already in the
   puzzle count too, not just words autofill adds.
5. **Clues are left alone.** Autofill fills letters only.
6. **All or nothing.** The fill is applied only when every slot has a word.

## How it works, in plain terms

Think of it as solving the puzzle the way a careful person would, but much
faster:

1. **Pick the hardest empty slot first** — the one with the fewest words
   that could possibly fit. (The app already knows how to count these; it
   is what the fill-priority panel uses.) Doing the hardest slot first
   means dead ends show up early, when they are cheap to back out of.
2. **Try a word in it.** Candidates are the word-list words matching the
   letters already there, in a random order so repeated attempts differ.
3. **Check the damage immediately.** After placing the word, every slot that
   crosses it has new letters. If any of those slots now has *zero* words
   that fit, this choice is a dead end — don't go further, take the word
   back out and try the next candidate.
4. **Otherwise, go back to step 1** with the slot that is now hardest.
5. **If every candidate for a slot fails,** back up to the previous slot and
   try its next candidate. This "back up and try something else" is the only
   way a fill that looks fine at first can be corrected.
6. **Stop** when every slot is filled (success) or when time runs out
   (failure).

The check in step 3 is what makes this practical. Without it, the search
would happily place ten words before discovering the first one made some
far-off slot impossible.

### Work on a scratch copy

The search places and removes words thousands of times. Doing that to the
real puzzle would fill the undo history with junk and be slow. So autofill:

1. Copies the current letters into a plain scratch grid.
2. Searches on the scratch grid.
3. If it succeeds, writes the finished words into the real puzzle in one
   go, as one undo step.

If the search fails, the real puzzle was never touched, which is how
"all or nothing" is guaranteed.

### Time limit

Some grids simply cannot be filled from a given word list, and the search
can't always tell quickly. So there is a cap: **10 seconds** by default
(adjustable later). When the cap is hit the search gives up and reports
failure. The cap is a plain time check inside the search loop — no extra
threads or background jobs in the first version.

### Speed notes

The word list already stores words grouped by length and remembers the
answer to repeated identical searches
([flat_file_word_list_adapter.py](../../crossword/adapters/flat_file_word_list_adapter.py)).
That is enough to start with. If real grids prove too slow, the obvious
next step is a dedicated lookup that, for each (length, position, letter)
combination, keeps the set of words having that letter there; intersecting
those sets avoids the pattern-matching step entirely. We will measure
before building it.

## Where the code goes

This follows the existing ports-and-adapters layout; nothing new is needed
on the adapter side because the word list port already does what we need.

| Layer | New / changed | Job |
|---|---|---|
| Use case | `crossword/use_cases/autofill_use_cases.py` — `AutofillUseCases` | Runs the search and applies the result. Needs a `WordListPort` and the puzzle. |
| Domain | `Puzzle.apply_fill(fills)` in [puzzle.py](../../crossword/domain/puzzle.py) | Writes a batch of words as **one** undo step. Modeled on `clear_unlocked`, which already records a many-words change as a single undo entry. |
| Use case | `PuzzleUseCases.autofill(user_id, name)` | Finds the working copy, calls `AutofillUseCases`, saves the result. Same pattern as the other edit methods. |
| HTTP | `POST /api/puzzles/{name}/autofill` in `puzzle_routes.py` | Returns the updated puzzle on success, or an error message in the usual `{"error": "..."}` shape. |
| Frontend | A button/menu item in the editor, plus a "working…" state | Calls the endpoint and redraws, like other edits. |
| Wiring | [wiring/__init__.py](../../crossword/wiring/__init__.py) | Builds `AutofillUseCases` with the shared word list. |
| Docs | `docs/dev/usecases.md`, `endpoints.md` | Add the new method; regenerate the endpoint list (don't hand-edit it). |

`AutofillUseCases` follows the same rule as the other use cases: it may use
the domain and the ports, and nothing else.

### The undo step

`Puzzle.undo_stack` holds one entry per user action. Autofill adds a single
entry of a new kind (for example `['autofill', [(seq, direction, old_text),
...]]`), and `undo()` / `redo()` learn to handle it, the same way they
already handle `'clear'` and swaps. Undoing restores every word autofill
changed; redoing puts them back.

### Duplicates during the search

Calling the normal "set text" path for every trial word would run the
duplicate check each time and record undo entries. Instead the search keeps
its own set of words used so far and checks each candidate against it with
the same near-duplicate function (`find_duplicate`) the rest of the app uses.
Only the final write goes through the puzzle.

## What can go wrong

- **The word list is too small or too odd** for the grid. A dense grid with
  many long crossing words needs a large list. The failure message names
  the stuck slot so the user can see where the pressure is.
- **The existing fill makes the grid impossible.** For example, a locked
  word forces a pattern no word matches. Autofill fails quickly in this
  case, since that slot has zero candidates from the start; the message
  should say so ("no words fit 7-Across as it stands") rather than "timed
  out".
- **Slow on large grids.** Mostly-empty 21×21 grids are the hard case. The
  time limit protects the user from waiting forever, and a progress or
  cancel button is listed below as a later improvement.
- **Word quality.** The word list is just a list — it has no notion of
  which words are common or good. Autofill may fill with legal but obscure
  words (and will do so in random order). See below.

## Not in the first version

Each of these is a reasonable follow-up, kept out to keep the first change
small and testable:

- **Word scores.** A list with a quality score per word would let autofill
  prefer good words and avoid junk. This needs a new word list format.
- **Cancel button and progress.** Run the search in the background and let
  the user stop it.
- **Preview before applying.** Show the proposed fill, with Accept / Try
  again. (Undo covers most of the need for now.)
- **Re-fill unlocked words.** An option to replace complete but unlocked
  words too, so autofill can fix a poor choice you made earlier.
- **Fill just the selected slot or region.**
- **Letter-frequency preference** (pick words that leave crossing slots the
  most options), reusing the scoring already in `get_ranked_suggestions`.

## Tests

Using pytest, with a tiny made-up word list so results are predictable:

- A small open grid with an obvious fill: succeeds, every slot is a word
  from the list, every crossing agrees.
- Existing complete words and locked words are unchanged afterward.
- Partly filled slots keep their letters.
- No two words in the result are equal or near-equal (CAT / CATS), including
  against words that were already in the puzzle.
- A grid with no possible fill: returns failure, puzzle identical to before.
- A time limit of ~0 seconds: returns failure promptly, puzzle unchanged.
- One `undo()` removes the whole fill; one `redo()` restores it.
- Endpoint: success response carries the updated puzzle; failure returns the
  `{"error": ...}` shape with a readable message.
- Frontend (Playwright): click Autofill on a small puzzle, see every cell
  filled; click Undo, see them cleared.

## Open questions

1. **Time limit default.** 10 seconds is a guess; try it on real puzzles
   from `samples/` and adjust.
2. **Random or alphabetical order?** Random gives variety on retry but makes
   a failing case harder to reproduce. Proposal: random, with the random
   seed returned in the error message and accepted by the use case so a
   failure can be repeated in a test.
3. **Should a partly filled unlocked word be allowed to change?** The
   proposal above says no (rule 2). If users find that too strict, it
   becomes the "re-fill unlocked" option.
