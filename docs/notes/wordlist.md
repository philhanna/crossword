# Word List Separation Design

## Question

Tell me what you think.  Right now, I have the words list in the same sqlite database as the puzzles.  I'd like to separate that out, initially just to a different database.  My reasons are: 1. I can imagine that different word lists are useful, and I'd like to be able to swap them in and out.  2. In the future there may be more that the word list can do; it isn't enough to just consider it a passive search source.  It could be that it combines words into phrases or any number of things. It may even be an AI agent that I call.  So it most likely needs some work on the port and adapter.  Do you think this is a worthwhile change?  Sketch out a plan for conversion.

---

## Assessment: Is This Change Worthwhile?

**Yes.** Separating the word list database from the puzzle database is a worthwhile architectural change.

### Reasoning

1. **Architectural soundness**: Word lists and puzzle data are fundamentally different concerns—one is configuration/reference data, the other is user content. Separating them follows single responsibility principle.

2. **Your use cases are valid**:
   - Different word lists (for themes, difficulty levels, languages) makes total sense
   - The evolution you envision (phrases, composition, AI agents) points to word lists becoming **active components**, not just lookup tables

3. **Your architecture is already ready**: The `WordListPort` abstraction exists; `SQLiteDictionaryAdapter` already has `load_from_database(db_path)`. No new classes are needed — just point it at a different file.

4. **Low risk**: This is internally-facing infrastructure with clean interfaces.

---

## Conversion Plan

### Step 1: Migrate the Data

Create a one-time migration script (`tools/migrate_wordlist.py`) that:
- Reads the `words` table from the puzzle database (`samples.db`)
- Writes to a new `words.db`
- Schema is identical; no transformation needed

### Step 2: Update Wiring

Update `crossword/wiring/__init__.py`:
- Add `word_dbfile` config key (separate from `dbfile`)
- Load `SQLiteDictionaryAdapter` from `word_dbfile` when present
- Fall back to `word_file` (text file), then `dbfile` (old behaviour), for backwards compatibility during transition

No new adapter class is needed. `SQLiteDictionaryAdapter.load_from_database()` already accepts any `db_path`.

### Load priority in `make_app()`

1. `word_adapter.load_from_database(config['word_dbfile'])` — new dedicated word DB
2. `word_adapter.load_from_file(config['word_file'])` — text file fallback
3. `word_adapter.load_from_database(config['dbfile'])` — old shared DB (transition only)
4. Empty adapter (tests only)

---

## Implementation Notes

### Files changed

```
crossword/
  wiring/
    __init__.py         # Update: add word_dbfile config key, adjust load priority
tools/
  migrate_wordlist.py   # NEW: one-time export script
```

No new adapter. No new port methods. `sqlite_dictionary_adapter.py` and `word_list_port.py` are unchanged.

### Configuration

- `dbfile`: Path to puzzle database (unchanged)
- `word_dbfile`: Path to word list database (new)
- `word_file`: Path to word list text file (fallback, unchanged)

### Database Schema

`words.db` uses the same schema as the current table in the puzzle database:

```sql
CREATE TABLE words (
    word  TEXT UNIQUE NOT NULL
);
```

---

## Future Work (not part of this change)

The goals below are worth pursuing, but don't need to happen now. Add them as separate issues when the requirements become concrete.

- **Port enrichment**: New methods on `WordListPort` (metadata, validation, phrase composition, AI suggestions) only make sense once there's a use case that calls them. Adding abstract methods speculatively forces every future adapter to implement things that may never be needed.

- **Multiple word lists**: Per-puzzle word list selection, a `WordListFactory`, theme-based lists — these are valid ideas but have no concrete use case yet.

---

## Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| Backwards compatibility broken | Fallback chain in `make_app()` covers old `dbfile` during transition |
| Deployment complexity (two DBs) | Migration script is a one-time export; afterwards `words.db` is standalone |
| Tests need updating | Only wiring tests; all word list port/adapter tests unchanged |
