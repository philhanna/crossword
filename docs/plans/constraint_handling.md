# Constraint Handling Performance Plan

## Goal

Reduce the cost of `get_word_constraints` and `get_ranked_suggestions` by avoiding
full dictionary scans when the required word length is already known. Currently each
call to `get_matches` compiles a regex and tests it against every word in the dictionary.
For an N-letter word, `get_word_constraints` makes N such scans.

## Background

`WordUseCases.get_word_constraints` (word_use_cases.py:75) iterates over each crossing
word and calls `self.word_list.get_matches(crossing_pattern)` once per position. For a
15-letter word this is 15 full scans. The crossing word's length is known at that point
(`crossing_word.length`) but is not passed to the adapter, so the adapter cannot narrow
its search.

Both adapters (`FlatFileWordListAdapter`, `SQLiteDictionaryAdapter`) store all words in
a flat `set` and iterate the entire set on every `get_matches` call.

## Changes

### Step 1 — `WordListPort`: add optional `length` parameter

File: `crossword/ports/word_list_port.py`

Add `length: int = None` to the `get_matches` signature. Default `None` preserves
existing behaviour (full scan). Update the docstring to describe the parameter.

```python
@abstractmethod
def get_matches(self, pattern: str, length: int = None) -> list[str]:
    """
    ...
    Args:
        pattern: Python regex pattern (e.g., "^[A-Z]{5}$" for 5-letter words)
        length:  If provided, only words of this exact length are considered.
                 Callers should supply this whenever the target length is known,
                 as it avoids scanning irrelevant words.
    ...
    """
```

### Step 2 — `FlatFileWordListAdapter`: bucket by length

File: `crossword/adapters/flat_file_word_list_adapter.py`

Replace `self._words: set` with `self._words_by_length: dict[int, list[str]]`.

In `load_from_file`:
```python
words = {line.strip().lower() for line in f if line.strip()}
self._words_by_length = {}
for w in words:
    self._words_by_length.setdefault(len(w), []).append(w)
```

In `get_matches`:
```python
def get_matches(self, pattern: str, length: int = None) -> list[str]:
    if length is not None:
        candidates = self._words_by_length.get(length, [])
    else:
        candidates = (w for bucket in self._words_by_length.values() for w in bucket)
    regex = re.compile(pattern, re.IGNORECASE)
    return sorted(word for word in candidates if regex.fullmatch(word))
```

In `get_all_words`:
```python
return sorted(w for bucket in self._words_by_length.values() for w in bucket)
```

### Step 3 — `SQLiteDictionaryAdapter`: same change

File: `crossword/adapters/sqlite_dictionary_adapter.py`

Identical restructuring to Step 2. Both `load_from_database` and `load_from_file`
build `self._words_by_length` instead of `self._words`. `get_matches` and
`get_all_words` are updated the same way.

### Step 4 — `WordUseCases`: pass length at the two hot call sites

File: `crossword/use_cases/word_use_cases.py`

In `get_word_constraints` (line 113):
```python
matches = self.word_list.get_matches(crossing_pattern, length=crossing_word.length)
```

In `get_ranked_suggestions` (line 179):
```python
candidates = self.word_list.get_matches(self._pattern_to_regex(pattern), length=word.length)
```

The third call site, `get_suggestions` (line 45), is the unconstrained public endpoint
where the caller does not necessarily fix a length. Leave it unchanged — it will
continue to do a full scan via the `length=None` default.

## What is not changing

- `WordUseCases.get_suggestions` — public pattern search, no length constraint
- All use case logic, scoring, ranking
- The port's `get_all_words` contract
- Any test that calls `get_matches` without a `length` argument — they continue to work

## Test coverage

The existing adapter tests exercise `get_matches` without a `length` argument and
should pass unchanged. Add cases to each adapter's test module that pass a `length`
and assert that only words of that length are returned, including the edge case where
no words of that length exist (expect `[]`).
