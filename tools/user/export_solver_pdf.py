"""
Export a puzzle to solver PDF format (empty grid + clues).

Usage:
    python tools/user/export_solver_pdf.py <puzzle_name> [output.pdf]

If output path is omitted, writes <puzzle_name>-solver.pdf in the current directory.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crossword.wiring import make_app


def main():
    if len(sys.argv) < 2:
        print("Usage: export_solver_pdf.py <puzzle_name> [output.pdf]", file=sys.stderr)
        sys.exit(1)

    name = sys.argv[1]
    out_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path(f"{name}-solver.pdf")

    app = make_app()
    pdf = app.export_uc.export_puzzle_to_solver_pdf(user_id=1, name=name)
    out_path.write_bytes(pdf)
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
