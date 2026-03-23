# Issue 148 — Rank Suggested Words by Likelihood of Fit

## Problem

`get_suggestions(pattern)` currently returns an alphabetically sorted list of matching words. When a user is filling in a word with known crossing letters, there is no signal about which candidates are more likely to work — i.e., leave the most options open for the crossing words. All matches are treated equally.

## Current flow

```
Constraints tab → GET /api/.../constraints → {crossers, pattern}
User clicks "Suggest ›" → GET /api/words/suggestions?pattern=... → alphabetical list
```

The key data that already exists but is thrown away: `crossers[i].matches` — the full list of dictionary words that match each crossing word's current pattern. From those lists we can compute, for any candidate, how many crossing-word completions it enables at each position.

---

## Ranking metric

For each candidate word, compute a **crossing viability score**:

```
score(candidate) = Σ over position i of:
    count of crossing-word matches where letter at crossing_index == candidate[i]
```

This answers: "If I place this word, how many options remain for each crossing word?" Words that use common letters at crossing positions (where many crossing words agree) rank higher.

This is computable from data already gathered during `get_word_constraints()` — no extra dictionary lookups needed beyond what constraints already does.

### Example

Crossing word at position 3 matches 40 dictionary words. Of those, 18 have E at the intersection, 10 have A, 7 have I, 5 have O. A candidate with E at position 3 scores 18 for that slot; one with O scores 5.

---

## Design

### 1. Extend `WordUseCases` — add `get_ranked_suggestions`

```python
def get_ranked_suggestions(self, word) -> list[dict]:
    """
    Return candidates for the given Word, ranked by crossing viability score.

    Returns:
        List of dicts sorted by score descending:
          [{"word": "CRANE", "score": 142}, ...]
    """
```

**Algorithm:**

```python
# Step 1: get crossing context (reuses existing logic)
constraints = self.get_word_constraints(word)
pattern = constraints["pattern"]

# Step 2: for each position, build letter → count map from crossing matches
letter_scores = []   # list of {letter: count} dicts, one per position
for crosser in constraints["crossers"]:
    crossing_pattern = "^" + re.sub(r"[ ?]", ".", crosser["crossing_text"].replace(".", " ")) + "$"
    matches = self.word_list.get_matches(crossing_pattern)
    idx = crosser["crossing_index"] - 1   # 0-indexed
    freq = {}
    for m in matches:
        letter = m[idx].upper()
        freq[letter] = freq.get(letter, 0) + 1
    letter_scores.append(freq)

# Step 3: get candidates matching the derived pattern
candidates = self.word_list.get_matches(pattern)

# Step 4: score and sort
def score(candidate):
    return sum(
        letter_scores[i].get(candidate[i].upper(), 0)
        for i in range(len(candidate))
        if i < len(letter_scores)
    )

return sorted(
    [{"word": c, "score": score(c)} for c in candidates],
    key=lambda x: x["score"],
    reverse=True,
)
```

**Performance note:** `get_word_constraints` already fetches the crossing matches once. To avoid a second fetch here, the letter frequency maps can be built during the same pass — fold this into `get_word_constraints` so the data is computed once and returned.

### 2. Update `get_word_constraints` to include letter frequency maps

Add a `letter_freq` field to each crosser entry:

```python
crossers[i]["letter_freq"] = {"E": 18, "A": 10, "I": 7, ...}
```

This is just a tally of the matches already fetched — zero extra cost. `get_ranked_suggestions` can then accept a pre-computed constraints dict instead of re-fetching.

### 3. New HTTP endpoint

```
GET /api/puzzles/{name}/words/{seq}/{dir}/suggestions
```

Uses `get_ranked_suggestions(word)` and returns:

```json
{
  "pattern": "[AEIOU][A-Z][AEIOU][ST][A-Z]",
  "suggestions": [
    {"word": "crane", "score": 142},
    {"word": "grail", "score": 117},
    ...
  ],
  "count": 34
}
```

Keep the existing `GET /api/words/suggestions?pattern=...` endpoint unchanged (it has no crossing context, returns alphabetically sorted words for use in the generic Suggest tab).

### 4. Frontend changes

**Constraints tab** — update `doFastpath` / "Suggest ›" button:

Instead of redirecting to the generic suggest tab with a pattern string, call the new context-aware endpoint directly and display the ranked results in a list within the Constraints tab (or update the Suggest tab with pre-fetched ranked results).

Suggested approach — replace the "Suggest ›" button behavior:

```javascript
async function doConstrainedSuggest() {
    const ew = AppState.editingWord;
    const wn = AppState.puzzleWorkingName;
    const data = await apiFetch('GET',
        `/api/puzzles/${wn}/words/${ew.seq}/${ew.direction}/suggestions`);

    // populate the same we-select list but with score annotations
    for (const item of data.suggestions) {
        const opt = document.createElement('option');
        opt.value = item.word.toUpperCase();
        opt.textContent = `${item.word.toUpperCase()}  (${item.score})`;
        selectEl.appendChild(opt);
    }
}
```

Showing the score next to each word gives the user a quick sense of how "constrained" each choice is.

---

## Fallback for the generic Suggest tab

When the user types a raw pattern in the Suggest tab (no word context), ranking by crossing viability isn't possible. Options:

1. Keep alphabetical order (current behavior) — simplest, no change needed
2. Add word frequency scoring to the dictionary (see below)

For now, **keep alphabetical order** in the generic tab and only apply viability ranking in the context-aware endpoint. This is the simplest incremental improvement.

---

## Optional future: word frequency

If the `words` SQLite table gains a `frequency` integer column (e.g., from the Google Books Ngram corpus or a crossword-specific frequency list), `get_matches` can `ORDER BY frequency DESC`. This would improve the generic tab too.

Schema change (not in scope for this issue):
```sql
ALTER TABLE words ADD COLUMN frequency INTEGER DEFAULT 0;
```

`DictionaryAdapter.get_matches` would then return words sorted by frequency rather than alphabetically. No use-case or API changes needed.

---

## File changes

| File | Change |
|------|--------|
| `crossword/use_cases/word_use_cases.py` | Add `get_ranked_suggestions(word)`; add `letter_freq` to `get_word_constraints` crossers |
| `crossword/http_server/word_handlers.py` | Add `handle_get_ranked_suggestions` handler |
| `crossword/http_server/main.py` | Register new route |
| `frontend/static/js/app.js` | Update Constraints tab "Suggest ›" to call new endpoint; display scores |
| `crossword/tests/test_word_use_cases.py` | Tests for `get_ranked_suggestions` |

---

## Tests

- `test_ranked_suggestions_orders_by_score` — candidate that matches more crossing words ranks higher
- `test_ranked_suggestions_all_blanks` — word with no filled crossing letters → all scores zero → still returns matches (falls back to alphabetical or equal score)
- `test_ranked_suggestions_no_candidates` — pattern matches nothing → returns empty list
- `test_get_word_constraints_includes_letter_freq` — each crosser now has a `letter_freq` dict

---

## Out of scope

- Word frequency from an external corpus
- Ranking in the generic `GET /api/words/suggestions` endpoint (no crossing context there)
- Exposing a "score threshold" filter to the user
