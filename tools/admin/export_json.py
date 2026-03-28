"""
Export a puzzle to JSON format (.json).

Usage:
    python tools/admin/export_json.py <puzzle_name> [output.json]

If output path is omitted, writes <puzzle_name>.json in the current directory.
"""

import sys
from pathlib import Path

# Allow running from any directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crossword.wiring import make_app


def main():
    if len(sys.argv) < 2:
        print("Usage: export_json.py <puzzle_name> [output.json]", file=sys.stderr)
        sys.exit(1)

    name = sys.argv[1]
    out_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path(f"{name}.json")

    app = make_app()
    json_text = app.export_uc.export_puzzle_to_json(user_id=1, name=name)
    out_path.write_text(json_text, encoding="utf-8")
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
