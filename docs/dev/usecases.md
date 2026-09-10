# Use Cases

The application layer (`crossword/use_cases/`) implements business logic by
coordinating domain models (`Grid`, `Puzzle`, `Word`) and ports. It has no
framework or HTTP dependencies. Each use-case class takes its ports via
constructor injection; all are instantiated once in `crossword/wiring/__init__.py`
and handed to the HTTP handlers. See [endpoints.md](endpoints.md) for the
HTTP routes that call into these use cases.

| Class | File | Injected ports |
|---|---|---|
| [PuzzleUseCases](#puzzleusecases) | `puzzle_use_cases.py` | `PersistencePort`, optionally `word_uc` (`WordUseCases`), `grid_generator` |
| [WordUseCases](#wordusecases) | `word_use_cases.py` | `WordListPort` |
| [ExportUseCases](#exportusecases) | `export_use_cases.py` | `PersistencePort` + one export adapter per format |
| [ImportUseCases](#importusecases) | `import_use_cases.py` | `PersistencePort` + one import adapter per format |
| [DefinitionUseCases](#definitionusecases) | `definition_use_cases.py` | `DefinitionProviderPort` |

Every method below takes `user_id` as its first argument (persistence and
ownership are scoped per user) unless noted otherwise.

## PuzzleUseCases

CRUD on puzzles, grid editing, word/clue editing, undo/redo, lifecycle state,
and dashboard/preview/stats queries.

| Method | Returns | Description |
|---|---|---|
| `create_puzzle(name, size)` | `None` | Create a new puzzle with a blank `size`×`size` grid in Grid mode; sets state to `DRAFT`. |
| `load_puzzle(name)` | `Puzzle` | Load a puzzle from storage. |
| `delete_puzzle(name)` | `None` | Delete a puzzle. |
| `list_puzzles(state=None)` | `list[str]` | List a user's puzzle names, most recent first; optionally filtered by lifecycle state. |
| `copy_puzzle(source_name, new_name, comment)` | `Puzzle` | Copy a puzzle under a new name, clearing undo/redo history; backs both Save (working copy → saved name) and Save As. Records a state-history snapshot; `comment` is required. |
| `rename_puzzle(old_name, new_name)` | `None` | Rename a puzzle in place, preserving id and state. |
| `get_puzzle_state(name)` | `dict` | Get `{state, publisher, date_submitted, date_published}`. |
| `set_puzzle_state(name, state, ...)` | `dict` | Apply a user-driven lifecycle transition (validates required fields for `submitted`/`published`). |
| `get_puzzle_state_history(name)` | `list[dict]` | Every state-history row for a puzzle, oldest first. |
| `open_puzzle_for_editing(name)` | `str` | Create a `__wc__<name>__<uuid8>` working copy for editing; returns its name. |
| `restore_puzzle_from_history(name, history_id)` | `str` | Open an old state-history snapshot as a new working copy, without touching the live puzzle. |
| `switch_to_grid_mode(name)` | `Puzzle` | Enter Grid mode; resets Grid-mode undo/redo. |
| `switch_to_puzzle_mode(name)` | `Puzzle` | Enter Puzzle mode; resets Puzzle-mode undo/redo. |
| `toggle_black_cell(name, r, c)` | `Puzzle` | Toggle a black cell in the grid. |
| `rotate_grid(name)` | `Puzzle` | Rotate the grid 180°. |
| `generate_grid(name, spec=None)` | `Puzzle` | Generate a random valid symmetric grid via `grid_generator`. |
| `undo_grid(name)` | `Puzzle` | Undo the last Grid-mode operation. |
| `redo_grid(name)` | `Puzzle` | Redo the last undone Grid-mode operation. |
| `set_puzzle_title(name, title)` | `Puzzle` | Set the puzzle title. |
| `set_cell_letter(name, r, c, letter)` | `Puzzle` | Set a single cell's letter (`A`–`Z` or space); rejects black cells. |
| `get_word_at(name, seq, direction)` | `Word` | Look up an across/down word by numbered cell. |
| `set_word_clue(name, seq, direction, clue, text=None, locked=None)` | `Puzzle` | Set a word's clue and, optionally, its text and/or locked state (both undo-tracked). |
| `clear_unlocked(name)` | `Puzzle` | Blank text and clue of every unlocked word, leaving locked words untouched. |
| `undo_puzzle(name)` | `Puzzle` | Undo the last Puzzle-mode operation. |
| `redo_puzzle(name)` | `Puzzle` | Redo the last undone Puzzle-mode operation. |
| `get_puzzle_stats(name)` | `dict` | Validation results and statistics (`valid`, `errors`, `size`, `wordcount`, `blockcount`, `wordlengths`). |
| `get_fill_order(name, top_n=10)` | `dict` | Ranked list of slots that are good candidates to fill next (cached per puzzle until invalidated by an edit). |
| `get_dashboard()` | `dict` | Summary metadata (state, size, word count, fill %, top word lengths, ...) for every real puzzle owned by the user. |
| `get_puzzle_preview(name)` | `dict` | Scaled-down SVG thumbnail and summary heading, used by the chooser dialogs. |

## WordUseCases

Word-list lookups, pattern-based suggestions, and crossing-letter constraint
analysis. Not user-scoped — the dictionary is shared.

| Method | Returns | Description |
|---|---|---|
| `get_suggestions(pattern, exclude_words=None, length=None)` | `list[str]` | Words matching a `?`/regex pattern, excluding duplicates/near-duplicates of `exclude_words`. |
| `get_all_words()` | `list[str]` | Every word in the dictionary. |
| `validate_word(word)` | `bool` | Whether a word is in the dictionary. |
| `get_word_constraints(word, input_pattern=None, cache=None)` | `dict` | Per-position letter constraints for a word, derived from what its crossing words allow. |
| `get_ranked_suggestions(word, input_pattern=None)` | `list[dict]` | Candidates for a word's slot, ranked by a crossing-viability score (`[{word, score}, ...]`). |
| `get_candidate_count(word, cache=None)` | `int` | Number of dictionary words satisfying a word's current crossing constraints. |
| `get_other_complete_words(word)` | `list[str]` | Text of every other complete word in the same puzzle (helper, used for duplicate exclusion). |

## ExportUseCases

Renders a saved puzzle to an external file format. Each method loads the
puzzle then delegates to the matching adapter.

| Method | Returns |
|---|---|
| `export_puzzle_to_acrosslite(name)` | `bytes` |
| `export_puzzle_to_xml(name)` | `str` |
| `export_puzzle_to_nytimes(name)` | `bytes` |
| `export_puzzle_to_solver_pdf(name)` | `bytes` |
| `export_puzzle_to_solved_pdf(name)` | `bytes` |
| `export_puzzle_to_puz(name)` | `bytes` |
| `export_puzzle_to_xd(name)` | `str` |
| `export_puzzle_to_ipuz(name)` | `str` |

## ImportUseCases

Parses external file content into a new `Puzzle` and saves it under a fresh
name. Each method validates the name is new before parsing.

| Method | Content type | Description |
|---|---|---|
| `import_puzzle_from_acrosslite(name, content)` | `str` | AcrossLite `.txt` format. |
| `import_puzzle_from_xd(name, content)` | `str` | `.xd` format. |
| `import_puzzle_from_ipuz(name, content)` | `str` | ipuz JSON format. |
| `import_puzzle_from_ccxml(name, content)` | `str` | Crossword Compiler `.xml` format. |
| `import_puzzle_from_puz(name, content)` | `bytes` | AcrossLite binary `.puz` format. |

## DefinitionUseCases

Looks up dictionary definitions for a word (used by the word editor's
definition lookup, separate from `WordListPort`'s pattern matching).

| Method | Returns | Description |
|---|---|---|
| `lookup(word)` | `dict` | Definitions grouped by part of speech: `{word, entries: [{part_of_speech, definitions: [{text, example}]}]}`. Raises `DefinitionNotFound` if the word isn't found. |
