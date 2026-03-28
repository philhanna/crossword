"""
Export a puzzle to AcrossLite format (.zip containing puzzle.txt and puzzle.json).

Usage:
    python tools/admin/export_acrosslite.py <puzzle_name> [output.zip]

If output path is omitted, writes <puzzle_name>.zip in the current directory.
"""

import sys
from pathlib import Path

# Allow running from any directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crossword.wiring import make_app


def main():
    if len(sys.argv) < 2:
        print("Usage: export_acrosslite.py <puzzle_name> [output.zip]", file=sys.stderr)
        sys.exit(1)

    name = sys.argv[1]
    out_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path(f"{name}.zip")

    app = make_app()
    zip_bytes = app.export_uc.export_puzzle_to_acrosslite(user_id=1, name=name)
    out_path.write_bytes(zip_bytes)
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
