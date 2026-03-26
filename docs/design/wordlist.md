## Question

Tell me what you think.  Right now, I have the words list in the same sqlite database as the puzzles.  I'd like to separate that out, initially just to a different database.  My reasons are: 1. I can imagine that different word lists are useful, and I'd like to be able to swap them in and out.  2. In the future there may be more that the word list can do; it isn't enough to just consider it a passive search source.  It could be that it combines words into phrases or any number of things. It may even be an AI agent that I call.  So it most likely needs some work on the port and adapter.  Do you think this is a worthwhile change?  Sketch out a plan for conversion.

---

# Word List Separation Design

## Assessment: Is This Change Worthwhile?

**Yes.** Separating the word list database from the puzzle database is a worthwhile architectural change.

### Reasoning

1. **Architectural soundness**: Word lists and puzzle data are fundamentally different concerns—one is configuration/reference data, the other is user content. Separating them follows single responsibility principle.

2. **Your use cases are valid**: 
   - Different word lists (for themes, difficulty levels, languages) makes total sense
   - The evolution you envision (phrases, composition, AI agents) points to word lists becoming **active components**, not just lookup tables
   - Future extensibility is built in from the start

3. **Your architecture is already half-ready**: The `WordListPort` abstraction exists; `DictionaryAdapter` can load from file or database. You just need to decouple the storage.

4. **Low risk**: This is internally-facing infrastructure with clean interfaces.

---

## Conversion Plan

### Phase 1: Create Word List Database & Adapter

1. Create `WordListDatabaseAdapter` (new file: `crossword/adapters/wordlist_database_adapter.py`) that:
   - Extends/implements `WordListPort`
   - Takes its own `db_path` parameter
   - Handles connection to a **separate SQLite database** with a `words` table
   - Inherits the regex matching logic from current `DictionaryAdapter`

2. Keep `DictionaryAdapter` as an in-memory adapter (for testing, file-based lists)

3. Update wiring (`crossword/wiring/__init__.py`):
   - Add config keys: `word_dbfile` (separate from `dbfile`)
   - Instantiate `WordListDatabaseAdapter` instead of `DictionaryAdapter`
   - Fall back to file loading if word DB missing (for backwards compatibility during migration)

### Phase 2: Migrate Data

1. Create a one-time migration script (`tools/migrate_wordlist.py`) that:
   - Reads `words` table from puzzle database
   - Writes to a new `words.db` (or similar)
   - Keeps schema identical initially

2. Update deployment/setup to create both databases

### Phase 3: Enhanced Word List Port (future-proofing)

1. Add new methods to `WordListPort` for future extensibility:
   - `get_word_metadata(word: str) -> dict` (for tags, difficulty, themes, etc.)
   - `validate_word(word: str) -> bool` (for future AI validation)
   - Maybe: `get_suggestions(pattern: str, max_results: int) -> list[Suggestion]`

2. This positions you to evolve without touching puzzle logic

### Phase 4: Support Multiple Word Lists (optional, later)

- Store word list selection in puzzle metadata or user config
- Create a `WordListFactory` that selects adapter based on config
- This enables theme-based word lists, difficulty levels, etc.

---

## Implementation Notes

### File Structure After Phase 1

```
crossword/
  adapters/
    dictionary_adapter.py       # Keep: in-memory loader
    wordlist_database_adapter.py  # NEW: database-backed adapter
    sqlite_adapter.py           # Keep: puzzle/grid persistence
  ports/
    word_list.py               # Keep: unchanged
  wiring/
    __init__.py                # Update: wire new adapter, add config keys
```

### Configuration

New config keys:
- `dbfile`: Path to puzzle database (unchanged)
- `word_dbfile`: Path to word list database (new)
- `word_file`: Path to word list text file (fallback, unchanged)

Load priority in `make_app()`:
1. Try `WordListDatabaseAdapter(config['word_dbfile'])`
2. Fall back to `DictionaryAdapter.load_from_file(config['word_file'])`
3. Fall back to empty in-memory adapter (testing only)

### Database Schema

Initial `words.db` schema (same as current in puzzle database):
```sql
CREATE TABLE words (
    id    INTEGER PRIMARY KEY,
    word  TEXT UNIQUE NOT NULL
);
```

Later (Phase 3+), extend with metadata:
```sql
CREATE TABLE words (
    id         INTEGER PRIMARY KEY,
    word       TEXT UNIQUE NOT NULL,
    difficulty INTEGER,        -- optional
    category   TEXT,          -- optional
    metadata   JSON           -- optional
);
```

---

## Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| Backwards compatibility broken | Fallback to file-based loading during transition |
| Deployment complexity (two DBs) | Migration script handles one-time export; then standard |
| Tests need updating | Only wiring tests; word list port tests unchanged |
| Word list port enrichment (Phase 3) may break adapters | Design with backward compatibility in mind; add optional methods |

---

## Timeline Estimate

- **Phase 1**: 1-2 hours (new adapter, wiring updates, tests)
- **Phase 2**: 30 minutes (migration script)
- **Phase 3**: 1-2 hours (port enhancement, adapter updates)
- **Phase 4**: TBD (depends on requirements)
