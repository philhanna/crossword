# crossword.use_cases.puzzle_source
from dataclasses import dataclass


@dataclass(frozen=True)
class PuzzleSource:
    """Where a puzzle to be compared comes from: a database name or a file path."""

    kind: str  # "db" or "file"
    value: str

    DB = "db"
    FILE = "file"

    @staticmethod
    def parse(text: str) -> "PuzzleSource":
        """
        Decide from the text what it names.

        Text ending in an import extension (.txt, .puz, .ipuz, .xd, .xml) is a
        file path; anything else is a puzzle name in the database.
        """
        from crossword.use_cases.import_use_cases import is_import_file_name

        kind = PuzzleSource.FILE if is_import_file_name(text) else PuzzleSource.DB
        return PuzzleSource(kind, text)
