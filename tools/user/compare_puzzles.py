"""
Compare two puzzles and print only the lines that differ (- first, + second).

What is compared is the title, then every Across word with its clue, then
every Down word with its clue. The two puzzles must have the same size and
the same black squares.

Each argument is either the name of a puzzle in the database, or, if it ends
in .txt, .puz, .ipuz, .xd or .xml, the path of a file in that import format.

A database name can be followed by @N to pick an earlier saved version:
    "My Puzzle@2"    the 2nd saved version (1 is the oldest)
    "My Puzzle@0"    the newest saved version (same as the puzzle itself)
    "My Puzzle@-1"   the version before the newest, i.e. as it was before the
                     latest save
Use --history to list a puzzle's versions.

Exit status: 0 if the puzzles are the same, 1 if they differ, 2 if they
could not be compared.

Usage:
    python3 tools/user/compare_puzzles.py <first> <second> [--user-id 1]
    python3 tools/user/compare_puzzles.py --history <name> [--user-id 1]
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
    parser.add_argument("first", nargs="?", help="Puzzle name (optionally NAME@N) or import file")
    parser.add_argument("second", nargs="?", help="Puzzle name (optionally NAME@N) or import file")
    parser.add_argument(
        "--history",
        metavar="NAME",
        help="List the saved versions of a database puzzle instead of comparing",
    )
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

    if args.history:
        list_history(compare_uc, args.user_id, args.history)
        return
    if not (args.first and args.second):
        parser.error("two puzzles are required (or use --history NAME)")

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


def list_history(compare_uc: CompareUseCases, user_id: int, name: str) -> None:
    """Print the comparable saved versions of a puzzle, newest first."""
    try:
        versions = compare_uc.list_versions(user_id, name)
    except PuzzleCompareError as e:
        print(e, file=sys.stderr)
        sys.exit(2)

    if not versions:
        print(f"{name} has no saved versions.")
        return
    print(f"{'N':>3} {'back':>5}  {'saved':<19}  {'state':<10}  comment")
    for v in reversed(versions):
        print(f"{v['number']:>3} {v['back']:>5}  {v['changed_at'][:19]:<19}  "
              f"{v['state']:<10}  {v['comment'] or ''}")


if __name__ == "__main__":
    main()
