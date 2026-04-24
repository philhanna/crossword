# crossword.adapters.puz_import_adapter
import puz

from crossword import Grid, Puzzle
from crossword.domain.word import Word
from crossword.ports.import_port import ImportPort, PuzzleImportError


class PuzImportAdapter(ImportPort):
    """
    Imports a puzzle from AcrossLite binary format (.puz).

    Uses the puzpy library to parse the binary format.
    Format spec: https://code.google.com/archive/p/puz/wikis/FileFormat.wiki
    """

    def import_puzzle(self, content: bytes) -> tuple[str, str, Puzzle]:  # type: ignore[override]
        """
        Parse AcrossLite binary content and return (title, author, puzzle).

        Args:
            content: Raw bytes of a .puz file

        Returns:
            (title, author, puzzle) — title and author are stripped strings
            (may be empty); puzzle is a fully initialized Puzzle in puzzle mode.

        Raises:
            PuzzleImportError: If the content is malformed or missing required data
        """
        try:
            p = puz.Puzzle()
            p.load(content)
        except Exception as e:
            raise PuzzleImportError(f"Failed to parse .puz file: {e}") from e

        title = (p.title or "").strip()
        author = (p.author or "").strip()
        width = p.width
        height = p.height

        if width != height:
            raise PuzzleImportError(
                f"Non-square puzzles are not supported: {width}x{height}"
            )
        n = width

        # Build grid with black cells
        black = p.blacksquare()
        grid = Grid(n)
        for i, ch in enumerate(p.solution):
            r, c = divmod(i, n)
            if ch == black:
                grid.add_black_cell(r + 1, c + 1)

        puzzle = Puzzle(grid, title=title or None)
        puzzle.enter_puzzle_mode()

        # Fill in solution letters
        for i, ch in enumerate(p.solution):
            r, c = divmod(i, n)
            if ch != black and ch.isalpha():
                puzzle.set_cell(r + 1, c + 1, ch.upper())

        # Map numbered words to clues via puzpy's numbering
        numbering = p.clue_numbering()

        across_seqs = sorted(puzzle.across_words.keys())
        down_seqs = sorted(puzzle.down_words.keys())

        if len(numbering.across) != len(across_seqs):
            raise PuzzleImportError(
                f"Across clue count mismatch: {len(numbering.across)} clues "
                f"for {len(across_seqs)} words"
            )
        if len(numbering.down) != len(down_seqs):
            raise PuzzleImportError(
                f"Down clue count mismatch: {len(numbering.down)} clues "
                f"for {len(down_seqs)} words"
            )

        for seq, entry in zip(across_seqs, numbering.across):
            puzzle.set_clue(seq, Word.ACROSS, entry["clue"])
        for seq, entry in zip(down_seqs, numbering.down):
            puzzle.set_clue(seq, Word.DOWN, entry["clue"])

        return title, author, puzzle
