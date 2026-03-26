# Wordlist Separation Plan

Implements the design in [docs/design/wordlist.md](../design/wordlist.md).

---

## Phase 1 — Migration script

- [x] Create `tools/migrate_wordlist.py`
  - Reads `words` table from puzzle DB (path from argv or `~/.crossword.ini`)
  - Creates `words.db` with identical schema
  - Inserts all rows; prints count on success

---

## Phase 2 — Wiring update

- [ ] Add `word_dbfile` config key support to `crossword/wiring/__init__.py`
- [ ] Replace current load logic with the priority chain:
  1. `word_adapter.load_from_database(config['word_dbfile'])` — new dedicated word DB
  2. `word_adapter.load_from_file(config['word_file'])` — text file fallback
  3. `word_adapter.load_from_database(config['dbfile'])` — old shared DB (transition)
  4. Empty adapter (no config — tests only)
- [ ] Update `make_app()` docstring to document `word_dbfile`

---

## Phase 3 — Tests

- [ ] Add `temp_word_db` fixture to `test_wiring.py` (separate SQLite DB with `words` table + a few rows)
- [ ] `test_make_app_loads_word_dbfile` — `word_dbfile` present → adapter populated from it
- [ ] `test_make_app_word_dbfile_takes_priority` — both `word_dbfile` and `dbfile` present → adapter uses `word_dbfile`
- [ ] `test_make_app_falls_back_to_word_file` — no `word_dbfile`, `word_file` present → adapter loads from file
- [ ] `test_make_app_falls_back_to_dbfile` — no `word_dbfile`, no `word_file`, `dbfile` present → adapter loads from shared DB (old behaviour)
- [ ] `test_make_app_empty_adapter_when_no_words` — none of the word sources present → adapter empty, no exception

---

## Phase 4 — Config documentation

- [ ] Add `word_dbfile` entry to `~/.crossword.ini` sample/docs (if one exists in the repo)

---

## Done

*(phases moved here when complete)*
