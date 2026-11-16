# crossword.use_cases.puzzle_source
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PuzzleSource:
    """
    Where a puzzle to be compared comes from: a database name or a file path.

    For a database puzzle, `version` optionally selects an earlier saved
    version instead of the live puzzle: N >= 1 is the Nth saved version
    (1 = oldest), 0 is the newest, and -k is k saves before the newest.
    """

    kind: str  # "db" or "file"
    value: str
    version: int | None = None

    DB = "db"
    FILE = "file"

    @staticmethod
    def parse(text: str) -> "PuzzleSource":
        """
        Decide from the text what it names.

        Text ending in an import extension (.txt, .puz, .ipuz, .xd, .xml) is a
        file path; anything else is a puzzle name in the database. A database
        name may end in "@N" or "@-N" (digits only) to pick a saved version.
        """
        from crossword.use_cases.import_use_cases import is_import_file_name

        if is_import_file_name(text):
            return PuzzleSource(PuzzleSource.FILE, text)

        match = re.fullmatch(r"(.+)@(-?\d+)", text)
        if match:
            return PuzzleSource(PuzzleSource.DB, match.group(1), int(match.group(2)))
        return PuzzleSource(PuzzleSource.DB, text)
