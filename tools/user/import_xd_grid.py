"""
Import a .xd puzzle file and write it back out as .xd to stdout.

Usage:
    python3 tools/user/import_xd_grid.py <file>
"""

import argparse
import sys

sys.path.insert(0, ".")
from crossword.adapters.xd_import_adapter import XdImportAdapter
from crossword.adapters.xd_export_adapter import XdExportAdapter
from crossword.domain.word import Word


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="Path to the .xd puzzle file")
    args = parser.parse_args()

    _title, _author, puzzle = XdImportAdapter().import_puzzle(open(args.file).read())

    for seq in puzzle.across_words:
        puzzle.set_clue(seq, Word.ACROSS, None)
    for seq in puzzle.down_words:
        puzzle.set_clue(seq, Word.DOWN, None)

    for r in range(1, puzzle.n + 1):
        for c in range(1, puzzle.n + 1):
            if not puzzle.is_black_cell(r, c):
                puzzle.set_cell(r, c, ' ')

    print(XdExportAdapter().export_puzzle_to_xd(puzzle))


if __name__ == "__main__":
    main()
