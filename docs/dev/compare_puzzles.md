# Comparing two puzzles — design doc

Written for: the project owner, to review and answer the open questions
before anything is built.

## What this adds

A tool that takes two puzzles and shows what is different between them.
It is meant for questions like "what did the editor change in my puzzle?"
or "how does this revised version differ from the one I submitted?"

Each puzzle is turned into a list of text lines:

1. One line for every Across word, in number order: the number, the answer,
   and the clue.
2. Then one line for every Down word, in the same way.

The title is printed as a first line (`Title: ...`). The two lists are then
compared line by line and the differences are printed in the familiar "diff"
style (lines starting with `-` exist only in
the first puzzle, lines starting with `+` exist only in the second).

Example. Puzzle A has these lines:

```
Title: Water words
Across
1A OCEAN  Big blue expanse
5A RIVER  Flows to the sea
Down
1D ORB    Round object
2D CAR    Vehicle
```

Puzzle B has the same grid, but 5-Across has a new clue and 2-Down has a
new answer. The result is:

```
 Title: Water words
 Across
 1A OCEAN  Big blue expanse
-5A RIVER  Flows to the sea
+5A RIVER  Water that flows to the sea
 Down
 1D ORB    Round object
-2D CAR    Vehicle
+2D CAB    Vehicle
```

If the two puzzles are the same, the tool says so and shows no differences.

## What is compared, and what is not

**Compared:** the title, and the answer letters and clue of every Across
and Down word.

**Not compared:** author, locked words (locks are ignored), circled squares,
the puzzle's state (draft, submitted, and so on), undo history, and anything
else.

Clues are compared exactly, except that spaces at the very start or end of
a clue are ignored. Upper and lower case differences count as changes.

Because the two puzzles are required to have the same shape, words can only
be *changed*, never added or removed, and a word keeps its number. So the
diff only ever shows changed lines in pairs (`-` then `+`).

## When the two puzzles cannot be compared

Before comparing, the tool checks that the two puzzles have the same
**shape**. If they do not, it stops and raises an error; it does not show a
partial diff.

- **Different size.** The number of rows or columns differs. The error says
  both sizes, for example "Puzzle sizes differ: 15x15 and 15x16".
- **Different black squares.** The sizes match but the black squares are in
  different places. The error lists the first few squares that differ, for
  example "Black squares differ at row 3 col 7, row 8 col 2".

Matching shapes guarantee that word numbers line up: 14-Across in the first
puzzle is the same place in the grid as 14-Across in the second, so each line
can be compared with its partner.

A new error class, `PuzzleCompareError`, is used for both problems, so
callers can catch one thing. It would sit in the same file as the new use
case.

## Where the two puzzles come from

Each of the two inputs can be any one of these, in any combination (for
example a file against a database puzzle, or two files in different
formats):

| Input | How the tool knows |
|---|---|
| A puzzle saved in the database | The input is a puzzle name, not a file path |
| AcrossLite text (`.txt`) | File extension |
| AcrossLite binary (`.puz`) | File extension |
| ipuz (`.ipuz`) | File extension |
| xd (`.xd`) | File extension |
| Crossword Compiler XML (`.xml`) | File extension |

These are the same five formats the Import menu already accepts. The tool
does **not** save anything to the database. It reads the file with the
existing import code, which hands back a puzzle in memory, and then throws
it away after the comparison. Importing is not needed first.

### How the tool decides "file or database name"

The rule is simple: an input is a **database puzzle name** unless it ends
with one of the import extensions (`.txt`, `.puz`, `.ipuz`, `.xd`, `.xml`),
in which case it is a file path. If the file does not exist, or the name is
not in the database, the tool reports "No file or puzzle named X".

(Consequence: a database puzzle whose name itself ends in one of those
extensions cannot be compared. Such names are unlikely, so this is accepted.)

### Which version of a database puzzle

Always the latest saved version, read by its real name. Working copies
(unsaved edits) and older versions from the puzzle's history are never used.

## How it looks to the user

### Command line (first version)

A new script next to the existing `get_theme_words.py`:

```
python3 tools/user/compare_puzzles.py <first> <second> [--user-id 1]
```

- `<first>` and `<second>` are file paths or puzzle names.
- `--user-id` defaults to 1, like the other tools.
- The diff goes to standard output in ordinary unified diff format.
- Exit code 0 means the puzzles are the same, 1 means they differ, and 2
  means they could not be compared (the error message goes to standard
  error). This is the same convention the `diff` command uses, so the tool
  can be used in scripts.

### Browser

No browser version is planned. This is a command-line tool only.

## Where it fits in the code

The project keeps its logic in use cases, with file reading done by
adapters. The comparison follows that rule.

1. **A new use case class, `CompareUseCases`**
   (`crossword/use_cases/compare_use_cases.py`). It needs the persistence
   port (to load database puzzles) and the five existing import adapters (to
   read files). It has one public method:

   ```
   compare_puzzles(user_id, first, second) -> list[str]
   ```

   where `first` and `second` are each a small description of the source
   (see below) and the result is the diff lines. It:

   1. loads each puzzle (from the database or by importing a file),
   2. checks the shapes match, raising `PuzzleCompareError` if not,
   3. builds the list of lines for each puzzle,
   4. returns the diff lines.

2. **A small "source" description.** Rather than passing around loose text,
   each input is a tiny object: either `("db", name)` or `("file", path)`.
   The command-line script applies the extension rule above and builds
   these. The use case itself never guesses, which keeps it easy to test.

3. **Reading a file.** The use case picks the right import adapter from the
   file extension. This is the same list of five adapters that
   `ImportUseCases` already holds, so the simplest approach is to move the
   "pick an adapter from the extension" step into one small shared helper
   used by both use cases. `.puz` files are binary and are read as bytes; the
   rest are read as text.

4. **Building the lines.** A function takes a puzzle and returns its lines:
   the title line, a heading `Across`, the Across lines, a heading `Down`, the Down lines.
   Each word line is `<number><A|D> <ANSWER>  <clue>`. A blank square in an
   unfinished answer is shown as `.`, and a word with no clue shows nothing
   after the answer. Python's built-in `difflib.unified_diff` does the
   comparing, so no new library is needed.

5. **Wiring.** `CompareUseCases` is created in
   `crossword/wiring/__init__.py` like the others.

6. **The script** `tools/user/compare_puzzles.py` is thin: parse the
   arguments, work out file-or-name, call the use case, print the result,
   set the exit code. It follows the same layout as `get_theme_words.py`.

The use case depends only on the ports and domain, as the project's
dependency rule requires; it does not touch the web layer.

## Tests

Using pytest, in `crossword/tests/`:

- Identical puzzles produce no diff lines.
- A changed title shows as one `-` and one `+` line.
- Locks and a trailing space on a clue do not cause differences.
- A changed clue shows as one `-` line and one `+` line.
- A changed answer shows as one `-` and one `+` line.
- Several changes show in number order, Across before Down.
- Different sizes raise `PuzzleCompareError` with both sizes in the message.
- Same size with different black squares raises the error and names the
  squares.
- A blank square in an answer shows as `.`; a missing clue shows nothing.
- Comparing a database puzzle to a file, a file to a file in a different
  format, and a database puzzle to a database puzzle. One test per format
  would be a lot, so: one per import adapter against a database puzzle,
  plus one mixed-format pair.
- A name that is not in the database, and a missing file with an import extension, each give a clear error.
- The script's exit codes (0, 1, 2), checked by running it on small files.

## Not included

- Comparing letters grid-square by grid-square. The comparison is by word
  line, as asked.
- Merging, or copying changes from one puzzle to the other.
- Saving the diff anywhere other than the screen or a shell redirect.
- Comparing more than two puzzles at once.
- Any database change.

## Docs to update when it is built

- [usecases.md](usecases.md): add `CompareUseCases`.
- A short "Tools" mention of `compare_puzzles.py` wherever the other
  `tools/user/` scripts are described.

## Decisions

All questions from the first draft have been answered:

1. File or database: a database puzzle name, unless the input ends in an
   import extension.
2. Whitespace and case: ignore only leading/trailing spaces in clues; case
   differences count.
3. The title is compared too.
4. (Withdrawn. The question was whether a word could be moved or renumbered
   between versions. Because the shapes must match, it cannot, so nothing to
   decide.)
5. Output is an ordinary unified diff; only changes occur, no additions or
   deletions.
6. No browser version.
7. If an import format ever numbered the same grid differently, raise the
   same error. Accepted.
8. Always the latest saved version of a database puzzle.
9. `--user-id` defaults to 1.
10. Locks are ignored.
