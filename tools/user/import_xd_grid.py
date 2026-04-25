"""
Import a .xd puzzle file and write the grid as JSON to stdout.

Usage:
    python3 tools/user/import_xd_grid.py <file>
"""

import argparse
import json
import sys

sys.path.insert(0, ".")
from crossword.adapters.xd_import_adapter import XdImportAdapter


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="Path to the .xd puzzle file")
    args = parser.parse_args()

    adapter = XdImportAdapter()
    content = open(args.file).read()
    _title, _author, puzzle = adapter.import_puzzle(content)

    grid = puzzle.grid
    result = {
        "file": args.file,
        "grid": json.loads(grid.to_json()),
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
