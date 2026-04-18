"""
Export a puzzle to solver PDF format (empty grid + clues).

Usage:
    python tools/user/export_solver_pdf.py <puzzle_name> [output.pdf]

If output path is omitted, writes <puzzle_name>-solver.pdf in the current directory.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crossword.wiring import make_app


def main():
    parser = argparse.ArgumentParser(
        description="Export a puzzle to solver PDF format (empty grid + clues)."
    )
    parser.add_argument("puzzle_name", help="Name of the puzzle to export")
    parser.add_argument(
        "output", nargs="?", type=Path,
        help="Output PDF path (default: <puzzle_name>-solver.pdf)"
    )
    args = parser.parse_args()

    out_path = args.output or Path(f"{args.puzzle_name}-solver.pdf")

    app = make_app()
    pdf = app.export_uc.export_puzzle_to_solver_pdf(user_id=1, name=args.puzzle_name)
    out_path.write_bytes(pdf)
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
