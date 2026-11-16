"""
Compare two puzzles and print only the lines that differ (- first, + second).

What is compared is the title, then every Across word with its clue, then
every Down word with its clue. The two puzzles must have the same size and
the same black squares.

Each argument is either the name of a puzzle in the database, or, if it ends
in .txt, .puz, .ipuz, .xd or .xml, the path of a file in that import format.

Exit status: 0 if the puzzles are the same, 1 if they differ, 2 if they
could not be compared.

Usage:
    python3 tools/user/compare_puzzles.py <first> <second> [--user-id 1]
"""

import argparse
import sys

sys.path.insert(0, ".")
from crossword import init_config
from crossword.adapters import SQLitePersistenceAdapter
from crossword.adapters.acrosslite_import_adapter import AcrossLiteImportAdapter
from crossword.use_cases.compare_use_cases import CompareUseCases, PuzzleCompareError
from crossword.use_cases.import_use_cases import ImportUseCases
from crossword.use_cases.puzzle_source import PuzzleSource


def main() -> None:
    """Parse arguments, run the comparison, print the diff, set the exit status."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("first", help="Puzzle name or import file")
    parser.add_argument("second", help="Puzzle name or import file")
    parser.add_argument(
        "--user-id",
        type=int,
        default=1,
        help="ID of the user who owns database puzzles (default: 1)",
    )
    args = parser.parse_args()

    config = init_config()
    persistence = SQLitePersistenceAdapter(config["dbfile"])
    import_uc = ImportUseCases(persistence, AcrossLiteImportAdapter())
    compare_uc = CompareUseCases(persistence, import_uc)

    try:
        diff = compare_uc.compare_puzzles(
            args.user_id,
            PuzzleSource.parse(args.first),
            PuzzleSource.parse(args.second),
        )
    except PuzzleCompareError as e:
        print(e, file=sys.stderr)
        sys.exit(2)

    if diff:
        print("\n".join(diff))
        sys.exit(1)
    print("The puzzles are the same.")


if __name__ == "__main__":
    main()
