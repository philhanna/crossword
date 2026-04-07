# crossword.adapters.acrosslite_import_adapter
from crossword import Grid, Puzzle
from crossword.domain.word import Word


class ImportError(Exception):
    """Raised when an AcrossLite text file cannot be parsed or is invalid."""
    pass


class AcrossLiteImportAdapter:
    """
    Imports a puzzle from AcrossLite text format (.txt).

    Format spec: https://www.litsoft.com/across/docs/AcrossTextFormat.pdf
    """

    def import_puzzle(self, content: str) -> tuple[str, str, Puzzle]:
        """
        Parse AcrossLite text content and return (title, author, puzzle).

        Args:
            content: Full text content of an AcrossLite .txt file

        Returns:
            (title, author, puzzle) — title and author are stripped strings
            (may be empty); puzzle is a fully initialized Puzzle in puzzle mode.

        Raises:
            ImportError: If the content is malformed or missing required sections
        """
        sections = self._parse_sections(content)
        self._validate_sections(sections)

        title = self._first_value(sections.get("TITLE", []))
        author = self._first_value(sections.get("AUTHOR", []))

        size_str = self._first_value(sections.get("SIZE", []))
        n = self._parse_size(size_str)

        grid_lines = [line.strip() for line in sections["GRID"] if line.strip()]
        self._validate_grid_lines(grid_lines, n)

        # Build grid with black cells
        grid = Grid(n)
        for r, row in enumerate(grid_lines, 1):
            for c, ch in enumerate(row, 1):
                if ch == ".":
                    grid.add_black_cell(r, c)

        # Build puzzle
        puzzle = Puzzle(grid, title=title or None)
        puzzle.enter_puzzle_mode()

        # Set cell letters from grid
        for r, row in enumerate(grid_lines, 1):
            for c, ch in enumerate(row, 1):
                if ch not in (".", "X") and ch.isalpha():
                    puzzle.set_cell(r, c, ch.upper())

        # Map clues to words
        across_clues = [line.strip() for line in sections.get("ACROSS", [])]
        down_clues = [line.strip() for line in sections.get("DOWN", [])]

        across_seqs = sorted(puzzle.across_words.keys())
        down_seqs = sorted(puzzle.down_words.keys())

        if len(across_clues) != len(across_seqs):
            raise ImportError(
                f"Across clue count mismatch: {len(across_clues)} clues "
                f"for {len(across_seqs)} words"
            )
        if len(down_clues) != len(down_seqs):
            raise ImportError(
                f"Down clue count mismatch: {len(down_clues)} clues "
                f"for {len(down_seqs)} words"
            )

        for seq, clue in zip(across_seqs, across_clues):
            puzzle.set_clue(seq, Word.ACROSS, clue)
        for seq, clue in zip(down_seqs, down_clues):
            puzzle.set_clue(seq, Word.DOWN, clue)

        return title, author, puzzle

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_sections(self, content: str) -> dict[str, list[str]]:
        """
        Split content into a dict of section_name -> [content lines].

        The first line must be '<ACROSS PUZZLE>'.
        Section names are the tag text without angle brackets.
        """
        sections: dict[str, list[str]] = {}
        current_section: str | None = None
        header_seen = False

        for line in content.splitlines():
            stripped = line.strip()

            if not header_seen:
                if stripped == "<ACROSS PUZZLE>":
                    header_seen = True
                    sections["_HEADER"] = []
                elif stripped:
                    # Non-blank line before header — not our format
                    raise ImportError(
                        "Not an AcrossLite text file "
                        "(expected '<ACROSS PUZZLE>' as first non-blank line)"
                    )
                continue

            if stripped.startswith("<") and stripped.endswith(">"):
                current_section = stripped[1:-1]
                if current_section not in sections:
                    sections[current_section] = []
            elif current_section is not None:
                sections[current_section].append(line)

        if not header_seen:
            raise ImportError(
                "Not an AcrossLite text file (missing '<ACROSS PUZZLE>' header)"
            )

        return sections

    def _validate_sections(self, sections: dict) -> None:
        for required in ("SIZE", "GRID", "ACROSS", "DOWN"):
            if required not in sections:
                raise ImportError(f"Missing required section <{required}>")

    def _validate_grid_lines(self, grid_lines: list[str], n: int) -> None:
        if len(grid_lines) != n:
            raise ImportError(
                f"Expected {n} grid rows, got {len(grid_lines)}"
            )
        for i, row in enumerate(grid_lines, 1):
            if len(row) != n:
                raise ImportError(
                    f"Grid row {i} has {len(row)} characters, expected {n}"
                )
            for ch in row:
                if ch not in "." and not ch.isalpha() and ch != "X":
                    raise ImportError(
                        f"Invalid character in grid row {i}: {ch!r}"
                    )

    @staticmethod
    def _first_value(lines: list[str]) -> str:
        """Return the first non-empty stripped line, or empty string."""
        for line in lines:
            stripped = line.strip()
            if stripped:
                return stripped
        return ""

    @staticmethod
    def _parse_size(size_str: str) -> int:
        """Parse 'NxM' size string; require square grid; return N."""
        parts = size_str.lower().split("x")
        if len(parts) != 2:
            raise ImportError(f"Invalid <SIZE> format: {size_str!r}")
        try:
            rows, cols = int(parts[0]), int(parts[1])
        except ValueError:
            raise ImportError(f"Non-numeric <SIZE> values: {size_str!r}")
        if rows != cols:
            raise ImportError(
                f"Non-square puzzles are not supported: {size_str!r}"
            )
        if rows < 1:
            raise ImportError(f"Invalid grid size: {rows}")
        return rows
