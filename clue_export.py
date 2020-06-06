#! /usr/bin/python3

import os

from configuration import Configuration
from puzzle import Puzzle
from clue_export_visitor import ClueExportVisitor


def main(args):

    config = Configuration()
    puzzles_root = config.get_puzzles_root()

    # If the --list option was specified, just show the
    # list of puzzles in the puzzles root directory

    if args.list:
        for puzzlename in os.listdir(puzzles_root):
            print(puzzlename)
        exit(0)

    # Open the input file and load the JSON it contains.
    # Construct a puzzle from it

    if not args.filename:
        raise ValueError("No filename specified")

    if args.relative:
        filename = os.path.join(puzzles_root, args.filename)
    else:
        filename = args.filename

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
    parser.add_argument("-r", "--relative", action="store_true",
                        help="File name is relative to the puzzle directory")
    parser.add_argument("-o", "--output",
                        help="Output file name (default=stdout)")
    parser.add_argument("filename", nargs="?",
                        help="Input JSON file containing puzzle", default=None)
    args = parser.parse_args()

    try:
        main(args)
    except Exception as e:
        print(e)
        exit(-2)