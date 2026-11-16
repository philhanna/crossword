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

The two lists are then compared line by line and the differences are
printed in the familiar "diff" style (lines starting with `-` exist only in
the first puzzle, lines starting with `+` exist only in the second).

Example. Puzzle A has these lines:

```
Across
1 OCEAN  Big blue expanse
5 RIVER  Flows to the sea
Down
1 ORB    Round object
2 CAR    Vehicle
```

Puzzle B has the same grid, but 5-Across has a new clue and 2-Down has a
new answer. The result is:

```
 Across
 1 OCEAN  Big blue expanse
-5 RIVER  Flows to the sea
+5 RIVER  Water that flows to the sea
 Down
 1 ORB    Round object
-2 CAR    Vehicle
+2 CAB    Vehicle
```

If the two puzzles are the same, the tool says so and shows no differences.

## What is compared, and what is not

**Compared:** the answer letters and the clue of every Across and Down
word.

**Not compared:** the title, author, locked words, circled squares, the
puzzle's state (draft, submitted, and so on), undo history, and anything
else. Only the words and clues you asked about. (See question 3 below.)

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

Proposal: if the text given matches an existing file on disk, it is a file.
Otherwise it is treated as the name of a puzzle in the database. If it is
neither, the tool reports "No file or puzzle named X". To force the database
reading (for example, a puzzle named `grid.txt`), the user can write
`db:grid.txt`. (See question 1.)

### Which version of a database puzzle

A puzzle in the database may have a "working copy" that holds unsaved edits
(see "Working copy pattern" in the project notes). Proposal: the tool always
reads the **saved** puzzle by its real name, never a working copy. This is
what the user last saved, which is normally what they want to compare.

## How it looks to the user

### Command line (first version)

A new script next to the existing `get_theme_words.py`:

```
python3 tools/user/compare_puzzles.py <first> <second> [--user-id 1]
```

- `<first>` and `<second>` are file paths or puzzle names.
- The diff goes to standard output.
- Exit code 0 means the puzzles are the same, 1 means they differ, and 2
  means they could not be compared (the error message goes to standard
  error). This is the same convention the `diff` command uses, so the tool
  can be used in scripts.

### Browser (not in the first version)

A later addition could be a "Compare…" item in the Puzzle menu with two
pickers and a side-by-side result. It would call the same use case through a
new route. It is left out of the first version; see question 6.

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
   The command-line script does the "is it a file or a name?" guessing and
   builds these. The use case itself never guesses, which keeps it easy to
   test and keeps file-system checks out of the use case.

3. **Reading a file.** The use case picks the right import adapter from the
   file extension. This is the same list of five adapters that
   `ImportUseCases` already holds, so the simplest approach is to move the
   "pick an adapter from the extension" step into one small shared helper
   used by both use cases. `.puz` files are binary and are read as bytes; the
   rest are read as text.

4. **Building the lines.** A function takes a puzzle and returns its lines:
   a heading `Across`, the Across lines, a heading `Down`, the Down lines.
   Each word line is `<number> <ANSWER>  <clue>`. A blank square in an
   unfinished answer is shown as `.`, and a word with no clue shows nothing
   after the answer. Python's built-in `difflib.unified_diff` does the
   comparing, so no new library is needed.

5. **Wiring.** `CompareUseCases` is created in
   `crossword/wiring/__init__.py` like the others, so a later browser route
   can use it without further plumbing.

6. **The script** `tools/user/compare_puzzles.py` is thin: parse the
   arguments, work out file-or-name, call the use case, print the result,
   set the exit code. It follows the same layout as `get_theme_words.py`.

The use case depends only on the ports and domain, as the project's
dependency rule requires; it does not touch the web layer.

## Tests

Using pytest, in `crossword/tests/`:

- Identical puzzles produce no diff lines.
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
- A name that is neither a file nor a puzzle gives a clear error.
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
- If a browser route is added later, regenerate
  [endpoints.md](endpoints.md) (it is generated; do not edit by hand).

## Questions for you

Each has my proposed answer, so a plain "go with your proposals" works.

1. **File or database name?** I proposed: a real file on disk wins; use
   `db:name` to force a database puzzle. Would you rather have an explicit
   flag on each input (for example `--file x.puz` / `--db "My puzzle"`)? It
   is wordier but never ambiguous.
2. **Clue text and whitespace.** Should `Big blue expanse` and
   `Big  blue expanse ` (extra spaces) count as different? Proposal: ignore
   leading and trailing spaces only; otherwise compare exactly. Should upper
   and lower case differences count? Proposal: yes, they count, since a
   publisher's edit of "ocean" to "Ocean" is a real edit.
3. **Anything else in the comparison?** The title and author are shown in
   the import formats and could be compared too. Proposal: leave them out,
   as you described the content to be words and clues only. Do you want an
   optional `--include-title` later?
4. **Answers that were reordered.** If a publisher renumbers or moves a
   word, the shapes still match (as required), so numbers line up and this
   cannot happen by design. I am assuming that is the intent. Correct?
5. **Output style.** Proposal: a normal unified diff with the headings
   `Across` and `Down` shown as unchanged lines for context. Would you
   prefer a shorter report that only lists changed words, for example
   `5-Across clue: "Flows to the sea" -> "Water that flows to the sea"`?
   The shorter form is easier to read for a puzzle; the diff form can be fed
   to other diff tools.
6. **Browser version.** Do you want the Compare dialog in the browser in the
   first version, or is the command line enough for now? If it is wanted,
   what would the result look like: a plain text diff in a dialog, or a
   two-column view with changes highlighted?
7. **Importing a file with the same size but a different number of words.**
   The black squares being identical means the words are identical, so I
   treat this as impossible. If an import format ever produces a different
   numbering for the same grid, I would raise the same error. Is that
   acceptable?
8. **Which database puzzle.** I proposed always the saved puzzle, never a
   working copy. Should there also be a way to name an earlier saved version
   from the puzzle's history (see
   [puzzle_content_snapshots.md](puzzle_content_snapshots.md)), for example
   `db:My puzzle@3`? That would make "compare to what I submitted" a
   one-liner, but it needs the snapshot feature to be finished first.
9. **User ID.** Other tools take `--user-id` and default to 1. Same here?
10. **Locked words.** Should the diff mark whether a word is locked (a theme
    word), so theme changes stand out? Proposal: no.
