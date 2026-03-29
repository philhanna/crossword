"""
Export a puzzle to Crossword Compiler XML format (.xml).

Usage:
    python tools/admin/export_ccxml.py <puzzle_name> [output.xml]

If output path is omitted, writes <puzzle_name>.xml in the current directory.
"""

import sys
from pathlib import Path

# Allow running from any directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crossword.wiring import make_app


def main():
    if len(sys.argv) < 2:
        print("Usage: export_ccxml.py <puzzle_name> [output.xml]", file=sys.stderr)
        sys.exit(1)

    name = sys.argv[1]
    out_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path(f"{name}.xml")

    app = make_app()
    xml = app.export_uc.export_puzzle_to_xml(user_id=1, name=name)
    out_path.write_text(xml, encoding="utf-8")
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
