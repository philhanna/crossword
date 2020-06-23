#! /usr/bin/python3

import os

from crossword import ClueExportVisitor
from crossword import Configuration
from crossword import Puzzle
from crossword.util import list_puzzles


def main(args):
    puzzles_root = Configuration.get_puzzles_root()

    # If the --list option was specified, just show the
    # list of puzzles in the puzzles root directory

    if args.list:
        list_puzzles(puzzles_root)
        exit(0)

    # Open the input file and load the JSON it contains.
    # Construct a puzzle from it

    if not args.puzzlename:
        raise ValueError("No puzzle name specified")

    filename = os.path.join(puzzles_root, args.puzzlename + ".json")

    if not os.path.exists(filename):
        raise FileNotFoundError(f"Puzzle file name {filename} not found")

    with open(filename) as fp:
        jsonstr = fp.read()
    puzzle = Puzzle.from_json(jsonstr)

    # Create the CSV output

    visitor = ClueExportVisitor()
    puzzle.accept(visitor)
    csvstr = visitor.csvstr

    if args.output:
        with open(args.output, "wt") as fp:
            print(csvstr, file=fp)
    else:
        # Stdout
        print(csvstr)


#   ============================================================
#   Mainline
#   ============================================================
if __name__ == '__main__':
    import argparse

    description = '''Exports a crossword puzzle to .csv format'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-l", "--list", action="store_true",
                        help="List puzzles in the puzzle directory")
    parser.add_argument("-o", "--output",
                        help="Output file name (default=stdout)")
    parser.add_argument("puzzlename", nargs="?",
                        help="Input JSON file containing puzzle", default=None)
    args = parser.parse_args()

    try:
        main(args)
    except Exception as e:
        print(e)
        exit(-2)
