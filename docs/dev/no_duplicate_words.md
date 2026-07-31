# No duplicate words — design doc

## The problem this solves

A real crossword puzzle never uses the same answer twice — a solver who
fills in CAT at 5-Across shouldn't later find CAT again at 34-Down. Most
puzzle editors also frown on near-duplicates, especially a word and its
plain plural (CAT and CATS), since that reads just as sloppily as an exact
repeat even though the letters aren't identical.

Right now nothing in this app stops either kind of repeat:

- The suggestion list in the word editor happily offers a word that's
  already sitting somewhere else in the same puzzle.
- Typing a word into the word editor and clicking OK saves it even if it
  duplicates (or is a plural of) a word already placed elsewhere.
- Typing letters directly into the grid, cell by cell, has the same
  problem, because — as it turns out — it goes through the exact same save
  path as the word editor (see below).

This doc adds one shared duplicate/near-duplicate check and wires it into
both the suggestion lists and the one place where word text actually gets
saved, so the whole app enforces the rule consistently rather than needing
three separate fixes.

## Where a word can actually get typed in

Before deciding where to put the check, it's worth being precise about how
many separate code paths can set a word's text, because the check only
needs to be added once, in the right place.

Tracing it through, there turn out to be only two paths in active use, and
they already converge on one function:

- **Word editor "OK"** sends `PUT /api/puzzles/<name>/words/<seq>/<direction>`
  with a `text` field
  ([puzzle_handlers.py:713](../../crossword/http_server/puzzle_handlers.py#L713)),
  which calls `PuzzleUseCases.set_word_clue()`
  ([puzzle_use_cases.py:508](../../crossword/use_cases/puzzle_use_cases.py#L508)).
- **Typing letters directly into a word on the grid** doesn't save anything
  keystroke by keystroke. `_peKeydown`
  ([word-editor.js:300](../../frontend/static/js/word-editor.js#L300)) just
  builds up the typed text in memory (`AppState.selectedWord.draftText`).
  The moment that word is completed or the selection moves on,
  `completeSelectedWordEdit()`
  ([word-editor.js:123](../../frontend/static/js/word-editor.js#L123))
  fires the **same** `PUT .../words/<seq>/<direction>` call, just with
  `draftText` as the `text` field.

So both "ways of typing a word" are really the same save operation under
the hood. `set_word_clue()` applies the new text by calling
`puzzle.set_text(seq, word_dir, text)`
([puzzle_use_cases.py:560](../../crossword/use_cases/puzzle_use_cases.py#L560)),
which lands in `Puzzle.set_text()`
([puzzle.py:97](../../crossword/domain/puzzle.py#L97)). That one method is
the natural place to block a duplicate — catch it there, and both the word
editor and direct grid typing are covered without touching either of them
individually.

There is a third endpoint, `PUT /api/puzzles/<name>/cells/<r>/<c>` →
`set_cell_letter()`
([puzzle_use_cases.py:443](../../crossword/use_cases/puzzle_use_cases.py#L443)),
which writes a single letter straight into the grid without going through
`Word.set_text()` at all. It's documented in the Swagger spec but nothing
in the current frontend calls it — grepping `frontend/` turns up no
callers. Since it's not reachable from the UI today, this doc leaves it
alone; if it's ever wired up as a real "type into one grid square" feature,
the same duplicate check will need to run wherever a word ends up complete
through that path too.

## Detecting exact and near duplicates

New file: `crossword/domain/word_similarity.py`. It's pure Python with no
dependencies, matching the rest of the domain layer, and it's usable from
both the domain layer (the save-time check) and the use-case layer (the
suggestion filters).

The exact-duplicate case is just a case-insensitive string comparison. For
"near duplicate," the doc scopes this to plain English plurals, which cover
the overwhelming majority of real cases (CAT/CATS, BOX/BOXES, CITY/CITIES,
WOLF/WOLVES) using ordinary suffix rules — no dictionary lookup, stemming
library, or new dependency required:

```python
def _plural_variants(word: str) -> set[str]:
    """All plausible plural spellings of word, using simple English rules."""
    variants = {word + "S", word + "ES"}
    if word.endswith("Y") and len(word) > 1 and word[-2] not in "AEIOU":
        variants.add(word[:-1] + "IES")
    if word.endswith("FE"):
        variants.add(word[:-2] + "VES")
    elif word.endswith("F"):
        variants.add(word[:-1] + "VES")
    return variants


def is_near_duplicate(a: str, b: str) -> bool:
    """True if a and b are the same word, or one is a plain plural of the
    other, ignoring case."""
    a, b = a.upper(), b.upper()
    if a == b:
        return True
    return b in _plural_variants(a) or a in _plural_variants(b)


def find_duplicate(candidate: str, existing_words) -> str | None:
    """Return the first word in existing_words that candidate duplicates
    or is a near-duplicate of, or None if there's no conflict."""
    for w in existing_words:
        if is_near_duplicate(candidate, w):
            return w
    return None
```

This deliberately generates *candidate* plural spellings and checks whether
they match a *real* word already in the puzzle, rather than trying to
classify which pluralization rule applies to a given word. That keeps false
positives extremely unlikely: appending "ES" to CAT produces "CATES," which
will only ever trigger a conflict if "CATES" is genuinely already a word
in the grid — which would itself be a coincidence worth flagging.

**What this does not catch:** irregular plurals (MOUSE/MICE, CHILD/CHILDREN,
GOOSE/GEESE) and other non-plural near-duplicates (past tense, gerunds,
etc.) are out of scope for a first version. They'd need either a hand-built
exception list or a real dictionary of word forms, and the ask here was
specifically "duplicate words... and near duplicates like plurals" — this
covers that directly. Expanding it later is just a matter of adding more
functions like `_plural_variants` and calling them from `is_near_duplicate`.

## Blocking entry at `Puzzle.set_text`

`Puzzle.set_text()` already has access to every other word in the puzzle
via `self.across_words` and `self.down_words`
([puzzle.py:50-60](../../crossword/domain/puzzle.py#L50-L60)), so no new
plumbing is needed to see what else is on the grid:

```python
def set_text(self, seq, direction, text, undo=True):
    """ Sets the text of the word at <seq><direction> """
    word = self.get_word(seq, direction)
    if undo:
        new_value = text
        old_value = word.get_text()
        if old_value != new_value:
            self._check_for_duplicate(seq, direction, new_value)
            undoable = ['text', seq, direction, old_value]
            self.undo_stack.append(undoable)
    word.set_text(text)

def _check_for_duplicate(self, seq, direction, text):
    length = self.get_word(seq, direction).length
    normalized = (text + " " * length)[:length]
    if " " in normalized:
        return  # word isn't fully filled in yet; nothing to compare
    others = [
        w for w in list(self.across_words.values()) + list(self.down_words.values())
        if (w.seq, w.direction) != (seq, direction) and w.is_complete()
    ]
    for other in others:
        if find_duplicate(normalized, [other.get_text()]):
            raise ValueError(
                f"{normalized.strip()} duplicates {other.get_text().strip()}, "
                f"already used at {other.location}"
            )
```

Three things about where this hooks in are worth calling out:

- **Only checked when the word is fully filled in.** A word that still has
  blank squares can't equal or plural-match anything by definition (a blank
  never equals a letter), so this only matters once every square has a
  letter — exactly the moment `Word.is_complete()`
  ([word.py:123](../../crossword/domain/word.py#L123)) already exists to
  detect.
- **Only checked when `undo=True`.** That flag is only `False` when
  `Puzzle.undo()` / `Puzzle.redo()`
  ([puzzle.py:270](../../crossword/domain/puzzle.py#L270),
  [puzzle.py:318](../../crossword/domain/puzzle.py#L318)) are replaying a
  value the word legitimately held before. Undo must never fail — if it
  did, a user could get stuck unable to undo their way out of a puzzle
  state — so replay is exempt. Every real, user-initiated edit goes through
  `Puzzle.set_text()` with the default `undo=True`
  ([puzzle_use_cases.py:560](../../crossword/use_cases/puzzle_use_cases.py#L560)),
  so this is the path that actually needs blocking.
- **Compares against every *other* word, not itself.** Without excluding
  `(seq, direction)`, saving a word would always "conflict" with its own
  old value before the new text replaces it. The list comprehension above
  filters that word out before comparing.

This raises a plain `ValueError`, which is the pattern already used
elsewhere for rejecting bad input — for example
`set_cell_letter()`
([puzzle_use_cases.py:459-472](../../crossword/use_cases/puzzle_use_cases.py#L459-L472))
and the "name already exists" check in
[_name_validation.py:9-18](../../crossword/use_cases/_name_validation.py#L9-L18).

## The error reaches the user with no new frontend code

`set_word_clue()` calls `puzzle.set_text()` directly, so the `ValueError`
propagates straight up. `handle_set_word_clue`
([puzzle_handlers.py:748](../../crossword/http_server/puzzle_handlers.py#L748))
already catches `ValueError` and returns `{"error": str(e)}`, and
`completeSelectedWordEdit()` already checks for `data.error` and calls
`showMessageLine(...)` to show it
([word-editor.js:150](../../frontend/static/js/word-editor.js#L150)). That
covers both the word editor and direct grid typing, since — as established
above — they're the same save call. Nothing in the frontend needs to
change for the block itself to show up as a message like:

> Error saving word: GARDEN duplicates GARDENS, already used at 12 across

## Keeping duplicates out of the suggestion list

There are two suggestion endpoints, and they need slightly different
treatment because one already has full puzzle context and the other
doesn't.

**`get_ranked_suggestions()`**
([word_use_cases.py:167](../../crossword/use_cases/word_use_cases.py#L167))
is the one actually used by default in the word editor (the "constrained"
checkbox is checked by default —
[word-editor.js:776](../../frontend/static/js/word-editor.js#L776)). It's
called with a real `Word` domain object
([word_handlers.py:163-164](../../crossword/http_server/word_handlers.py#L163-L164)),
and every `Word` already carries a reference back to its puzzle
(`self.puzzle`, set in `Word.__init__`,
[word.py:16](../../crossword/domain/word.py#L16)). So this needs no new
parameters — just filter the candidate list before returning it:

```python
others = [
    w.get_text() for w in list(word.puzzle.across_words.values()) + list(word.puzzle.down_words.values())
    if (w.seq, w.direction) != (word.seq, word.direction) and w.is_complete()
]
candidates = [c for c in candidates if not find_duplicate(c.upper(), others)]
```

**`get_suggestions(pattern)`**
([word_use_cases.py:26](../../crossword/use_cases/word_use_cases.py#L26))
is the "unconstrained" mode (checkbox unchecked —
`_fetchPatternSuggestions()`,
[word-editor.js:784](../../frontend/static/js/word-editor.js#L784)). Today
it's a pure dictionary lookup with no puzzle context at all —
`GET /api/words/suggestions?pattern=...` doesn't know which puzzle or which
word slot it's being called for. The only caller of this endpoint anywhere
in the app is the word editor itself, always while a specific word in a
specific puzzle is selected, so the fix is to let the frontend pass that
context along as optional query parameters (`puzzle`, `seq`, `direction`),
the same identifiers the ranked-suggestions endpoint already takes as path
segments. When they're present, `handle_get_suggestions` loads the word the
same way `handle_get_ranked_suggestions` does
(`app.puzzle_uc.get_word_at(...)`,
[word_handlers.py:163](../../crossword/http_server/word_handlers.py#L163))
and applies the same filter. When they're absent — e.g. a tool hitting this
endpoint standalone, like `tools/swagger.py`'s documented use of it — it
behaves exactly as it does today, with no filtering. This keeps the
endpoint backward compatible for any use outside the word editor.

## What this intentionally leaves alone

- **`set_cell_letter` / `PUT .../cells/<r>/<c>`** — unused by the frontend
  today (see above), so not wired up. Flagging it here so it isn't
  forgotten if that endpoint is ever put behind a real UI feature later.
- **Irregular plurals and other word-form variants** — out of scope for
  this version; see the note under "Detecting exact and near duplicates."
- **Cross-puzzle duplicates** — this only compares words within the *same*
  puzzle. A word reused across two different puzzles the user owns is
  normal and expected (lots of common words repeat across different
  puzzles); only a repeat *inside one grid* is a problem.
- **Existing puzzles that already contain a duplicate** — this check only
  fires when a word's text is *changed*. A puzzle that already has a
  duplicate sitting in it (hand-built before this feature existed, or
  imported from elsewhere) will load and display fine; the block only
  stops a *new* duplicate from being introduced. Retroactively flagging or
  fixing existing duplicates isn't part of this doc.

## Tests to update

- New `crossword/tests/test_word_similarity.py` — `is_near_duplicate` and
  `find_duplicate`: exact matches, `+S`/`+ES`/`+IES`/`+VES` plural pairs in
  both directions, and confirming ordinary unrelated words of similar
  length aren't flagged.
- `crossword/tests/test_puzzle.py` — setting a word's text to something
  that duplicates or near-duplicates another complete word raises
  `ValueError` and leaves the grid unchanged; setting it to a value that
  doesn't conflict still works; a word with blank squares is never
  flagged.
- `crossword/tests/test_puzzle_undo.py` — undo/redo can still restore a
  value that would otherwise conflict with what's currently on the grid,
  since replay uses `undo=False` and skips the check.
- `crossword/tests/test_puzzle_use_cases.py` — `set_word_clue` surfaces the
  `ValueError` with the conflicting word's text and location in the
  message.
- `crossword/tests/test_word_use_cases.py` — `get_ranked_suggestions`
  excludes words already used elsewhere in the puzzle (and their plurals);
  `get_suggestions` does the same when given puzzle/seq/direction context,
  and is unfiltered without it.
- `crossword/tests/test_http_server.py` — `PUT .../words/<seq>/<direction>`
  returns `{"error": ...}` (not a 500) when the new text duplicates another
  word; `GET /api/words/suggestions` accepts the new optional query
  parameters and filters accordingly.

## Open questions

1. **Should a locked word be exempt from the check?** A locked word's text
   can't be changed through the normal edit path anyway (the Answer field
   is disabled while locked —
   [puzzle_use_cases.py:552-557](../../crossword/use_cases/puzzle_use_cases.py#L552-L557)),
   so in practice this question only matters if some future code path
   tries to set text on a locked word directly. Recommended: no special
   case needed now: the check is purely about the *text being written*, not
   the lock state, so it naturally does the right thing if that ever
   changes.
2. **Should this be a hard block, or a warning the user can override?**
   This doc treats it as a hard block, consistent with how the app already
   handles other invalid input (bad cell letters, duplicate names) — reject
   with a clear message, no silent acceptance. If real usage turns up a
   legitimate reason to allow a repeat on purpose (e.g. a themed puzzle
   that intentionally reuses a word), that would need a deliberate opt-in
   design, not a default in this feature.
