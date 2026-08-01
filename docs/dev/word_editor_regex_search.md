# Free-form regex search in the word editor — design doc

## The problem this solves

The word editor's "Suggestions" box already lets you type a rough pattern —
letters you know, spaces for the ones you don't — and get back matching
dictionary words. Under the hood, that box is quietly more powerful than it
looks: if you type something with regex characters in it (`[AEIOU]`, `CAT|DOG`,
and so on), the backend already understands it as a real Python regular
expression and searches with it correctly
([word_use_cases.py:253-277](../../crossword/use_cases/word_use_cases.py#L253-L277)).

The catch is that you can never actually type one in. The Answer field that
doubles as the pattern box is capped, in the HTML itself, to exactly the
number of letters in the crossword slot
([word-editor.js:487](../../frontend/static/js/word-editor.js#L487),
`maxlength="${len}"`). A useful regex is almost always *longer* than the word
it's meant to match — `[AEIOU]{3}` is 9 characters for a 3-letter search,
`C[AR]..E` is 8 characters for a 5-letter one. The box simply won't let you
type them.

This doc is about removing that cap so any regex can be typed and searched —
while making sure the search only ever looks at words of the right length,
so a loose pattern like `C.*T` can't return "CROCHET" as a match for a
3-letter slot just because the regex itself doesn't rule it out.

## Two separate gaps, one on each side

### Backend: the plain search path doesn't filter by length at all

There are two suggestion endpoints, and only one of them already limits
itself to words of the right length:

- **Ranked / "Constrained" search** (`GET
  /api/puzzles/<name>/words/<seq>/<dir>/suggestions`, backing
  `get_ranked_suggestions`) builds one character-class per letter position
  from the crossing words, so its pattern is always exactly `word.length`
  positions long by construction, and it already calls
  `word_list.get_matches(pattern, length=word.length)`
  ([word_use_cases.py:201](../../crossword/use_cases/word_use_cases.py#L201)).
  This path is not the target of this change — it can't express "any regex"
  anyway, since it's locked to one character class per cell.

- **Plain pattern search** (`GET /api/words/suggestions`, backing
  `get_suggestions`) is the one this doc is about. It calls
  `word_list.get_matches(regex_pattern)` with **no length argument**
  ([word_use_cases.py:49](../../crossword/use_cases/word_use_cases.py#L49)).
  The dictionary is organized internally as separate lists, one per word
  length, so the search can jump straight to (say) "all the 5-letter
  words" instead of checking every word in the dictionary. But that only
  happens when a `length` is given. Without one, `get_matches` checks
  every word, of every length, and just trusts the pattern to only match
  words of the length it's meant for
  ([flat_file_word_list_adapter.py:75-79](../../crossword/adapters/flat_file_word_list_adapter.py#L75-L79)).

  For today's wildcard patterns (letters and blanks, always exactly as many
  characters as the slot) that's harmless — a pattern with, say, 5 fixed
  positions can only ever match 5-letter words anyway. But a real regex
  doesn't have to work that way. `C.*T` can match "CT", "CAT", "COAT", or
  "CROCHET" — the pattern itself puts no ceiling on length. Once arbitrary
  regex is allowed, "search the whole dictionary and hope the pattern
  happens to constrain length" stops being good enough. The slot's length
  has to be enforced directly, not implied.

### Frontend: the input box is too short to type a regex into

Even with the backend fixed, the Answer field
([word-editor.js:486-488](../../frontend/static/js/word-editor.js#L486-L488))
is hard-capped at the slot length via `maxlength`, and every keystroke also
writes a truncated, padded-to-length copy of the box into the live grid
preview (`weHandleTextInput` →
[word-editor.js:574-579](../../frontend/static/js/word-editor.js#L574-L579)).
That's exactly right for its main job — typing a candidate answer directly
into a slot and watching it appear on the grid — but it leaves no room to
type a longer search expression, and even if the cap were simply removed,
half-typed regex punctuation (`[`, `|`, `{3}`) would start flashing into the
grid cells as you type, which would be confusing and has no useful meaning
as a "draft answer."

## What changes

### 1. Thread word length through the plain search path

`get_suggestions` gains an optional `length` parameter, passed straight
through to `word_list.get_matches`, the same way `get_ranked_suggestions`
and `get_candidate_count` already do:

```python
def get_suggestions(self, pattern: str, exclude_words: list[str] = None,
                     length: int = None) -> list[str]:
    ...
    matches = self.word_list.get_matches(regex_pattern, length=length)
```

`handle_get_suggestions` already loads the `Word` object whenever
`puzzle`/`seq`/`direction` are given, in order to compute `exclude_words`
([word_handlers.py:44-47](../../crossword/http_server/word_handlers.py#L44-L47)).
That same `word` already knows its own length, so the handler can pass
`length=word.length` at no extra cost — no new lookup, no new request
parameter needed for the normal case (searching from inside the word
editor, which always has puzzle context).

For the rare case of a caller hitting `/api/words/suggestions` with no
puzzle context (so there's no `Word` to read a length from), accept an
optional `length` query parameter directly, so the endpoint still has a way
to scope the search:

```
GET /api/words/suggestions?pattern=<pattern>&length=<n>
GET /api/words/suggestions?pattern=<pattern>&puzzle=<name>&seq=<seq>&direction=<dir>
```

When neither is present, behavior is unchanged from today (search the whole
dictionary) — this only tightens things up for the callers that can supply
a length, which in practice is every real use from the word editor.

This is the change that actually delivers "any regex, but only words of the
right length": once `length` is passed all the way through, the search only
ever looks at the list of words that are exactly that many letters long
([flat_file_word_list_adapter.py:75-76](../../crossword/adapters/flat_file_word_list_adapter.py#L75-L76)),
so a pattern like `C.*T` searched for a 3-letter slot can only ever come
back with 3-letter words — "CROCHET" is never a candidate in the first
place, not filtered out after the fact.

### 2. Let the Answer field hold a full regex, without corrupting the grid preview

Reuse the existing "Constrained" checkbox as the signal for which mode the
field is in, rather than adding a new input:

- **Constrained checked (default, unchanged):** the field behaves exactly
  as it does today — capped at the slot length, live-synced to the grid
  preview on every keystroke. This mode's search is always exactly
  slot-length anyway (each position is one crossing-derived letter class),
  so there's never a reason to type more than `len` characters here.

- **Constrained unchecked (free-form regex search):** drop the `maxlength`
  cap on the field, and stop syncing it into the live grid preview while
  it's in this mode — `weHandleTextInput` skips the
  `renderPuzzleEditorLhs()` call when unconstrained search is active, so
  typing `[AEIOU]{2}` doesn't flash regex punctuation into the puzzle grid.
  The field's contents are only ever sent to `/api/words/suggestions` as a
  search pattern in this mode; nothing is written to the grid until the
  user actually picks a result.

Picking a result from the suggestion list already does the right thing and
needs no change: `weListItemClick`
([word-editor.js:543-552](../../frontend/static/js/word-editor.js#L543-L552))
replaces whatever is in the Answer field with the chosen word and re-syncs
`draftText` from it. So the flow becomes: uncheck Constrained, type a regex,
hit Suggest, double-click (or click, then Apply) a result — at which point
the field holds a real, correctly-sized answer again, and Apply behaves
exactly as it always has.

One more small guard is worth adding, in case the user types a regex and
hits Apply directly without picking anything from the list first: Apply
should only commit the field's contents as the slot's answer when it's a
plausible answer — letters (and blanks) only, and no longer than the slot.
`_selectedWordIsComplete`
([word-editor.js:78-82](../../frontend/static/js/word-editor.js#L78-L82))
already has the concept of "is this field's content a real answer";
extending that same check to gate Apply avoids ever writing raw regex
punctuation into a grid cell.

## Safety of allowing arbitrary regex

The backend was already willing to run anything that "looked like regex"
through Python's regex engine before this change
([word_use_cases.py:267-273](../../crossword/use_cases/word_use_cases.py#L267-L273)).
So this isn't opening the door to a new kind of input — it's just making a
door that was already unlocked actually easy to find and use from the
screen. Two things are worth tightening up now that it's a real, advertised
feature instead of something only a user who guessed at it could stumble
into:

- **Slow, "runaway" patterns.** Certain regular expressions can be written
  (by accident or on purpose) so that checking them against a piece of text
  takes an extremely long time — far longer than the text's length would
  suggest — instead of finishing almost instantly like a normal search.
  That's usually a real danger when the text being checked can be long and
  attacker-supplied. Here it isn't much of one: every word being checked is
  a short dictionary word (the word list tops out well under 30 letters),
  so even a worst-case pattern can only ever be slow-checked against a
  short word, which puts a natural ceiling on how bad it can get. As a
  cheap extra safeguard anyway, put a cap on how long the search pattern
  itself can be (e.g. 200 characters) and reject anything longer with the
  same "invalid pattern" error already used for broken regex syntax — a
  real search for a crossword word never needs to be longer than that.
- **The search results cache never gets cleared out.** The word-list code
  saves the results of every search it's ever run, keyed by the exact
  search text and length, so it doesn't have to redo the same search
  twice — but it never throws old entries away
  ([flat_file_word_list_adapter.py:24](../../crossword/adapters/flat_file_word_list_adapter.py#L24),
  [:66-68](../../crossword/adapters/flat_file_word_list_adapter.py#L66-L68)).
  That was a small, pre-existing rough edge when only a handful of
  predictable searches ever reached it. Once people can type any regex they
  like, the number of different searches that could ever be saved has no
  real limit. This doesn't need to block the change — each saved result is
  small, and it only grows as fast as people actually click "Suggest," not
  under some outsider's control — but it's worth putting a size limit on
  this saved-results list later (throwing away the oldest entries once it
  gets too big is the usual fix) rather than letting it grow forever.

## Tests to update

- `crossword/tests/test_word_use_cases.py` — `get_suggestions` gains a
  `length` argument; add a case asserting it's forwarded to
  `word_list.get_matches(..., length=...)`, alongside the existing
  `test_get_suggestions_with_regex`
  ([test_word_use_cases.py:35-42](../../crossword/tests/test_word_use_cases.py#L35-L42))
  which already confirms arbitrary regex syntax is accepted.
- `crossword/tests/test_http_server.py` — extend
  `test_handle_get_suggestions_filters_using_puzzle_context`
  ([test_http_server.py:543](../../crossword/tests/test_http_server.py#L543))
  to also assert `length=word.length` is passed through when puzzle context
  is given; add a case for the new standalone `length` query parameter; add
  a case for a pattern over the new max-length cap being rejected.
- `crossword/tests/adapters/test_dictionary_adapter.py` — add a regex case
  with a variable-length pattern (e.g. `C.*T`) confirming that passing
  `length=3` only ever returns 3-letter words, never longer ones the regex
  alone would also accept.
- Frontend: manual check (no JS test harness in this project today) —
  uncheck Constrained, type a multi-character regex longer than the slot,
  confirm it's accepted and searched, confirm the grid preview doesn't
  change until a suggestion is picked, and confirm Apply is a no-op (or
  shows a message) if pressed while the field still holds raw regex text.

## Open questions

1. **Exact pattern-length cap.** 200 characters is a placeholder — any
   number comfortably larger than a human would ever type by hand works;
   this isn't a tight performance limit, just a sanity backstop.
2. **Should the unconstrained-search checkbox be relabeled?** "Constrained"
   already correctly describes what turning it off does (search without the
   crossing-letter constraints); it doesn't need a rename just because the
   pattern box now accepts richer syntax when it's off. Recommend leaving
   the label as-is unless real users find it confusing in practice.
3. **When to put a size limit on the saved-results list.** Flagged above as
   a good follow-up, not a blocker. Recommend shipping without it and
   revisiting only if memory use actually turns out to matter in practice —
   same wait-and-see approach the project has already taken on a similar
   question elsewhere (see
   [puzzle_content_snapshots.md](puzzle_content_snapshots.md), "How far
   back should snapshots be kept?").
